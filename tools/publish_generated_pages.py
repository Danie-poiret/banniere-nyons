"""Publish regenerated pages from a clean, disposable automation checkout.

On a concurrent push, recompute from the new main instead of rebasing stale HTML.
No force push or reset of a dirty worktree is permitted.
"""
import argparse
from pathlib import Path
import subprocess
import sys

PORTAL = 'infos-pratiques-nyons/immobilier-nyons/index.html'
PORTAL_URL = 'https://www.vivreanyons.fr/infos-pratiques-nyons/immobilier-nyons/'


def git(root, *args, check=True, capture=False):
    return subprocess.run(['git', *args], cwd=root, check=check, text=True,
                          stdout=subprocess.PIPE if capture else None)


def clean_checkout(root):
    if git(root, 'status', '--porcelain', '--untracked-files=no', capture=True).stdout:
        raise RuntimeError('Refusing to move a checkout with existing tracked changes.')


def prepare(root, mode):
    def python(*args):
        subprocess.run([sys.executable, *args], cwd=root, check=True)
    if mode == 'immobilier':
        python('tools/update_immobilier_portal.py')
        python('tools/update_immobilier_portal.py', '--check')
        python('tools/harmonize_seo.py', '--url', PORTAL_URL, '--apply')
        python('tools/harmonize_seo.py', '--url', PORTAL_URL, '--check')
    else:
        python('tools/harmonize_seo.py', '--all', '--apply', '--stage')
        python('tools/harmonize_seo.py', '--all', '--check')


def publish(root, mode, attempts=3):
    root = Path(root).resolve()
    if mode not in ('immobilier', 'seo'):
        raise ValueError('Unknown publication mode')
    clean_checkout(root)
    git(root, 'config', 'user.name', 'github-actions[bot]')
    git(root, 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    for attempt in range(1, attempts + 1):
        clean_checkout(root)
        git(root, 'fetch', 'origin', 'main')
        # Only clean CI checkouts and unpushed generated commits are moved here.
        git(root, 'checkout', '-B', 'main', 'origin/main')
        print(f'{mode}: prepare from current main, attempt {attempt}/{attempts}', flush=True)
        prepare(root, mode)
        if mode == 'immobilier':
            changed = git(root, 'diff', '--name-only', '-z', 'HEAD', capture=True).stdout
            if set(changed.rstrip('\0').split('\0')) - {'', PORTAL}:
                raise RuntimeError('Immobilier generation changed a file outside its portal.')
            git(root, 'add', '--', PORTAL)
        elif git(root, 'diff', '--quiet', check=False).returncode:
            raise RuntimeError('SEO generation left unstaged changes; nothing will be published.')
        difference = git(root, 'diff', '--cached', '--quiet', check=False).returncode
        if difference == 0:
            print(f'{mode}: already up to date; no commit needed.', flush=True)
            return False
        if difference != 1:
            raise RuntimeError('Unable to inspect generated changes.')
        message = ('Actualiser les guides du portail immobilier' if mode == 'immobilier'
                   else 'Compléter les métadonnées SEO après génération')
        git(root, 'commit', '-m', message)
        if git(root, 'push', 'origin', 'HEAD:main', check=False).returncode == 0:
            return True
        print('Publication refused; fetching and regenerating rather than rebasing HTML.', flush=True)
    raise RuntimeError(f'Publication failed after {attempts} attempts; no force push was used.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('immobilier', 'seo'))
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    publish(args.root, args.mode)
