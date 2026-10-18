"""Rehearse existing generators on a disposable Linux checkout; never retire files."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'cleanup-rehearsal'
PREFIXES = ('vivreanyons-test/', 'banniere-nyons/vivreanyons-test/')


def command(*args):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def snapshot():
    paths = command('git', 'ls-files', '-z')
    if paths.returncode:
        raise RuntimeError(paths.stderr)
    return {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
            for p in paths.stdout.split('\0') if p and (ROOT/p).is_file()}


def changed(before, after):
    return [p for p in sorted(set(before) | set(after)) if before.get(p) != after.get(p)]


def load(stem):
    sys.path.insert(0, str(ROOT/'tools'))
    spec = importlib.util.spec_from_file_location('rehearsal_'+stem, ROOT/'tools'/f'{stem}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def homepage_fixture():
    data = json.loads((ROOT/'assets/home-content.json').read_text(encoding='utf-8'))
    events, editorial = [], {}
    for row in data['events']:
        url = row['url']
        events.append({'url': url, 'page_url': url, 'title': row['title'],
                       'start_date': row['start'], 'end_date': row['end'],
                       'kind': row['kind'], 'summary': row['summary'],
                       'sessions': row.get('sessions', [])})
        editorial[url] = {'intro': row['summary'],
                          'practical': {'date_time': row['dateTime'], 'location_name': row['place']}}
    fixture = OUT/'homepage-fixture.json'
    fixture.write_text(json.dumps({'agenda': {'events': events, 'updated_at': data['sourceUpdated']},
                                   'editorial': editorial, 'published': list(editorial)}, ensure_ascii=False), encoding='utf-8')
    return fixture


def refresh_homepage(fixture):
    module = load('update_homepage')
    real_select = module.select
    module.select = lambda root, data, at=None: real_select(root, data, '2026-10-18T12:00:00Z')
    class FrozenDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.datetime(2026, 10, 18, 12, tzinfo=datetime.timezone.utc).astimezone(tz)
    module.datetime = FrozenDateTime
    module.refresh(ROOT, fixture)


def main(expected_counts=None):
    if sys.platform != 'linux' or os.environ.get('NYONS_CLEANUP_REHEARSAL') != '1':
        raise SystemExit('Requires explicitly isolated disposable Linux checkout')
    if command('git', 'remote').stdout.strip():
        raise SystemExit('Refusing rehearsal: Git remotes still configured')
    if command('git', 'symbolic-ref', '--short', 'HEAD').stdout.strip() == 'main':
        raise SystemExit('Refusing rehearsal on main')
    # A dedicated network namespace must have no live external interface.
    interfaces = command('ip', '-j', 'link', 'show')
    if interfaces.returncode or any(row['ifname'] != 'lo' for row in json.loads(interfaces.stdout)):
        raise SystemExit('Refusing rehearsal without isolated network namespace')
    OUT.mkdir(exist_ok=True)
    baseline = snapshot()
    counts = {'main': 0, 'test1': 0, 'test2': 0}
    for p in baseline:
        if p.endswith('.html'):
            counts['test2' if p.startswith(PREFIXES[1]) else 'test1' if p.startswith(PREFIXES[0]) else 'main'] += 1
    if counts != (expected_counts or {'main': 536, 'test1': 487, 'test2': 487}):
        raise SystemExit('Snapshot changed: '+str(counts))
    fixture = homepage_fixture()
    steps = [
        ('consolidate_venterol_urls.py', []), ('consolidate_venterol_urls.py', []),
        ('repair_legacy_urls.py', []), ('repair_legacy_urls.py', []),
        ('update_health_section.py', []),
        ('update_weather_navigation.py', []), ('update_weather_navigation.py', []),
        ('update_latest_article.py', []),
        ('update_google_analytics.py', []), ('update_google_analytics.py', []),
        ('update_site_seo.py', []), ('normalize_indexing_targets.py', []),
        ('update_immobilier_portal.py', []), ('update_immobilier_portal.py', ['--check']),
        ('homepage-fixture', []),
        ('harmonize_seo.py', ['--all', '--apply']),
        ('harmonize_seo.py', ['--all', '--check']),
        ('check_indexing_targets.py', []), ('check_site_integrity.py', []),
        ('check_bus_schedules.py', []), ('check_homepage.cjs', []), ('check_bus_schedules.cjs', []),
    ]
    report = {'platform': sys.platform, 'network': 'isolated namespace', 'remotes': [],
              'baseline_html_counts': counts, 'runs': [],
              'scope': 'Existing generators; removal, import preflight and rollback are measured separately by the caller; no live feeds or publication',
              'frozen_homepage_time': '2026-10-18T12:00:00Z'}
    for generation in (1, 2):
        start = snapshot()
        run = {'generation': generation, 'steps': []}
        for name, args in steps:
            before = snapshot()
            if name == 'homepage-fixture':
                try:
                    refresh_homepage(fixture)
                    status, output = 0, 'Existing cached agenda, fixed clock and date'
                except Exception:
                    status, output = 1, traceback.format_exc()
            else:
                result = command('node' if name.endswith('.cjs') else sys.executable, 'tools/'+name, *args)
                status, output = result.returncode, result.stdout+result.stderr
            try:
                load('test_cleanup_guard').check_tree(ROOT)
            except Exception:
                status = status or 1
                output += '\n'+traceback.format_exc()
            item = {'script': name, 'args': args, 'exit': status,
                    'changed_files': changed(before, snapshot()), 'output': output}
            run['steps'].append(item)
            print(json.dumps({'generation': generation, 'script': name, 'exit': status,
                              'changed': len(item['changed_files'])}), flush=True)
        run['changed_files'] = changed(start, snapshot())
        report['runs'].append(run)
    photo = json.loads((ROOT/'tools/restore-fiche-photos-manifest.json').read_text(encoding='utf-8'))
    mismatches = []
    for p, expected in photo['expected_sha'].items():
        body = (ROOT/p).read_bytes()
        actual = hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
        if actual != expected:
            mismatches.append(p)
    report['legacy_photo_preflight_mismatches'] = mismatches
    report['second_generation_stable'] = not report['runs'][1]['changed_files']
    report['baseline_to_generated_changes'] = changed(baseline, snapshot())
    report['untracked_after_rehearsal'] = command('git', 'ls-files', '--others', '--exclude-standard').stdout.splitlines()
    report['failed_steps'] = [f"{r['generation']}:{s['script']}" for r in report['runs'] for s in r['steps'] if s['exit']]
    report['cleanup_authorized_by_test'] = False
    report['remaining_gates'] = ['Unique text and all media comparison for an explicit small batch',
                                'ZIP/import non-resurrection safeguards and rollback drill for that batch',
                                'Legacy one-shot photo preflight review', 'Browser and post-deployment checks']
    (OUT/'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'second_generation_stable': report['second_generation_stable'],
                      'failed_steps': report['failed_steps'], 'photo_preflight_mismatches': len(mismatches)}))
    return bool(report['failed_steps'] or not report['second_generation_stable'])


if __name__ == '__main__':
    raise SystemExit(main())
