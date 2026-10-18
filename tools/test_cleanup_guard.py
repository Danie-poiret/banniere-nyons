"""Fail closed on reimports of explicitly retired test HTML. Never deletes files."""
import argparse
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

PREFIXES = ('vivreanyons-test/', 'banniere-nyons/vivreanyons-test/')


def retired(root):
    data = json.loads((root/'tools/test-cleanup-policy.json').read_text(encoding='utf-8'))
    if data.get('version') != 1 or not isinstance(data.get('retired_paths'), list):
        raise ValueError('Invalid cleanup policy')
    result = data['retired_paths']
    for name in result:
        if not isinstance(name, str) or not name.startswith(PREFIXES) or not name.endswith('/index.html'):
            raise ValueError('Only explicit test HTML can be retired')
        if '\\' in name or '..' in PurePosixPath(name).parts or name.startswith('/'):
            raise ValueError('Unsafe retired path')
    return result


def check_tree(root):
    found = [p for p in retired(root) if (root/p).exists()]
    if found:
        raise ValueError('Retired test pages reappeared: '+', '.join(found))


def ensure_import_allowed(root):
    # Both historical importers rewrite whole test indexes/navigation and the
    # live importer removes historical directories. Reject the whole operation
    # before network, deletion or writes when a retirement policy is active.
    if retired(root):
        raise ValueError('Legacy bulk import blocked by cleanup policy; stage and review it separately')


def extract_package(root, package):
    root = root.resolve()
    check_tree(root)
    blocked = {p.casefold() for p in retired(root)}
    with zipfile.ZipFile(package) as archive:
        planned = []
        seen = set()
        for member in archive.infolist():
            name = member.filename
            path = PurePosixPath(name)
            if (not name or name.startswith('/') or '\\' in name or ':' in name
                    or '..' in path.parts or stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError('Unsafe ZIP member: '+name)
            normalized = path.as_posix().rstrip('/')
            key = normalized.casefold()
            if key in seen or key in blocked:
                raise ValueError('Duplicate or retired ZIP member: '+name)
            if path.parts[0].casefold() in {'.git', '.github', 'tools'}:
                raise ValueError('ZIP cannot replace repository controls: '+name)
            seen.add(key)
            target = root.joinpath(*path.parts)
            if not target.resolve().is_relative_to(root):
                raise ValueError('ZIP target escapes repository: '+name)
            if any(p.is_symlink() for p in [target, *target.parents] if p.is_relative_to(root)):
                raise ValueError('ZIP target traverses a symlink: '+name)
            planned.append((member, target))
        # Verify every payload before the first filesystem write.
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC validation failed')
        for member, target in planned:
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(member))
    check_tree(root)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--extract', type=Path)
    args = parser.parse_args()
    if args.extract:
        extract_package(args.repo, args.extract)
    else:
        check_tree(args.repo)


if __name__ == '__main__':
    main()
