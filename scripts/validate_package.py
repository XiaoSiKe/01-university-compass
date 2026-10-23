#!/usr/bin/env python3
"""Validate the current Skill; --build publishes a checked ZIP and manifest.

Optional excluded markers: supply a JSON string array via --exclude-env NAME.
Only matching paths and marker indexes are reported, never marker values.
No network calls. Requires Python 3.9 or newer.
"""
import argparse
import io
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_common import metadata, publish_files, snapshot

ROOT = Path(__file__).resolve().parents[1]


def slug(text):
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    return re.sub(r"[^\w\-\s]", "", text, flags=re.UNICODE).replace(" ", "-")


def anchors(text):
    found = set(re.findall(r'<a\s+id=["\']([^"\']+)', text))
    counts = {}
    for header in re.findall(r"^#{1,6}\s+(.+)$", text, re.M):
        anchor = slug(header)
        count = counts.get(anchor, 0)
        counts[anchor] = count + 1
        found.add(anchor if not count else "{}-{}".format(anchor, count))
    return found


def zip_bytes(name, files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, data in files.items():
            entry = zipfile.ZipInfo(name + "/" + path, (1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    return buffer.getvalue()


def zip_matches(data, name, files):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        expected = {name + "/" + path: content for path, content in files.items()}
        return (len(archive.namelist()) == len(expected)
                and set(archive.namelist()) == set(expected)
                and all(archive.read(path) == content for path, content in expected.items()))


def scan_exclusions(root, terms, replacements=None):
    matches = []
    replacements = replacements or {}

    def check(label, data):
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return
        variants = [text, unquote(text)]
        try:
            variants.append(json.dumps(json.loads(text), ensure_ascii=False))
        except ValueError:
            pass
        normalized = "\n".join(unicodedata.normalize("NFKC", item).casefold() for item in variants)
        hits = [index for index, term in enumerate(terms)
                if unicodedata.normalize("NFKC", term).casefold() in normalized]
        if hits:
            matches.append({"path": label, "marker_indexes": hits})

    paths = {path for path in root.rglob("*") if path.is_file()
             and not any(part in {".git", "__pycache__", ".DS_Store"}
                         or part.startswith(".compass-publish-") for part in path.relative_to(root).parts)}
    paths.update(replacements)
    for path in sorted(paths):
        data = replacements[path] if path in replacements else path.read_bytes()
        if path.suffix == ".zip":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for entry in archive.namelist():
                    check(path.relative_to(root).as_posix() + "!" + entry, archive.read(entry))
        else:
            check(path.relative_to(root).as_posix(), data)
    return matches


def inspect(root, build=False, exclude_env=None):
    errors = []
    info = metadata(root)
    skill = info["skill"]
    files, manifest, skill_digest = snapshot(skill)
    text_files = {}
    for path, data in files.items():
        try:
            text_files[skill / path] = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            errors.append("Non UTF-8 Skill file: " + path)
    ui = text_files.get(skill / "agents/openai.yaml", "")
    if "$" + info["name"] not in ui:
        errors.append("Default prompt lacks explicit Skill invocation")
    description = re.search(r'^  short_description: "(.+)"$', ui, re.M)
    if not description or not 25 <= len(description[1]) <= 64:
        errors.append("UI description length outside 25–64")
    links = 0
    for path, text in text_files.items():
        if path.suffix != ".md":
            continue
        for target in re.findall(r"\]\(([^)]+)\)", text):
            target = target.strip().strip("<>")
            if urlsplit(target).scheme:
                continue
            target_path, _, fragment = unquote(target).partition("#")
            destination = (path.parent / target_path).resolve() if target_path else path.resolve()
            links += 1
            if not destination.is_relative_to(skill.resolve()):
                errors.append("Escaping link in " + path.name)
            elif not destination.is_file():
                errors.append("Missing link {}: {}".format(path.name, target))
            elif fragment and fragment not in anchors(destination.read_text(encoding="utf-8-sig")):
                errors.append("Missing anchor {}: {}".format(path.name, target))
    sources = json.loads((root / "research/sources.json").read_text(encoding="utf-8-sig"))
    ids = [source["id"] for source in sources]
    if len(set(ids)) != len(ids):
        errors.append("Duplicate source IDs")
    cards = []
    for path, text in text_files.items():
        for reference in set(re.findall(r"\bR\d{2}\b", text)):
            if reference not in ids:
                errors.append("Unknown source {} in {}".format(reference, path.name))
        cards.extend(re.findall(r"^#{2,3}\s+([ZPLTA]\d{2})\s*[：:]", text, re.M))
    if len(cards) != len(set(cards)):
        errors.append("Duplicate card IDs")
    cases_path = root / "tests" / ("cases-" + info["test_directory"] + ".json")
    cases = json.loads(cases_path.read_text(encoding="utf-8-sig")) if cases_path.exists() else []
    if isinstance(cases, dict):
        cases = cases.get("cases", [])
    multiple = sum(3 <= len(case.get("user_turns", [])) <= 5 for case in cases)
    manifest_path = root / "skill-manifest.json"
    zip_path = root / (info["name"] + ".zip")
    proposed = {manifest_path: (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode(),
                zip_path: zip_bytes(info["name"], files)}
    manifest_ok = False
    zip_ok = False
    try:
        manifest_data = proposed[manifest_path] if build else manifest_path.read_bytes()
        archive_data = proposed[zip_path] if build else zip_path.read_bytes()
        manifest_ok = json.loads(manifest_data.decode("utf-8-sig")) == manifest
        zip_ok = zip_matches(archive_data, info["name"], files)
        if not manifest_ok:
            errors.append("Manifest differs from current Skill; use --build after checks")
        if not zip_ok:
            errors.append("ZIP differs from current Skill")
    except (OSError, ValueError, zipfile.BadZipFile):
        errors.append("Package is missing or invalid")
    exclusion = {"performed": False, "matching_files": []}
    if exclude_env:
        try:
            terms = json.loads(os.environ[exclude_env])
            if not isinstance(terms, list) or not terms or any(not isinstance(term, str) or not term for term in terms):
                raise ValueError("invalid exclusion list")
            exclusion["performed"] = True
            exclusion["matching_files"] = scan_exclusions(root, terms, proposed if build else None)
            if exclusion["matching_files"]:
                errors.append("Excluded markers found in delivery files")
        except (KeyError, OSError, ValueError, zipfile.BadZipFile):
            errors.append("Excluded-marker input or scanned archive is invalid")
    published = False
    if build and not errors:
        try:
            if snapshot(skill)[2] != skill_digest:
                raise ValueError("Skill changed while candidates were being validated")
            publish_files(proposed)
            published = True
        except (OSError, ValueError) as error:
            errors.append("Package publication failed: " + str(error))
    return {"version": info["version"], "status": "FAIL" if errors else "PASS",
            "skill_files": len(files), "skill_bytes": sum(len(data) for data in files.values()),
            "relative_links": links, "card_ids": cards, "source_count": len(ids),
            "new_cases": len(cases), "multi_turn_cases": multiple,
            "skill_digest": skill_digest, "manifest_matches": manifest_ok,
            "zip_matches": zip_ok, "build_published": published,
            "package_check_scope": "checked_candidates" if build else "current_artifacts",
            "exclusion_scan": exclusion, "errors": errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--exclude-env", help="environment variable containing JSON array")
    parser.add_argument("--output", help="report path; defaults to the current version's test directory")
    args = parser.parse_args(argv)
    try:
        report = inspect(ROOT, args.build, args.exclude_env)
        version_dir = "v" + report["version"].replace(".", "")
    except (OSError, ValueError, KeyError) as error:
        report = {"status": "FAIL", "errors": [str(error)]}
        version_dir = "unversioned"
    output = Path(args.output) if args.output else ROOT / "tests" / version_dir / "structure-results.json"
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(report["status"] != "PASS")


if __name__ == "__main__":
    sys.exit(main())
