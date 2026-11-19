"""Install the fixed sheng/24A446 endpoint after the audited legacy CI transforms."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess

SNAPSHOT = '92158731b9f32509b7ccd612ab25eea118f24eaa68b32aa8722be424b646f547'
MANIFEST_SHA256 = '7a0ea4c8fcb4d0a5945cda44029980d3e5ab008744eaf2cb06c23527465369d2'
FILE_COUNT = 127


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def safe(workspace, name):
    rel = PurePosixPath(name)
    if rel.is_absolute() or not rel.parts or rel.parts[0] not in ('UniXNU', 'device') or any(x in ('..', '.git') for x in rel.parts) or '\\' in name or ':' in name:
        raise ValueError('Unsafe source path: ' + name)
    result = workspace.joinpath(*rel.parts)
    if not result.resolve().is_relative_to(workspace.resolve()) or any(x.is_symlink() for x in [result, *result.parents] if x == workspace or workspace in x.parents):
        raise ValueError('Symlink or escaping source path: ' + name)
    return result


def read_manifest():
    raw = Path(__file__).with_name('sources.json').read_bytes()
    if sha(raw) != MANIFEST_SHA256:
        raise ValueError('Frozen manifest hash mismatch')
    manifest = json.loads(raw)
    if manifest['snapshot_sha256'] != SNAPSHOT or len(manifest['files']) != FILE_COUNT:
        raise ValueError('Frozen snapshot or file count mismatch')
    names = [x['path'] for x in manifest['files']]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate frozen source paths')
    for row in manifest['files']:
        if sha(base64.b64decode(row['after_base64'], validate=True)) != row['after_sha256']:
            raise ValueError('Corrupt frozen source payload: ' + row['path'])
    return manifest


def validate_files(workspace, manifest, verify=False):
    pending = []
    for row in manifest['files']:
        path = safe(workspace, row['path'])
        current = sha(path.read_bytes()) if path.is_file() else None
        if current not in ((row['after_sha256'],) if verify else (row['before_sha256'], row['after_sha256'])):
            raise ValueError('Unexpected source preimage: %s (%s)' % (row['path'], current))
        if current != row['after_sha256']:
            pending.append((path, row))
    return pending


def module_state(workspace, row, verify=False, postbuild=False):
    path = safe(workspace, row['path'])
    top = Path(git(path, 'rev-parse', '--show-toplevel')).resolve()
    if top != path.resolve() or not git(path, 'remote', 'get-url', 'origin').removesuffix('.git').endswith('github.com/' + row['repository']):
        raise ValueError('Component source identity differs: ' + row['path'])
    head = git(path, 'rev-parse', 'HEAD')
    if head not in ((row['after_pin'],) if verify else (row['before_pin'], row['after_pin'])):
        raise ValueError('Component revision differs: ' + row['path'] + ' ' + head)
    parent, relative = row['path'].split('/', 1)
    stage = git(workspace / parent, 'ls-files', '--stage', '--', relative).split()
    if len(stage) != 4 or stage[0] != '160000' or stage[1] not in ((row['after_pin'],) if verify else (row['before_pin'], row['after_pin'])):
        raise ValueError('Component parent gitlink differs: ' + row['path'])
    changed = git(path, 'diff', '--name-only', 'HEAD', '--').splitlines()
    allowed = row['final_dirty'] if head == row['after_pin'] else row['before_dirty']
    for name in changed:
        raw = (path / name).read_bytes()
        values = [allowed.get(name)]
        if postbuild:
            values.append(row.get('build_mutations', {}).get(name))
        if sha(raw) not in values:
            raise ValueError('Unreviewed component modification: ' + row['path'] + '/' + name)
    if verify:
        for name, digest in row['final_dirty'].items():
            if sha((path / name).read_bytes()) != digest:
                raise ValueError('Missing component adaptation: ' + row['path'] + '/' + name)
    return dict(path=row['path'], head=head, index_pin=stage[1], dirty_sha256={n: sha((path/n).read_bytes()) for n in changed})


def verify(workspace, manifest, postbuild=False):
    validate_files(workspace, manifest, verify=True)
    states = [module_state(workspace, row, verify=True, postbuild=postbuild) for row in manifest['components']]
    return dict(snapshot_sha256=SNAPSHOT, overlay_manifest_sha256=MANIFEST_SHA256, root_base_heads=manifest['root_base_heads'], selected_fixed_heads=manifest['selected_fixed_heads'], source_file_count=FILE_COUNT, component_states=states, native_build_verified=False, hardware_verified=False)


def apply(workspace, manifest, check=False):
    pending = validate_files(workspace, manifest)
    states = [module_state(workspace, row) for row in manifest['components']]
    if check:
        return dict(check_only=True, pending_files=len(pending), component_states=states)
    # Download all changed commits before changing any source file.
    for row, state in zip(manifest['components'], states):
        if state['head'] != row['after_pin']:
            subprocess.run(['git', '-C', str(safe(workspace, row['path'])), 'fetch', '--no-tags', '--depth', '1', 'origin', row['after_pin']], check=True)
    for row, state in zip(manifest['components'], states):
        path = safe(workspace, row['path'])
        if state['head'] != row['after_pin']:
            dirty = list(state['dirty_sha256'])
            if dirty:
                subprocess.run(['git', '-C', str(path), 'restore', '--source=HEAD', '--worktree', '--', *dirty], check=True)
            subprocess.run(['git', '-C', str(path), 'checkout', '--quiet', '--detach', row['after_pin']], check=True)
        for name, data in row['adapted_files'].items():
            target = path / name
            target.write_bytes(base64.b64decode(data, validate=True))
        parent, relative = row['path'].split('/', 1)
        # The fetch pipeline reads parent-index gitlinks; keep it on the selected endpoint.
        subprocess.run(['git', '-C', str(workspace/parent), 'update-index', '--add', '--cacheinfo', '160000,'+row['after_pin']+','+relative], check=True)
    for path, row in pending:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(row['after_base64'], validate=True))
        if os.name != 'nt':
            path.chmod(int(row['mode'][-3:], 8) | 0o400)
    report = verify(workspace, manifest)
    report['updated_files'] = len(pending)
    (workspace/'frozen-upstream-effective.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace', type=Path)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--postbuild', action='store_true')
    args = parser.parse_args()
    workspace = args.workspace.resolve(strict=True)
    manifest = read_manifest()
    result = verify(workspace, manifest, args.postbuild) if args.verify else apply(workspace, manifest, args.check)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
