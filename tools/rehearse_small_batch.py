"""Linux-only, offline control/removal comparison. Never changes the PR checkout."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'cleanup-rehearsal'
SUBJECTS = ('Restaurant-La-Farigoule-Nyons', 'Restaurants-pas-chers-nyons', 'macdo-fast-food-nyons-debat')
PREFIXES = ('vivreanyons-test/', 'banniere-nyons/vivreanyons-test/')
TARGETS = [prefix+'restaurants-de-nyons/'+slug+'/index.html' for prefix in PREFIXES for slug in SUBJECTS]


def cmd(*args, cwd=ROOT):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def inventory(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}


def delta(a, b):
    return [p for p in sorted(a.keys() | b.keys()) if a.get(p) != b.get(p)]


def inspect(root):
    module = load(root/'tools/check_site_integrity.py', 'batch_integrity')
    files = inventory(root)
    sources = {p: (root/p).read_text(encoding='utf-8') for p in files if p.endswith('.html') or p == 'sitemap.xml'}
    return module.inspect(files, sources, (root/'CNAME').read_text().strip())


def guard_probes(root, scratch):
    guard = load(root/'tools/test_cleanup_guard.py', 'batch_guard')
    results = []
    before = inventory(root)
    for name in ('import_vivreanyons_drive.py', 'import_vivreanyons_live.py'):
        args = [sys.executable, str(root/'tools'/name), '--repo', str(root)]
        if 'drive' in name:
            args.extend(['--sources', str(scratch)])
        result = cmd(*args, cwd=root)
        ok = result.returncode != 0 and 'Legacy bulk import blocked' in result.stderr and inventory(root) == before
        results.append({'probe': name, 'blocked_before_writes': ok, 'exit': result.returncode, 'output': result.stderr})
        assert ok, results[-1]
    for target in TARGETS:
        package = scratch/'reimport.zip'
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('allowed-first.txt', 'must not be written')
            archive.writestr(target, 'retired')
        try:
            guard.extract_package(root, package)
            raise AssertionError('ZIP unexpectedly accepted')
        except ValueError as error:
            assert 'retired ZIP member' in str(error)
        assert inventory(root) == before
        results.append({'probe': 'zip:'+target, 'blocked_before_writes': True})
    for unsafe in ('../escape.html', '/absolute.html', 'tools/test-cleanup-policy.json', '.github/workflows/unsafe.yml', TARGETS[0].upper(), 'a\\bad.html'):
        package = scratch/'unsafe.zip'
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('allowed-first.txt', 'must not be written')
            archive.writestr(unsafe, 'bad')
        try:
            guard.extract_package(root, package)
            raise AssertionError('Unsafe ZIP unexpectedly accepted')
        except ValueError:
            pass
        assert inventory(root) == before
        results.append({'probe': 'unsafe-zip:'+unsafe, 'blocked_before_writes': True})
    # The stored historical ZIP is inspected, never unpacked into the checkout.
    archives = []
    for package in root.glob('*.zip'):
        with zipfile.ZipFile(package) as archive:
            names = archive.namelist()
            archives.append({'name': package.name, 'entries': len(names),
                             'retired_members': [n for n in names if n.casefold() in {t.casefold() for t in TARGETS}]})
    return {'probes': results, 'historical_archives': archives}


def clone_tree(destination):
    result = cmd('git', 'clone', '--no-hardlinks', '--no-checkout', str(ROOT), str(destination))
    assert result.returncode == 0, result.stderr
    for args in [('config', 'core.autocrlf', 'false'), ('checkout', '--detach', 'HEAD'),
                 ('remote', 'remove', 'origin'), ('config', 'push.default', 'nothing')]:
        result = cmd('git', *args, cwd=destination)
        assert result.returncode == 0, result.stderr
    hook = destination/'.git/hooks/pre-push'
    hook.write_text('#!/bin/sh\nexit 1\n')
    hook.chmod(0o755)


def main():
    if sys.platform != 'linux' or os.environ.get('NYONS_CLEANUP_REHEARSAL') != '1':
        raise SystemExit('Disposable Linux rehearsal only')
    assert not cmd('git', 'remote').stdout.strip()
    assert cmd('git', 'symbolic-ref', '--short', 'HEAD').stdout.strip() != 'main'
    interfaces = cmd('ip', '-j', 'link', 'show')
    assert interfaces.returncode == 0 and all(row['ifname'] == 'lo' for row in json.loads(interfaces.stdout))
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    OUT.mkdir(exist_ok=True)
    tracked_before = cmd('git', 'status', '--porcelain', '--untracked-files=no').stdout
    report = {'simulation_only': True, 'public_cleanup_performed': False, 'targets': TARGETS,
              'network': 'isolated namespace', 'commit': cmd('git', 'rev-parse', 'HEAD').stdout.strip()}
    with tempfile.TemporaryDirectory(prefix='nyons-six-page-rehearsal-') as temp:
        scratch = Path(temp)
        scenarios = {}
        final_states = {}
        for scenario in ('control', 'six-removed'):
            root = scratch/scenario
            clone_tree(root)
            initial = inventory(root)
            originals = {p: (root/p).read_bytes() for p in initial}
            if scenario == 'six-removed':
                for target in TARGETS:
                    assert target in initial
                    (root/target).unlink()
                policy = root/'tools/test-cleanup-policy.json'
                data = json.loads(policy.read_text())
                assert data['retired_paths'] == []
                data['retired_paths'] = TARGETS
                policy.write_text(json.dumps(data, indent=2))
                report['anti_resurrection'] = guard_probes(root, scratch)
            before_generation = inventory(root)
            first_integrity = inspect(root)
            harness = load(root/'tools/check_test_cleanup_safety.py', 'batch_'+scenario.replace('-', '_'))
            harness.OUT = OUT/scenario
            harness.OUT.mkdir(parents=True, exist_ok=True)
            code = harness.main({'main': 536, 'test1': 484, 'test2': 484} if scenario == 'six-removed' else None)
            generated = json.loads((harness.OUT/'results.json').read_text())
            final = inventory(root)
            final_states[scenario] = final
            after_integrity = inspect(root)
            missing = [p for p in TARGETS if not (root/p).exists()]
            # Restore bytes for every path, remove only files created in this
            # verified temporary tree, then compare the entire file inventory.
            for p in set(final)-set(initial):
                (root/p).unlink()
            for p, body in originals.items():
                (root/p).parent.mkdir(parents=True, exist_ok=True)
                (root/p).write_bytes(body)
            restored = inventory(root)
            rollback_integrity = inspect(root)
            item = {'generator_exit': code, 'initial_integrity': first_integrity,
                    'final_integrity': after_integrity, 'generation_changed_files': delta(before_generation, final),
                    'all_changes': delta(initial, final), 'missing_batch_after_two_generations': missing,
                    'rollback_exact': initial == restored, 'rollback_integrity': rollback_integrity,
                    'runs': generated['runs'], 'failed_steps': generated['failed_steps'],
                    'second_generation_stable': generated['second_generation_stable']}
            scenarios[scenario] = item
            assert item['rollback_exact'] and not rollback_integrity['errors']
        report['scenarios'] = scenarios
        differential = delta(final_states['control'], final_states['six-removed'])
        allowed = set(TARGETS) | {'tools/test-cleanup-policy.json'}
        report['differential_files'] = differential
        report['unexpected_differential_files'] = [p for p in differential if p not in allowed]
        report['main_pages_changed_by_removal'] = [p for p in differential if p.endswith('.html') and not p.startswith(PREFIXES)]
        report['assets_changed_by_removal'] = [p for p in differential if not p.endswith('.html') and p != 'tools/test-cleanup-policy.json']
        report['public_url_changes_in_pr'] = 0
        report['remaining_gates'] = ['Keep every public URL accessible; removal with unchanged links fails integrity',
                                     'Resolve existing generator drift before any real cleanup',
                                     'No retirement activation, merge or deployment authorized']
        report['real_cleanup_ready'] = False
        (OUT/'small-batch-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        assert not report['unexpected_differential_files'], report['unexpected_differential_files']
        assert not report['main_pages_changed_by_removal'] and not report['assets_changed_by_removal']
        assert len(scenarios['six-removed']['missing_batch_after_two_generations']) == 6
        assert scenarios['control']['generator_exit'] == 0
        # A missing-link diagnostic is an observed no-go result, not a waiver.
        assert scenarios['six-removed']['failed_steps'] == ['1:check_site_integrity.py', '2:check_site_integrity.py']
        assert scenarios['six-removed']['second_generation_stable']
        assert cmd('git', 'status', '--porcelain', '--untracked-files=no').stdout == tracked_before
    print(json.dumps({'simulation_complete': True, 'cleanup_ready': False, 'rollback_exact': True}))


if __name__ == '__main__':
    main()
