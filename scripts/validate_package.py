#!/usr/bin/env python3
"""Validate portable Skill; --build refreshes manifest and ZIP. No network calls.
Optional excluded markers: supply a JSON string array via --exclude-env NAME.
Only matching paths and marker indexes are reported, never the marker values.
"""
import argparse, hashlib, json, os, re, sys, unicodedata, zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'zeroone-university-compass'

def digest(data): return hashlib.sha256(data).hexdigest()
def slug(text):
    text = re.sub(r'<[^>]+>', '', text).strip().lower()
    return re.sub(r'[^\w\-\s]', '', text, flags=re.UNICODE).replace(' ', '-')
def anchors(text):
    found = set(re.findall(r'<a\s+id=["\']([^"\']+)', text))
    counts = {}
    for h in re.findall(r'^#{1,6}\s+(.+)$', text, re.M):
        a = slug(h); n = counts.get(a, 0); counts[a] = n + 1
        found.add(a if not n else f'{a}-{n}')
    return found

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--exclude-env', help='environment variable containing JSON array')
    ap.add_argument('--output', default='tests/v020/structure-results.json')
    args = ap.parse_args()
    errors=[]; links=0
    files=sorted(p for p in SKILL.rglob('*') if p.is_file())
    text_files={}
    for p in files:
        try: text_files[p]=p.read_text(encoding='utf-8-sig')
        except UnicodeDecodeError: errors.append(f'Non UTF-8 file: {p.relative_to(ROOT)}')
    main_text=text_files.get(SKILL/'SKILL.md','')
    if not main_text.startswith('---\n'): errors.append('Missing YAML frontmatter')
    if not re.search(r'^name: zeroone-university-compass$',main_text,re.M): errors.append('Skill name mismatch')
    version=re.search(r'^  version: "([^"]+)"$',main_text,re.M)
    if not version or version[1]!='0.2.0': errors.append('Version mismatch')
    ui=text_files.get(SKILL/'agents/openai.yaml','')
    if '$zeroone-university-compass' not in ui: errors.append('Default prompt lacks explicit Skill invocation')
    desc=re.search(r'^  short_description: "(.+)"$',ui,re.M)
    if not desc or not 25<=len(desc[1])<=64: errors.append('UI description length outside 25–64')
    for p,txt in text_files.items():
        if p.suffix!='.md': continue
        for target in re.findall(r'\]\(([^)]+)\)',txt):
            target=target.strip().strip('<>')
            if urlsplit(target).scheme: continue
            path, _, fragment=unquote(target).partition('#')
            dest=(p.parent/path).resolve() if path else p.resolve()
            links+=1
            if not dest.is_relative_to(SKILL.resolve()): errors.append(f'Escaping link in {p.name}')
            elif not dest.is_file(): errors.append(f'Missing link {p.name}: {target}')
            elif fragment and fragment not in anchors(dest.read_text(encoding='utf-8-sig')):
                errors.append(f'Missing anchor {p.name}: {target}')
    sources=json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8-sig'))
    ids=[s['id'] for s in sources]
    if len(set(ids))!=len(ids): errors.append('Duplicate source IDs')
    for p,txt in text_files.items():
        for ref in set(re.findall(r'\bR\d{2}\b',txt)):
            if ref not in ids: errors.append(f'Unknown source {ref} in {p.name}')
    cards=[]
    for txt in text_files.values():
        cards+=re.findall(r'^#{2,3}\s+([ZPLT]\d{2})\s*[：:]',txt,re.M)
    if len(cards)!=len(set(cards)): errors.append('Duplicate card IDs')
    cases_path=ROOT/'tests/cases-v020.json'
    cases=json.loads(cases_path.read_text()) if cases_path.exists() else []
    if isinstance(cases,dict): cases=cases.get('cases',[])
    multi=sum(3<=len(c.get('user_turns',[]))<=5 for c in cases)
    if len(cases)!=22 or multi<10: errors.append(f'Expected 22 new cases and >=10 multi-turn, found {len(cases)}/{multi}')
    manifest=[{'path':str(p.relative_to(SKILL)),'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in files]
    if args.build and not errors:
        (ROOT/'skill-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        with zipfile.ZipFile(ROOT/'zeroone-university-compass.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in files: z.write(p,p.relative_to(ROOT))
    manifest_ok=False; zip_ok=False
    try:
        manifest_ok=json.loads((ROOT/'skill-manifest.json').read_text(encoding='utf-8-sig'))==manifest
        if not manifest_ok: errors.append('Manifest differs from current Skill; use --build after checks')
        with zipfile.ZipFile(ROOT/'zeroone-university-compass.zip') as z:
            expected={str(p.relative_to(ROOT)):p.read_bytes() for p in files}
            zip_ok=set(z.namelist())==set(expected) and all(z.read(n)==data for n,data in expected.items())
            if not zip_ok: errors.append('ZIP differs from current Skill')
    except (OSError,ValueError,zipfile.BadZipFile) as e: errors.append(type(e).__name__+': package check failed')
    excluded={'performed':False,'matching_files':[]}
    if args.exclude_env:
        raw=os.environ.get(args.exclude_env)
        if not raw: errors.append('Excluded-marker environment variable is missing')
        else:
            terms=json.loads(raw)
            if not isinstance(terms,list) or not terms or any(not isinstance(t,str) or not t for t in terms):
                errors.append('Excluded markers must be a nonempty array of nonempty strings')
            else:
                excluded['performed']=True
                def check(label,data):
                    try: txt=data.decode('utf-8-sig')
                    except UnicodeDecodeError: return
                    variants=[txt,unquote(txt)]
                    try: variants.append(json.dumps(json.loads(txt),ensure_ascii=False))
                    except ValueError: pass
                    norm='\n'.join(unicodedata.normalize('NFKC',v).casefold() for v in variants)
                    hits=[i for i,t in enumerate(terms) if unicodedata.normalize('NFKC',t).casefold() in norm]
                    if hits: excluded['matching_files'].append({'path':label,'marker_indexes':hits})
                for p in ROOT.rglob('*'):
                    if not p.is_file() or any(x in {'.git','__pycache__','.DS_Store'} for x in p.relative_to(ROOT).parts): continue
                    if p.suffix=='.zip':
                        with zipfile.ZipFile(p) as z:
                            for n in z.namelist(): check(str(p.relative_to(ROOT))+'!'+n,z.read(n))
                    else: check(str(p.relative_to(ROOT)),p.read_bytes())
                if excluded['matching_files']: errors.append('Excluded markers found in delivery files')
    report={'version':version[1] if version else None,'status':'PASS' if not errors else 'FAIL',
            'skill_files':len(files),'skill_bytes':sum(p.stat().st_size for p in files),
            'relative_links':links,'card_ids':cards,'source_count':len(ids),'new_cases':len(cases),'multi_turn_cases':multi,
            'skill_digest':digest(json.dumps(manifest,sort_keys=True).encode()),
            'manifest_matches':manifest_ok,'zip_matches':zip_ok,'exclusion_scan':excluded,'errors':errors}
    out=ROOT/args.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2));return bool(errors)
if __name__=='__main__': sys.exit(main())
