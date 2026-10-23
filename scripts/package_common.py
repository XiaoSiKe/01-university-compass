"""Shared release metadata, raw-byte identity and transactional package writes.

Keep this module dependency-free so maintenance commands work on Python 3.9.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def metadata(root):
    skill = Path(root) / "01-university-compass"
    text = (skill / "SKILL.md").read_text(encoding="utf-8-sig")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("SKILL.md requires closed YAML frontmatter")
    header = text.split("\n---\n", 1)[0]
    name = re.search(r"^name:\s*([a-z0-9-]+)\s*$", header, re.M)
    version = re.search(r'^\s{2}version:\s*["\']?(\d+\.\d+\.\d+)["\']?\s*$', header, re.M)
    description = re.search(r"^description:\s*\S.+$", header, re.M)
    if not name or name[1] != skill.name or not version or not description:
        raise ValueError("SKILL.md name, description or semantic version is invalid")
    return {"name": name[1], "version": version[1], "skill": skill,
            "test_directory": "v" + version[1].replace(".", "")}


def snapshot(skill):
    """Return one consistent raw-byte snapshot, manifest and its canonical digest."""
    files = {p.relative_to(skill).as_posix(): p.read_bytes()
             for p in sorted(skill.rglob("*")) if p.is_file()}
    manifest = [{"path": path, "bytes": len(data), "sha256": digest(data)}
                for path, data in files.items()]
    return files, manifest, manifest_digest(manifest)


def manifest_digest(manifest):
    # This is the original validator's raw-manifest digest, kept stable for evidence.
    return digest(json.dumps(manifest, sort_keys=True).encode())


def publish_files(contents):
    """Publish a small set of sibling files, restoring originals on failure.

    Candidates and backups are fully written before replacement. On a rollback
    failure retain backups and report their path instead of losing recovery data.
    """
    targets = [Path(path) for path in contents]
    if not targets:
        return
    if len({path.parent.resolve() for path in targets}) != 1:
        raise ValueError("Transactional outputs must share one directory")
    stage = Path(tempfile.mkdtemp(prefix=".compass-publish-", dir=str(targets[0].parent)))
    originals = {}
    replaced = []
    preserve = False
    try:
        for index, target in enumerate(targets):
            candidate = stage / (str(index) + ".candidate")
            with candidate.open("wb") as handle:
                handle.write(contents[target])
                handle.flush()
                os.fsync(handle.fileno())
            backup = stage / (str(index) + ".backup")
            if target.exists():
                shutil.copy2(target, backup)
                originals[target] = backup
            else:
                originals[target] = None
        for index, target in enumerate(targets):
            os.replace(str(stage / (str(index) + ".candidate")), str(target))
            replaced.append(target)
    except BaseException as error:
        failures = []
        for target in reversed(replaced):
            try:
                backup = originals[target]
                if backup is None:
                    target.unlink()
                else:
                    os.replace(str(backup), str(target))
            except OSError as rollback_error:
                failures.append(str(rollback_error))
        if failures:
            preserve = True
            raise OSError("Publication and rollback failed; recovery files: " + str(stage)) from error
        raise
    finally:
        if not preserve:
            shutil.rmtree(stage)
