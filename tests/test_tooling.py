#!/usr/bin/env python3
"""Deterministic maintenance regressions; fixtures live only in temporary folders.

No real model, network request, installed Skill or historical evidence is used.
Run: python3 -m unittest discover -s tests -p test_tooling.py -v
"""
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'scripts'))
import package_common as common
import render_delivery as renderer
import validate_package as validator

spec = importlib.util.spec_from_file_location('compass_native_regressions', PROJECT / 'tests/run_discovery.py')
discovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discovery)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def fixture(root):
    skill = root / '01-university-compass'
    (skill / 'agents').mkdir(parents=True)
    (skill / 'references').mkdir()
    (skill / 'SKILL.md').write_text('''---
name: 01-university-compass
description: A minimal Skill used only in isolated tooling tests.
metadata:
  version: "0.3.0"
---
# Fixture
SKILL_CONTENT_SENTINEL
[Task](references/tasks.md#t01)
''', encoding='utf-8')
    (skill / 'agents/openai.yaml').write_text('''interface:
  short_description: "陪大学新生与 AI 初学者明确目标并通过实践逐步形成自己的判断和能力"
  default_prompt: "使用 $01-university-compass。"
''', encoding='utf-8')
    (skill / 'references/tasks.md').write_text('<a id="t01"></a>\n## T01：Fixture\nR01\n', encoding='utf-8')
    write_json(root / 'research/sources.json', [{'id': 'R01'}])
    write_json(root / 'tests/cases-v030.json', [{'id': 'V01', 'user_turns': ['one', 'two', 'three']}])
    return skill


def adopted_fixture(root):
    skill = fixture(root)
    info = common.metadata(root)
    _, _, skill_digest = common.snapshot(skill)
    evaluation = root / 'tests/v030/evaluation.json'
    entries = []
    for case, condition, answer in [('V01', 'skill', 'REVIEWED_OLDER_ANSWER'),
                                     ('V01', 'baseline', 'EXPLICIT_BASELINE_ANSWER')]:
        path = evaluation.parent / 'behavior' / (case + '-' + condition) / 'attempt-001.json'
        artifact = {'case': case, 'condition': condition, 'version': info['version'],
                    'skill_digest': skill_digest, 'status': 'completed',
                    'turns': [{'number': 1, 'status': 'completed', 'user': 'question', 'answer': answer}]}
        write_json(path, artifact)
        entries.append({'case': case, 'condition': condition, 'status': 'pass',
                        'artifact': path.relative_to(evaluation.parent).as_posix(),
                        'artifact_sha256': common.digest(path.read_bytes())})
    index = {'version': info['version'], 'skill_digest': skill_digest, 'status': 'PASS', 'cases': entries}
    write_json(evaluation, index)
    return evaluation, index, info, skill_digest


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='compass-tooling-package-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = fixture(self.root)
        self.assertEqual(validator.inspect(self.root, build=True)['status'], 'PASS')
        self.before = {name: (self.root / name).read_bytes()
                       for name in ('skill-manifest.json', '01-university-compass.zip')}

    def assert_originals_preserved(self):
        for name, data in self.before.items():
            self.assertEqual((self.root / name).read_bytes(), data, name)

    def change_skill(self, text='Updated valid task text'):
        with (self.skill / 'references/tasks.md').open('a', encoding='utf-8') as handle:
            handle.write('\n' + text + '\n')

    def test_counts_and_version_follow_current_files(self):
        report = validator.inspect(self.root)
        self.assertEqual(report['version'], '0.3.0')
        self.assertEqual(report['new_cases'], 1)
        self.assertEqual(report['multi_turn_cases'], 1)
        self.assertEqual(report['card_ids'], ['T01'])
        self.assertEqual(report['status'], 'PASS')

    def test_exclusion_failure_never_publishes_candidates(self):
        self.change_skill('FORBIDDEN_CANARY_FOR_TOOLING_TEST')
        with mock.patch.dict(os.environ, {'COMPASS_TEST_EXCLUSIONS': '["FORBIDDEN_CANARY_FOR_TOOLING_TEST"]'}):
            report = validator.inspect(self.root, build=True, exclude_env='COMPASS_TEST_EXCLUSIONS')
        self.assertEqual(report['status'], 'FAIL')
        self.assertFalse(report['build_published'])
        self.assertTrue(report['exclusion_scan']['matching_files'])
        self.assert_originals_preserved()

    def test_broken_link_never_publishes_candidates(self):
        self.change_skill('[missing](missing.md)')
        report = validator.inspect(self.root, build=True)
        self.assertEqual(report['status'], 'FAIL')
        self.assert_originals_preserved()

    def test_second_replace_failure_rolls_back_first(self):
        self.change_skill()
        replace = os.replace

        def fail_zip_candidate(source, target):
            if Path(source).name == '1.candidate':
                raise OSError('simulated second-file replace failure')
            return replace(source, target)

        with mock.patch.object(common.os, 'replace', side_effect=fail_zip_candidate):
            report = validator.inspect(self.root, build=True)
        self.assertEqual(report['status'], 'FAIL')
        self.assertFalse(report['build_published'])
        self.assert_originals_preserved()
        self.assertFalse(list(self.root.glob('.compass-publish-*')))

    def test_candidate_write_failure_preserves_existing_outputs(self):
        self.change_skill()
        with mock.patch.object(common.os, 'fsync', side_effect=OSError('simulated staging write failure')):
            report = validator.inspect(self.root, build=True)
        self.assertEqual(report['status'], 'FAIL')
        self.assert_originals_preserved()

    def test_rollback_removes_new_output_if_it_did_not_exist(self):
        (self.root / 'skill-manifest.json').unlink()
        replace = os.replace

        def fail_zip_candidate(source, target):
            if Path(source).name == '1.candidate':
                raise OSError('simulated failure')
            return replace(source, target)

        with mock.patch.object(common.os, 'replace', side_effect=fail_zip_candidate):
            report = validator.inspect(self.root, build=True)
        self.assertEqual(report['status'], 'FAIL')
        self.assertFalse((self.root / 'skill-manifest.json').exists())
        self.assertEqual((self.root / '01-university-compass.zip').read_bytes(), self.before['01-university-compass.zip'])

    def test_successful_rebuild_is_consistent_and_reproducible(self):
        self.change_skill()
        report = validator.inspect(self.root, build=True)
        self.assertEqual(report['status'], 'PASS')
        self.assertTrue(report['build_published'])
        first = (self.root / '01-university-compass.zip').read_bytes()
        self.assertEqual(validator.inspect(self.root)['status'], 'PASS')
        self.assertEqual(validator.inspect(self.root, build=True)['status'], 'PASS')
        self.assertEqual((self.root / '01-university-compass.zip').read_bytes(), first)


class RendererTests(unittest.TestCase):
    def test_adopted_index_wins_over_latest_attempt_and_includes_baseline(self):
        with tempfile.TemporaryDirectory(prefix='compass-tooling-render-') as directory:
            root = Path(directory)
            evaluation, index, info, skill_digest = adopted_fixture(root)
            newest = evaluation.parent / 'behavior/V01-skill/attempt-999.json'
            write_json(newest, {'case': 'V01', 'condition': 'skill', 'status': 'timeout',
                                'turns': [{'user': 'later', 'answer': 'UNREVIEWED_LATER_FAILURE'}]})
            report = renderer.render(root, evaluation)
            rendered = (root / 'tests/实际对话记录.html').read_text(encoding='utf-8')
            boundary = rendered.index('<h2>未采用与历史尝试</h2>')
            self.assertLess(rendered.index('REVIEWED_OLDER_ANSWER'), boundary)
            self.assertLess(rendered.index('EXPLICIT_BASELINE_ANSWER'), boundary)
            self.assertGreater(rendered.index('UNREVIEWED_LATER_FAILURE'), boundary)
            self.assertEqual(report['baseline_cases'], 1)
            self.assertEqual(report['actual_turns'], 2)

    def test_unlisted_baseline_is_not_implicitly_adopted(self):
        with tempfile.TemporaryDirectory(prefix='compass-tooling-index-') as directory:
            root = Path(directory)
            evaluation, index, info, skill_digest = adopted_fixture(root)
            index['cases'] = index['cases'][:1]
            write_json(evaluation, index)
            report = renderer.render(root, evaluation)
            self.assertEqual(report['baseline_cases'], 0)
            self.assertNotIn('EXPLICIT_BASELINE_ANSWER', (root / 'tests/实际对话记录.html').read_text(encoding='utf-8'))

    def test_invalid_adoption_never_replaces_existing_pages(self):
        variants = ['missing', 'evaluation_version', 'evaluation_digest', 'evaluation_status',
                    'case_status', 'duplicate', 'artifact_checksum', 'artifact_version',
                    'artifact_digest', 'artifact_status', 'artifact_identity', 'empty_turn']
        for variant in variants:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory(prefix='compass-tooling-refusal-') as directory:
                root = Path(directory)
                evaluation, index, info, skill_digest = adopted_fixture(root)
                artifact = evaluation.parent / index['cases'][0]['artifact']
                item = json.loads(artifact.read_text())
                if variant == 'missing':
                    artifact.unlink()
                elif variant == 'evaluation_version':
                    index['version'] = '0.2.0'
                elif variant == 'evaluation_digest':
                    index['skill_digest'] = 'wrong'
                elif variant == 'evaluation_status':
                    index['status'] = 'PENDING'
                elif variant == 'case_status':
                    index['cases'][0]['status'] = 'fail'
                elif variant == 'duplicate':
                    index['cases'].append(index['cases'][0].copy())
                elif variant == 'artifact_checksum':
                    index['cases'][0]['artifact_sha256'] = 'wrong'
                else:
                    if variant == 'artifact_version':
                        item['version'] = '0.2.0'
                    elif variant == 'artifact_digest':
                        item['skill_digest'] = 'wrong'
                    elif variant == 'artifact_status':
                        item['status'] = 'timeout'
                    elif variant == 'artifact_identity':
                        item['condition'] = 'baseline'
                    elif variant == 'empty_turn':
                        item['turns'][0]['answer'] = ''
                    write_json(artifact, item)
                    index['cases'][0]['artifact_sha256'] = common.digest(artifact.read_bytes())
                write_json(evaluation, index)
                pages = [root / '00_先读说明.html', root / 'tests/实际对话记录.html']
                for path in pages:
                    path.write_text('ORIGINAL_PAGE', encoding='utf-8')
                with self.assertRaises(renderer.EvidenceError):
                    renderer.render(root, evaluation)
                self.assertTrue(all(path.read_text() == 'ORIGINAL_PAGE' for path in pages))


class DiscoveryTests(unittest.TestCase):
    def test_nonempty_evidence_is_refused_unchanged(self):
        with tempfile.TemporaryDirectory(prefix='compass-tooling-discovery-') as directory:
            output = Path(directory) / 'existing'
            output.mkdir()
            prior = output / 'result.json'
            prior.write_bytes(b'ORIGINAL_EVIDENCE')
            with self.assertRaises(ValueError):
                discovery.prepare_output(output)
            self.assertEqual(prior.read_bytes(), b'ORIGINAL_EVIDENCE')

    def test_empty_directory_can_be_claimed_only_once(self):
        with tempfile.TemporaryDirectory(prefix='compass-tooling-claim-') as directory:
            output = Path(directory) / 'empty'
            discovery.prepare_output(output)
            with self.assertRaises(ValueError):
                discovery.prepare_output(output)

    def test_native_multiturn_replays_actual_answers_without_skill_injection(self):
        with tempfile.TemporaryDirectory(prefix='compass-tooling-native-') as directory:
            root = Path(directory)
            fixture(root)
            info = common.metadata(root)
            output = discovery.prepare_output(root / 'results')
            args = argparse.Namespace(output=output, config_home=root / 'private-config', timeout=5)
            prompts = []

            def process(command, **kwargs):
                prompts.append(kwargs['input'])
                answer = 'ACTUAL_FIRST_ANSWER' if len(prompts) == 1 else 'ACTUAL_SECOND_ANSWER'
                events = [{'type': 'item.completed', 'item': {
                    'type': 'command_execution', 'command': 'cat .agents/skills/01-university-compass/SKILL.md',
                    'exit_code': 0, 'aggregated_output': 'read only fixture'}},
                    {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': answer}}]
                return types.SimpleNamespace(stdout='\n'.join(json.dumps(item) for item in events), stderr='', returncode=0)

            case = {'id': 'D04', 'title': 'multi', 'user_turns': ['使用 $01-university-compass，开始。', '继续并改变条件。']}
            with mock.patch.object(discovery.subprocess, 'run', side_effect=process):
                report = discovery.run_one(case, args, '', 'configured-test-model', [], info)
            self.assertEqual(report['status'], 'completed')
            self.assertEqual(report['turns'], 2)
            self.assertNotIn('ACTUAL_FIRST_ANSWER', prompts[0])
            self.assertIn('ACTUAL_FIRST_ANSWER', prompts[1])
            self.assertNotIn('ACTUAL_SECOND_ANSWER', prompts[1])
            self.assertTrue(all('SKILL_CONTENT_SENTINEL' not in prompt for prompt in prompts))
            evidence = json.loads((output / 'D04/result.json').read_text())
            self.assertEqual([turn['history_messages'] for turn in evidence['turns']], [0, 2])
            observed = evidence['turns'][0]['paths_observed_in_successful_read_commands']
            self.assertEqual(observed[0]['path'], 'SKILL.md')
            self.assertEqual(observed[0]['sha256'], common.digest((info['skill'] / 'SKILL.md').read_bytes()))

    def test_list_uses_current_version_cases_file_without_writes_or_model(self):
        with tempfile.TemporaryDirectory(prefix='compass-tooling-list-') as directory:
            root = Path(directory)
            fixture(root)
            write_json(root / 'tests/v030/discovery-cases.json', [
                {'id': 'D04-custom', 'user_turns': ['one', 'two', 'three']}])
            stream = io.StringIO()
            with mock.patch.object(discovery, 'ROOT', root), mock.patch.object(discovery.subprocess, 'run') as process:
                with contextlib.redirect_stdout(stream):
                    self.assertEqual(discovery.main(['--list']), 0)
            process.assert_not_called()
            self.assertEqual(json.loads(stream.getvalue())['cases'], [{'id': 'D04-custom', 'turns': 3}])
            self.assertFalse((root / 'tests/v030/discovery').exists())


if __name__ == '__main__':
    unittest.main()
