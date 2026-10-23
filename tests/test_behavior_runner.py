#!/usr/bin/env python3
"""Regression checks using synthetic Codex events; never invokes a real model."""

import contextlib
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from types import SimpleNamespace
import unittest
from unittest import mock


TESTS = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.object(sys, "dont_write_bytecode", True):
        spec.loader.exec_module(module)
    return module


behavior = load_module("behavior_runner_under_test", TESTS / "run_behavior.py")
integrity = load_module("behavior_integrity_under_test", TESTS / "check_behavior_integrity.py")


def message_events(answer):
    return [
        {"type": "thread.started", "thread_id": "synthetic-fixture"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {
            "id": "fixture-message", "type": "agent_message", "text": answer,
        }},
        {"type": "turn.completed", "usage": {
            "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0,
        }},
    ]


class BehaviorRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="compass-runner-test-", dir="/tmp")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.config_home = self.base / "config"
        self.config_home.mkdir()
        self.args = SimpleNamespace(
            output=self.base / "out", config_home=self.config_home,
            resume=False, version="0.3.0", skill_digest="fixture-old-digest", timeout=1,
        )
        blocker = mock.patch.object(
            behavior.subprocess, "run",
            side_effect=AssertionError("A regression test attempted a real subprocess"),
        )
        blocker.start()
        self.addCleanup(blocker.stop)

    def invoke(self, case, tokens=()):
        with contextlib.redirect_stdout(io.StringIO()):
            return behavior.run_case(
                case, "baseline", self.args, 'model="synthetic-fixture"\n',
                "synthetic-fixture", "", [], list(tokens),
            )

    def fake_process(self, prompts, fail_at=None, private_first=False):
        failures = {fail_at} if isinstance(fail_at, int) else set(fail_at or ())

        def run(cmd, **kwargs):
            prompts.append(kwargs["input"])
            number = len(prompts)
            if number in failures:
                return subprocess.CompletedProcess(cmd, 1, "", "synthetic interruption")
            answer = (
                "private-fixture-marker" if private_first and number == 1
                else "synthetic-answer-" + str(number)
            )
            output = Path(cmd[cmd.index("--output-last-message") + 1])
            output.write_text(answer, encoding="utf-8")
            stdout = "\n".join(json.dumps(event) for event in message_events(answer))
            return subprocess.CompletedProcess(cmd, 0, stdout, "")
        return run

    def cli_listing(self, *arguments):
        stdout = io.StringIO()
        argv = [str(TESTS / "run_behavior.py"), "--config-home", str(self.config_home),
                *arguments, "--list"]
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
            self.assertEqual(behavior.main(), 0)
        return json.loads(stdout.getvalue())

    def test_redacted_partial_attempt_restarts_from_first_turn(self):
        prompts = []
        case = {"id": "FIXTURE", "user_turns": ["first", "second"]}
        fake = self.fake_process(prompts, fail_at=2, private_first=True)
        with mock.patch.object(behavior.subprocess, "run", side_effect=fake):
            first = self.invoke(case, ["private-fixture-marker"])
            self.assertEqual(first["status"], "process_failed")
            first_record = behavior.load_json(first["artifact"])
            self.assertFalse(first_record["turns"][0]["history_replay_safe"])
            self.assertNotIn("private-fixture-marker", json.dumps(first_record))
            self.args.resume = True
            second = self.invoke(case, ["private-fixture-marker"])

        self.assertEqual(second["status"], "completed")
        self.assertNotEqual(first["artifact"], second["artifact"])
        self.assertTrue(Path(first["artifact"]).is_file())
        self.assertEqual(len(prompts), 4)
        self.assertIn("<current_student_message>\nfirst\n", prompts[2])
        encoded = prompts[3].split("<conversation_history>\n", 1)[1]
        history = json.loads(encoded.split("\n</conversation_history>", 1)[0])
        self.assertEqual(history, [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "synthetic-answer-3"},
        ])

    def assert_metadata_change_invalidates_resume(self, field, changed):
        prompts = []
        case = {"id": "FIXTURE", "user_turns": ["unchanged baseline input"]}
        with mock.patch.object(
            behavior.subprocess, "run", side_effect=self.fake_process(prompts),
        ):
            first = self.invoke(case)
            self.assertEqual(first["status"], "completed")
            self.args.resume = True
            setattr(self.args, field, changed)
            second = self.invoke(case)
        self.assertEqual(second["status"], "completed", "stale baseline was reused")
        self.assertEqual(len(prompts), 2)
        self.assertNotEqual(first["artifact"], second["artifact"])
        self.assertEqual(behavior.load_json(second["artifact"])[field], changed)

    def test_baseline_version_change_does_not_reuse_completed_attempt(self):
        self.assert_metadata_change_invalidates_resume("version", "0.3.1")

    def test_baseline_raw_digest_change_does_not_reuse_completed_attempt(self):
        self.assert_metadata_change_invalidates_resume("skill_digest", "fixture-new-digest")

    def test_same_second_attempts_resume_newest_actual_history(self):
        prompts = []
        case = {"id": "ORDER-FIXTURE", "user_turns": ["first", "second", "third"]}
        real_strftime = behavior.time.strftime

        def same_attempt_second(format_string, *arguments):
            if format_string == "%Y%m%dT%H%M%S":
                return "20261023T000000"
            return real_strftime(format_string, *arguments)

        # Reverse the UUID order while allowing each real artifact to retain its
        # own creation metadata, fingerprint, saved turns, and filesystem times.
        identifiers = [SimpleNamespace(hex=character * 32) for character in ("f", "0", "8")]
        with mock.patch.object(behavior.time, "strftime", side_effect=same_attempt_second), \
                mock.patch.object(behavior.uuid, "uuid4", side_effect=identifiers), \
                mock.patch.object(behavior.subprocess, "run", side_effect=self.fake_process(prompts, {2, 5})):
            older = self.invoke(case)
            newer = self.invoke(case)
            older_record = behavior.load_json(older["artifact"])
            newer_record = behavior.load_json(newer["artifact"])
            self.assertEqual(older_record["fingerprint"], newer_record["fingerprint"])
            self.assertEqual(sum(t["status"] == "completed" for t in older_record["turns"]), 1)
            self.assertEqual(sum(t["status"] == "completed" for t in newer_record["turns"]), 2)
            self.assertEqual(older_record["turns"][0]["answer"], "synthetic-answer-1")
            self.assertEqual(newer_record["turns"][0]["answer"], "synthetic-answer-3")
            self.args.resume = True
            resumed = self.invoke(case)

        self.assertEqual(resumed["status"], "completed")
        resumed_record = behavior.load_json(resumed["artifact"])
        expected_history = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": newer_record["turns"][0]["answer"]},
            {"role": "user", "content": "second"},
            {"role": "assistant", "content": newer_record["turns"][1]["answer"]},
        ]
        encoded = prompts[5].split("<conversation_history>\n", 1)[1]
        replayed = json.loads(encoded.split("\n</conversation_history>", 1)[0])
        self.assertEqual(replayed, expected_history, "resume replayed an older attempt's actual answers")
        self.assertEqual(resumed_record["previous_attempt"], newer["artifact"])
        self.assertEqual(len(prompts), 6, "resume discarded the newer attempt's completed second turn")

    def test_empty_selection_exits_nonzero(self):
        argv = [str(TESTS / "run_behavior.py"), "--config-home", str(self.config_home),
                "--group", "baseline", "--baseline-id", "UNKNOWN-FIXTURE", "--list"]
        stderr = io.StringIO()
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                behavior.main()
        self.assertNotEqual(raised.exception.code, 0)
        self.assertIn("No cases selected", stderr.getvalue())

    def test_explicit_historical_files_select_48_skill_cases(self):
        arguments = []
        for name in ("cases-a.json", "cases-b.json", "cases-v020.json", "cases-v030.json"):
            arguments += ["--case-file", str(TESTS / name)]
        listing = self.cli_listing("--group", "all", *arguments)
        expected = {
            *("A%02d" % n for n in range(1, 9)),
            *("B%02d" % n for n in range(1, 9)),
            *("N%02d" % n for n in range(1, 23)),
            *("V%02d" % n for n in range(1, 11)),
        }
        self.assertEqual(len(listing["cases"]), 48)
        self.assertEqual({(c["id"], c["condition"]) for c in listing["cases"]},
                         {(case_id, "skill") for case_id in expected})

    def test_new_group_uses_metadata_version_without_relying_on_id_prefix(self):
        root = self.base / "project"
        skill = root / "01-university-compass"
        (skill / "references").mkdir(parents=True)
        (root / "tests").mkdir()
        (skill / "SKILL.md").write_text('---\nname: fixture\nmetadata:\n  version: "7.8.9"\n---\n')
        for name, identity in (("cases-a.json", "V-OLD"), ("cases-b.json", "LEGACY"),
                               ("cases-v789.json", "ARBITRARY-ID")):
            (root / "tests" / name).write_text(json.dumps([
                {"id": identity, "user_turns": ["fixture input"]}]))
        with mock.patch.object(behavior, "ROOT", root):
            listing = self.cli_listing("--skill", str(skill), "--group", "new")
            self.assertEqual([c["id"] for c in listing["cases"]], ["ARBITRARY-ID"])
            legacy = self.cli_listing("--skill", str(skill), "--group", "legacy")
            self.assertEqual({c["id"] for c in legacy["cases"]}, {"V-OLD", "LEGACY"})

    def test_default_baseline_selects_only_four_comparisons(self):
        listing = self.cli_listing("--group", "baseline")
        self.assertEqual(len(listing["cases"]), 4)
        self.assertEqual({(c["id"], c["condition"]) for c in listing["cases"]},
                         {(case_id, "baseline") for case_id in ("V01", "V03", "V05", "V06")})

    @unittest.skipUnless(hasattr(time, "tzset"), "requires POSIX timezone switching")
    def test_utc_timestamps_match_wall_clock_in_non_utc_child(self):
        # The only real child process is Python itself; its Codex call is mocked.
        # tzset stays in that child so concurrent evaluations cannot see a TZ change.
        child_code = textwrap.dedent("""\
            import json
            import os
            import sys
            import time
            from unittest import mock

            sys.path.insert(0, sys.argv[1])
            from test_behavior_runner import BehaviorRunnerTests, behavior

            previous_tz = os.environ.get("TZ")
            test = BehaviorRunnerTests("test_redacted_partial_attempt_restarts_from_first_turn")
            try:
                os.environ["TZ"] = "UTC-8"
                time.tzset()
                test.setUp()
                prompts = []
                with mock.patch.object(
                    behavior.subprocess, "run", side_effect=test.fake_process(prompts),
                ):
                    result = test.invoke({"id": "UTC-FIXTURE", "user_turns": ["first"]})
                record = behavior.load_json(result["artifact"])
                print(json.dumps({
                    "reference_epoch": time.time(),
                    "local_utc_offset": -time.timezone,
                    "started_at_utc": record["started_at_utc"],
                    "finished_at_utc": record["finished_at_utc"],
                }))
            finally:
                test.doCleanups()
                if previous_tz is None:
                    os.environ.pop("TZ", None)
                else:
                    os.environ["TZ"] = previous_tz
                time.tzset()
            """)
        process = subprocess.Popen(
            [sys.executable, "-B", "-c", child_code, str(TESTS)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            self.fail("the timezone fixture child timed out")
        self.assertEqual(process.returncode, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result["local_utc_offset"], 8 * 60 * 60)
        for field in ("started_at_utc", "finished_at_utc"):
            with self.subTest(field=field):
                epoch = datetime.strptime(result[field], "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc,
                ).timestamp()
                self.assertLessEqual(abs(epoch - result["reference_epoch"]), 2)


class IntegrityCoverageTests(unittest.TestCase):
    def test_checker_rejects_incomplete_or_extra_adopted_coverage(self):
        helper = integrity.helper
        skill = integrity.ROOT / "01-university-compass"
        skill_text, normalized_manifest = helper.read_skill(skill)
        raw_manifest = [
            {"path": str(p.relative_to(skill)), "bytes": p.stat().st_size,
             "sha256": helper.sha(p.read_bytes())}
            for p in sorted(skill.rglob("*")) if p.is_file()
        ]
        digest = helper.sha(json.dumps(raw_manifest, sort_keys=True).encode())
        entry = (skill / "SKILL.md").read_text(encoding="utf-8")
        version = re.search(r'^  version: "([0-9]+\.[0-9]+\.[0-9]+)"$', entry, re.M)[1]
        cases = {case["id"]: case for case in helper.cases_all()}

        with tempfile.TemporaryDirectory(prefix="compass-integrity-test-", dir="/tmp") as tmp:
            base = Path(tmp)

            def make_artifact(case_id, condition):
                history, turns = [], []
                for number, user in enumerate(cases[case_id]["user_turns"], 1):
                    answer = "Synthetic validator fixture; no model invoked. " + str(number)
                    turns.append({
                        "number": number, "user": user,
                        "prompt_sha256": helper.sha(helper.compose_prompt(
                            condition, skill_text, history, user)),
                        "history_messages": len(history), "status": "completed",
                        "returncode": 0, "answer": answer, "tool_call_count": 0,
                        "events": message_events(answer),
                    })
                    history.extend([{"role": "user", "content": user},
                                    {"role": "assistant", "content": answer}])
                path = base / (case_id + "-" + condition + ".json")
                path.write_text(json.dumps({
                    "version": version, "skill_digest": digest, "case": case_id,
                    "condition": condition, "configured_model": "synthetic-fixture",
                    "status": "completed", "turns": turns,
                    "skill_manifest": normalized_manifest if condition == "skill" else [],
                }, ensure_ascii=False), encoding="utf-8")
                return {"case": case_id, "condition": condition, "artifact": path.name,
                        "artifact_sha256": helper.sha(path.read_bytes())}

            complete = [make_artifact(case_id, "skill") for case_id in cases]
            complete += [make_artifact(case_id, "baseline") for case_id in sorted(helper.BASELINE_IDS)]
            index_path = base / "index.json"

            def check(items):
                index_path.write_text(json.dumps({
                    "version": version, "skill_digest": digest, "cases": items,
                }), encoding="utf-8")
                return integrity.check(index_path)

            valid = check(complete)
            self.assertEqual(valid["status"], "PASS", valid["errors"])
            self.assertEqual(valid["adopted_cases"], len(cases) + len(helper.BASELINE_IDS))
            frozen = base / "frozen-skill"
            shutil.copytree(skill, frozen)
            self.assertEqual(integrity.check(index_path, skill_path=frozen)["status"], "PASS")
            entrypoint = frozen / "SKILL.md"
            entrypoint.write_text(entrypoint.read_text() + "\nChanged fixture content\n")
            mismatch = integrity.check(index_path, skill_path=frozen)
            self.assertEqual(mismatch["status"], "FAIL")
            self.assertTrue(any("digest mismatch" in error for error in mismatch["errors"]))
            invalid_sets = {
                "only_one_baseline": [next(item for item in complete if item["condition"] == "baseline")],
                "missing_skill": [item for item in complete if (item["case"], item["condition"]) != ("V01", "skill")],
                "missing_baseline": [item for item in complete if (item["case"], item["condition"]) != ("V01", "baseline")],
                "extra_condition": complete + [make_artifact("V01", "unknown-fixture")],
            }
            for name, items in invalid_sets.items():
                with self.subTest(name=name):
                    result = check(items)
                    self.assertEqual(result["status"], "FAIL")
                    self.assertTrue(all(r["status"] == "PASS" for r in result["records"]))
                    self.assertEqual(len(result["errors"]), 1, result["errors"])
                    self.assertIn("adopted coverage mismatch", result["errors"][0])

            suite_path = base / "suite.json"
            suite = {"version": version, "case_files": [str(TESTS / "cases-v031.json")],
                     "conditions": ["skill"]}
            suite_path.write_text(json.dumps(suite))
            subset = [item for item in complete if item["case"].startswith("G") and item["condition"] == "skill"]
            def scoped(items):
                index_path.write_text(json.dumps({"version": version, "skill_digest": digest,
                    "suite_sha256": helper.sha(suite_path.read_bytes()), "cases": items}))
                return integrity.check(index_path, suite_path)
            self.assertEqual(scoped(subset)["status"], "PASS")
            self.assertEqual(scoped(subset[:-1])["status"], "FAIL")
            # A changed scope cannot silently reuse a previously accepted index.
            suite["conditions"] = ["baseline"]
            suite_path.write_text(json.dumps(suite))
            with self.assertRaisesRegex(ValueError, "Suite digest"):
                integrity.check(index_path, suite_path)
            for invalid in ([["skill"]], ["skill", "skill"], ["unsupported"]):
                suite["conditions"] = invalid
                suite_path.write_text(json.dumps(suite))
                with self.assertRaisesRegex(ValueError, "unique supported conditions"):
                    scoped(subset)


if __name__ == "__main__":
    unittest.main()
