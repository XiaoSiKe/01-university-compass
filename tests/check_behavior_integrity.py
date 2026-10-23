#!/usr/bin/env python3
"""Check adopted real-run evidence; does not assign a semantic pass."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('behavior_helpers', ROOT/'tests/run_behavior.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def check(index_path, suite_path=None, skill_path=None):
    index = helper.load_json(index_path)
    skill_path = Path(skill_path) if skill_path is not None else ROOT/'01-university-compass'
    skill_text, normalized_manifest = helper.read_skill(skill_path)
    raw_manifest = [{'path':str(p.relative_to(skill_path)),
                     'bytes':p.stat().st_size, 'sha256':helper.sha(p.read_bytes())}
                    for p in sorted(skill_path.rglob('*')) if p.is_file()]
    digest = helper.sha(json.dumps(raw_manifest, sort_keys=True).encode())
    if suite_path is not None:
        suite_path = Path(suite_path).resolve()
        suite = helper.load_json(suite_path)
        if suite.get('version') != index['version']:
            raise ValueError('Suite version does not match evaluation')
        if index.get('suite_sha256') != helper.sha(suite_path.read_bytes()):
            raise ValueError('Suite digest does not match evaluation')
        sources = suite.get('case_files')
        conditions = suite.get('conditions')
        if (not isinstance(sources,list) or not sources or
                any(not isinstance(s,str) or not s.strip() for s in sources) or
                not isinstance(conditions,list) or not conditions or
                any(not isinstance(c,str) for c in conditions) or
                len(set(conditions)) != len(conditions) or
                any(c not in {'skill','baseline'} for c in conditions)):
            raise ValueError('Suite requires case_files and unique supported conditions')
        paths = [(suite_path.parent/s).resolve() for s in sources]
        if any(not p.is_relative_to(ROOT.resolve()) for p in paths):
            raise ValueError('Suite case file escapes the project')
        supplied = helper.cases_all(paths)
        cases = {c['id']:c for c in supplied}
        if not cases or len(cases) != len(supplied):
            raise ValueError('Suite must contain distinct, nonempty cases')
        expected_keys = {(case_id,condition) for case_id in cases for condition in conditions}
    else:
        cases = {c['id']:c for c in helper.cases_all()}
        expected_keys = {(case_id,'skill') for case_id in cases} | {(case_id,'baseline') for case_id in helper.BASELINE_IDS}
    errors, records, models, keys = [], [], set(), set()
    for item in index.get('cases', []):
        key = (item['case'], item['condition'])
        if key in keys: errors.append('duplicate adopted case: '+str(key))
        keys.add(key)
        p = index_path.parent/item['artifact']
        if not p.is_file():
            errors.append('missing artifact: '+str(item['artifact']))
            continue
        data = helper.load_json(p)
        models.add(data.get('configured_model'))
        e = []
        if item.get('artifact_sha256') != helper.sha(p.read_bytes()): e.append('artifact digest mismatch')
        if data.get('version') != index['version']: e.append('version mismatch')
        if data.get('skill_digest') != digest: e.append('Skill raw digest mismatch')
        if data.get('status') != 'completed': e.append('process not completed')
        if (data.get('case'),data.get('condition')) != key: e.append('case/condition mismatch')
        if item['condition']=='skill' and data.get('skill_manifest') != normalized_manifest: e.append('loaded Skill text mismatch')
        if item['condition']=='baseline' and data.get('skill_manifest'): e.append('baseline contains Skill manifest')
        case = cases.get(item['case'])
        if case is None:
            e.append('unknown case')
            case = {'user_turns':[]}
        turns = data.get('turns',[])
        if len(turns) != len(case['user_turns']): e.append('turn count mismatch')
        history = []
        for n, turn in enumerate(turns):
            user = case['user_turns'][n] if n < len(case['user_turns']) else ''
            expected = helper.compose_prompt(item['condition'],skill_text,history,user)
            if turn.get('user') != user: e.append('input mismatch at turn '+str(n+1))
            if turn.get('prompt_sha256') != helper.sha(expected): e.append('prompt/history hash mismatch at turn '+str(n+1))
            if turn.get('history_messages') != 2*n: e.append('history length mismatch at turn '+str(n+1))
            if turn.get('status') != 'completed' or turn.get('returncode') != 0: e.append('incomplete turn '+str(n+1))
            if not turn.get('answer','').strip(): e.append('empty answer at turn '+str(n+1))
            calls = helper.evidence(turn.get('events',[]))
            if calls or turn.get('tool_call_count') != 0: e.append('unexpected external tool evidence')
            messages = [v.get('item',{}).get('text','') for v in turn.get('events',[])
                        if v.get('type')=='item.completed' and v.get('item',{}).get('type')=='agent_message']
            if not messages or messages[-1].rstrip() != turn.get('answer','').rstrip(): e.append('answer differs from final event')
            history.extend([{'role':'user','content':user},{'role':'assistant','content':turn.get('answer','')}])
        errors.extend(str(key)+': '+s for s in e)
        records.append({'case':key[0],'condition':key[1],'turns':len(turns),'status':'PASS' if not e else 'FAIL'})
    if keys != expected_keys:
        errors.append('adopted coverage mismatch; missing='+str(sorted(expected_keys-keys))+'; extra='+str(sorted(keys-expected_keys)))
    if index.get('skill_digest') != digest: errors.append('index does not target current Skill')
    if len(models) != 1 or None in models: errors.append('model configuration is missing or inconsistent')
    return {'version':index['version'],'status':'PASS' if not errors else 'FAIL',
            'scope':'run_integrity_only_not_semantic_or_student_effectiveness',
            'skill_digest':digest,'model':next(iter(models)) if len(models)==1 else sorted(str(m) for m in models),
            'adopted_cases':len(records),'actual_answers':sum(r['turns'] for r in records),
            'records':records,'errors':errors}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--suite',type=Path,help='Independent case/condition specification for a scoped release run')
    p.add_argument('--skill',type=Path,help='Exact historical Skill snapshot; defaults to current files')
    p.add_argument('--output',type=Path)
    args = p.parse_args()
    result = check(args.evaluation.resolve(), args.suite, args.skill)
    text = json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        if args.output.exists(): p.error('refusing to overwrite an existing integrity report')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text)
    print(text,end='')
    return bool(result['errors'])

if __name__=='__main__': sys.exit(main())
