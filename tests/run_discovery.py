#!/usr/bin/env python3
"""Run fresh native Skill discovery, including real multi-turn conversations.

The Skill is copied into an isolated project's .agents/skills directory. Its
contents are never injected into prompts. Each turn receives only actual prior
messages, the current user message and the same read-only tool restrictions.
Default output is a unique run directory. Existing nonempty evidence is refused.
"""
import argparse
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from package_common import digest, metadata, snapshot

spec = importlib.util.spec_from_file_location('compass_behavior_helpers', ROOT / 'tests/run_behavior.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

LOCAL_TOOL_LIMIT = ('本轮只进行对话；需要时仅可只读查看当前项目内相关资料。'
                    '不联网、不修改文件、不读取项目外文件、不创建提醒。')
DISABLED = tuple(value for value in helper.DISABLED_FEATURES
                 if value not in ('shell_tool', 'unified_exec')) + ('shell_snapshot', 'skill_mcp_dependency_install')


def prepare_output(path):
    path = Path(path).resolve()
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise ValueError('Refusing to overwrite nonempty evidence directory: ' + str(path))
    path.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also prevents two processes from claiming an empty path.
    with (path / '.run-claimed').open('x', encoding='utf-8') as handle:
        handle.write('Native discovery evidence; use a new directory for another run.\n')
    return path


def clean(value, tokens, private_paths):
    value = helper.scrub(value, tokens)
    if isinstance(value, str):
        for path, label in private_paths:
            value = value.replace(path, label)
        value = re.sub(r'/Users/[^/\s"\']+', '[USER_HOME]', value)
        value = re.sub(r'(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+', r'\1[REDACTED]', value)
        value = re.sub(r'\bsk-[A-Za-z0-9_-]{10,}\b', '[REDACTED]', value)
        value = re.sub(r'("(?:access_token|refresh_token|id_token|api_key)"\s*:\s*")[^"]+', r'\1[REDACTED]', value, flags=re.I)
        return value
    if isinstance(value, list):
        return [clean(item, tokens, private_paths) for item in value]
    if isinstance(value, dict):
        return {clean(key, tokens, private_paths): clean(item, tokens, private_paths) for key, item in value.items()}
    return value


def compose_prompt(history, user):
    parts = [LOCAL_TOOL_LIMIT]
    if history:
        parts.append('以下是同一对话此前真实产生的消息，继续处理当前消息：\n'
                     '<conversation_history>\n' + json.dumps(history, ensure_ascii=False)
                     + '\n</conversation_history>')
    parts.append('<current_user_message>\n' + user + '\n</current_user_message>')
    return '\n\n'.join(parts)


def default_cases(name):
    return [
        {'id': 'D01-explicit', 'title': '显式调用', 'user_turns': [
            '使用 $' + name + '。我大一，新闻专业，刚开始接触 AI。今晚只有20分钟，没有教材在手，也不想付费。请直接带我开始一件能检查理解的事。']},
        {'id': 'D02-natural', 'title': '自然语言发现', 'user_turns': [
            '我刚上大一，不会编程，想入门AI，可网上教程看得我更乱了。我只有手机，每周能花两小时。现在能先做什么？']},
        {'id': 'D03-unrelated-code', 'title': '无关代码不误触发', 'user_turns': [
            '用 Python 写一个函数 stable_unique(items)，保留列表中每种可哈希元素第一次出现的位置。只给代码。']},
    ]


def load_cases(path, name):
    if path is None:
        cases = default_cases(name)
    else:
        data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
        cases = data.get('cases', []) if isinstance(data, dict) else data
    ids = set()
    if not isinstance(cases, list) or not cases:
        raise ValueError('Discovery cases must be a nonempty list')
    for case in cases:
        identity = case.get('id', '')
        turns = case.get('user_turns')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', identity) or identity in ids:
            raise ValueError('Discovery case IDs must be unique safe path components')
        if not isinstance(turns, list) or not turns or any(not isinstance(turn, str) or not turn.strip() for turn in turns):
            raise ValueError('Every discovery case needs nonempty user_turns')
        ids.add(identity)
    return cases


def command(workspace, final_path):
    result = ['codex', '--no-daemon', 'exec', '--skip-git-repo-check', '--ephemeral', '--ignore-rules',
              '--sandbox', 'read-only', '--json', '--color', 'never', '--cd', str(workspace),
              '--output-last-message', str(final_path), '-c', 'approval_policy="never"',
              '-c', 'web_search="disabled"', '-c', 'project_doc_max_bytes=0',
              '-c', 'features.skip_host_skill_discovery=true']
    for feature in DISABLED:
        result.extend(['--disable', feature])
    return result + ['-']


def observed_paths(calls, name, manifest):
    paths = set()
    known = {entry['path']: entry for entry in manifest}
    for event in calls:
        item = event.get('item', {})
        if (event.get('type') != 'item.completed' or item.get('type') != 'command_execution'
                or item.get('exit_code') != 0):
            continue
        for match in re.finditer(r'(?:\.agents/skills/' + re.escape(name)
                                 + r'/)?(?:references/[A-Za-z0-9_-]+\.md|SKILL\.md)', item.get('command', '')):
            relative = match.group(0).split(name + '/', 1)[-1]
            if relative in known:
                paths.add(relative)
    return [dict(known[path]) for path in sorted(paths)]


def run_one(case, args, config, model, tokens, info):
    output = args.output / case['id']
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    history = []
    result = {'case': case['id'], 'title': case.get('title', case['id']), 'condition': 'native',
              'version': info['version'], 'configured_model': model, 'status': 'running',
              'runner_sha256': digest(Path(__file__).read_bytes()),
              'config_sha256': digest(config.encode()),
              'input_sha256': digest(json.dumps(case['user_turns'], ensure_ascii=False).encode()),
              'method': 'fresh_cli_native_project_skill_discovery',
              'context_method': 'actual_history_replayed_per_turn_without_skill_text_injection',
              'tool_policy': 'read_only_local_skill_documents; external_tools_disabled',
              'semantic_status': 'requires_manual_review', 'turns': []}
    with tempfile.TemporaryDirectory(prefix='compass-discovery-', dir='/tmp') as temporary:
        temp = Path(temporary)
        workspace, runtime = temp / 'workspace', temp / 'runtime'
        workspace.mkdir()
        runtime.mkdir(mode=0o700)
        config_path = runtime / 'config.toml'
        config_path.write_text(config, encoding='utf-8')
        config_path.chmod(0o600)
        auth = args.config_home / 'auth.json'
        if auth.is_file():
            shutil.copy2(auth, runtime / 'auth.json')
            (runtime / 'auth.json').chmod(0o600)
        installed = workspace / '.agents/skills' / info['name']
        installed.parent.mkdir(parents=True)
        shutil.copytree(info['skill'], installed)
        _, manifest, skill_digest = snapshot(installed)
        result.update(skill_manifest=manifest, skill_digest=skill_digest,
                      install_location='.agents/skills/' + info['name'])
        private_paths = sorted([(str(temp.resolve()), '[TEST_ROOT]'), (str(temp), '[TEST_ROOT]'),
                                (str(ROOT), '[PROJECT_ROOT]'), (str(args.config_home), '[USER_CODEX]'),
                                (str(Path.home()), '[USER_HOME]')], key=lambda item: len(item[0]), reverse=True)
        env = {key: value for key, value in os.environ.items()
               if not key.startswith('CODEX_') and key != 'COMPASS_EXCLUDE_TOKENS'}
        env['CODEX_HOME'] = str(runtime)

        def save_json(path, data):
            path.write_text(json.dumps(clean(data, tokens, private_paths), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

        save_json(output / 'result.json', result)
        for number, user in enumerate(case['user_turns'], 1):
            prompt = compose_prompt(history, user)
            final_path = temp / ('final-' + str(number) + '.txt')
            turn_start = time.monotonic()
            try:
                process = subprocess.run(command(workspace, final_path), input=prompt, text=True,
                                         capture_output=True, cwd=workspace, env=env, timeout=args.timeout)
                stdout, stderr, code = process.stdout, process.stderr, process.returncode
                status = 'completed' if code == 0 else 'process_failed'
            except subprocess.TimeoutExpired as error:
                stdout, stderr, code, status = error.stdout or '', error.stderr or '', None, 'timeout'
                if isinstance(stdout, bytes):
                    stdout = stdout.decode(errors='replace')
                if isinstance(stderr, bytes):
                    stderr = stderr.decode(errors='replace')
            except OSError as error:
                stdout, stderr, code, status = '', str(error), None, 'launch_failed'
            events = helper.decode_events(stdout)
            calls = helper.evidence(events)
            answer = final_path.read_text(encoding='utf-8') if final_path.is_file() else helper.answer_from(events)
            if status == 'completed' and not answer.strip():
                status = 'empty_answer'
            read_commands = [event.get('item', {}) for event in calls
                             if event.get('type') == 'item.completed'
                             and event.get('item', {}).get('type') == 'command_execution']
            turn = {'number': number, 'user': user, 'answer': answer, 'status': status,
                    'returncode': code, 'history_messages': len(history), 'prompt_sha256': digest(prompt.encode()),
                    'elapsed_seconds': round(time.monotonic() - turn_start, 2),
                    'paths_observed_in_successful_read_commands': observed_paths(calls, info['name'], manifest),
                    'read_command_evidence': [{'command': item.get('command'), 'exit_code': item.get('exit_code'),
                                               'output_chars': len(item.get('aggregated_output', ''))}
                                              for item in read_commands],
                    'tool_call_count': len(calls)}
            result['turns'].append(turn)
            prefix = 'turn-{:02d}'.format(number)
            for suffix, value in [('prompt.txt', prompt), ('actual-response.txt', answer), ('stderr.txt', stderr)]:
                (output / (prefix + '.' + suffix)).write_text(clean(value, tokens, private_paths), encoding='utf-8')
            save_json(output / (prefix + '.events.json'), events)
            save_json(output / 'result.json', result)
            if status != 'completed':
                result['status'] = status
                break
            history.extend([{'role': 'user', 'content': user}, {'role': 'assistant', 'content': answer}])
        else:
            result['status'] = 'completed'
        result['elapsed_seconds'] = round(time.monotonic() - started, 2)
        result['has_final'] = bool(result['turns']) and all(turn['answer'].strip() for turn in result['turns'])
        save_json(output / 'result.json', result)
    return {'case': case['id'], 'status': result['status'], 'turns': len(result['turns']),
            'has_final': result['has_final'], 'artifact': case['id'] + '/result.json'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='new or empty directory; nonempty directories are refused')
    parser.add_argument('--cases-file', type=Path, help='JSON cases containing id/title/user_turns')
    parser.add_argument('--case', action='append', help='select one case ID; repeatable')
    parser.add_argument('--config-home', type=Path, default=Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))))
    parser.add_argument('--timeout', type=float, default=240, help='seconds per actual model turn')
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--list', action='store_true', help='list selected cases without model calls or output writes')
    args = parser.parse_args(argv)
    try:
        if args.timeout <= 0 or args.jobs < 1:
            raise ValueError('timeout and jobs must be positive')
        info = metadata(ROOT)
        default_path = ROOT / 'tests' / info['test_directory'] / 'discovery-cases.json'
        case_path = args.cases_file or (default_path if default_path.exists() else None)
        cases = load_cases(case_path, info['name'])
        if args.case:
            unknown = set(args.case) - {case['id'] for case in cases}
            if unknown:
                raise ValueError('Unknown cases: ' + ', '.join(sorted(unknown)))
            cases = [case for case in cases if case['id'] in args.case]
        if args.list:
            print(json.dumps({'version': info['version'], 'cases': [
                {'id': case['id'], 'turns': len(case['user_turns'])} for case in cases]}, ensure_ascii=False, indent=2))
            return 0
        if not shutil.which('codex'):
            raise ValueError('codex executable not found; no evaluations were run')
        target = args.output or ROOT / 'tests' / info['test_directory'] / 'discovery' / (
            'run-' + time.strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8])
        args.output = prepare_output(target)
        config, model = helper.config_subset(args.config_home)
        tokens = helper.exclusions()
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(run_one, case, args, config, model, tokens, info): case['id'] for case in cases}
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as error:
                results.append({'case': futures[future], 'status': 'harness_failed',
                                'error': clean(str(error), tokens, [
                                    (str(ROOT), '[PROJECT_ROOT]'),
                                    (str(args.config_home), '[USER_CODEX]'),
                                    (str(Path.home()), '[USER_HOME]')])})
    summary = {'version': info['version'], 'method': 'native_discovery_no_skill_text_injection',
               'configured_model': model, 'semantic_status': 'requires_manual_review', 'results': results}
    (args.output / 'run.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'results': results}, ensure_ascii=False))
    return 0 if all(item['status'] == 'completed' and item.get('has_final') for item in results) else 1


if __name__ == '__main__':
    sys.exit(main())
