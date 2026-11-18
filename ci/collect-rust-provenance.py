#!/usr/bin/env python3
"""Read-only postbuild observation; never resolves dependencies or changes builder identity. Python 3.11+."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tomllib
from datetime import datetime, timezone


def digest(data):
    return hashlib.sha256(data).hexdigest()


def collect(tree, output, target='ios27', source=None, probe=None):
    tree = Path(tree).resolve()
    source_input = Path(source) if source else tree / '.cache/gpu-reference/metal2vulkan'
    source = source_input.resolve()
    output = Path(output).resolve()
    if output.is_relative_to(tree) or output.is_relative_to(source):
        raise ValueError('Output must be outside all input trees')
    output.mkdir(parents=True, exist_ok=False)  # unique snapshot; never mix stale evidence
    errors = []
    report = dict(schema=1, captured_at=datetime.now(timezone.utc).isoformat(), target=target,
                  purpose='postbuild-observation-not-build-attestation', lock_pinned=False,
                  archive_dependency_binding='unproven: builder identity excludes lock and toolchain',
                  toolchain_scope='installed at collection time; not proof of compiler used by reused archive',
                  files={}, tools={}, errors=errors)
    bridge = tree / 'build/adreno-metal-bridge'

    def capture(label, path, copy=False, required=True):
        item = {'status': 'missing', 'required': required}
        report['files'][label] = item
        try:
            before = path.stat()
            h = hashlib.sha256()
            data = bytearray() if copy else None
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(chunk)
                    if copy:
                        data.extend(chunk)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                raise ValueError('file changed during collection')
            item.update(status='present', bytes=after.st_size, sha256=h.hexdigest(), mtime_ns=after.st_mtime_ns)
            if copy:
                (output / label).write_bytes(data)
                item['artifact'] = label
                return bytes(data)
        except FileNotFoundError:
            if required:
                errors.append(label + ': missing')
        except (OSError, ValueError) as exc:
            item['status'] = 'error'
            item['error_type'] = type(exc).__name__
            errors.append(label + ': read failed')
        return None

    lock = capture('Cargo.lock', bridge / 'Cargo.lock', copy=True)
    if lock is not None:
        try:
            parsed = tomllib.loads(lock.decode('utf-8'))
            packages = parsed.get('package', [])
            if parsed.get('version') not in (3, 4) or not packages or not all(isinstance(p, dict) and p.get('name') and p.get('version') for p in packages):
                raise ValueError('invalid Cargo lock shape')
            report['lock'] = {'status': 'parsed', 'format': parsed['version'], 'packages': len(packages),
                              'registry_packages': sum(str(p.get('source', '')).startswith('registry+') for p in packages),
                              'with_checksums': sum('checksum' in p for p in packages)}
        except (UnicodeError, ValueError, TypeError):
            report['lock'] = {'status': 'invalid'}
            errors.append('Cargo.lock: invalid')

    # Preserve the exact source hash, but publish a parsed canonical representation with path fields normalized.
    manifest_path = bridge / 'Cargo.toml'
    capture('manifest-original', manifest_path)
    try:
        manifest_raw = manifest_path.read_bytes()
        if digest(manifest_raw) != report['files']['manifest-original'].get('sha256'):
            raise ValueError('manifest changed')
        manifest = tomllib.loads(manifest_raw.decode('utf-8'))
        tree_lexical = Path(os.path.abspath(tree))
        source_input_path = source_input
        source_lexical = Path(os.path.abspath(source_input_path))
        source_root = Path(source).resolve()
        component_link = tree / 'drivers/AdrenoMetal'
        try:
            component_resolved = component_link.resolve(strict=True)
            component_root = component_resolved if component_resolved != Path(os.path.abspath(component_link)) else None
            if component_root is not None and not component_root.is_dir():
                component_root = None
        except OSError:
            component_root = None

        def normalize_path(value):
            raw = Path(value)
            lexical = Path(os.path.abspath(raw if raw.is_absolute() else manifest_path.parent / raw))
            resolved = lexical.resolve()

            def relative(path, base):
                try:
                    return path.relative_to(base)
                except ValueError:
                    return None

            # Keep paths written through the known tree alias stable, but only
            # dereference an external target when it is the configured component.
            tree_lex_rel = relative(lexical, tree_lexical)
            source_lex_rel = relative(lexical, source_lexical)
            if source_lex_rel is not None:
                source_rel = relative(resolved, source_root)
                if source_rel is not None:
                    return '<translator>/' + source_rel.as_posix()
                component_rel = relative(resolved, component_root) if component_root is not None else None
                if component_rel is not None:
                    suffix = component_rel.as_posix()
                    return '<tree>/drivers/AdrenoMetal' + ('/' + suffix if suffix != '.' else '')
                raise ValueError('source path resolved outside configured roots')

            if tree_lex_rel is not None:
                if component_root is not None and tree_lex_rel.parts[:2] == ('drivers', 'AdrenoMetal'):
                    component_rel = relative(resolved, component_root)
                    if component_rel is None:
                        raise ValueError('component link escaped its configured root')
                    suffix = component_rel.as_posix()
                    return '<tree>/drivers/AdrenoMetal' + ('/' + suffix if suffix != '.' else '')
                tree_rel = relative(resolved, tree)
                if tree_rel is not None:
                    return '<tree>/' + tree_rel.as_posix()
                raise ValueError('tree path resolved outside declared roots')

            tree_rel = relative(resolved, tree)
            if tree_rel is not None:
                return '<tree>/' + tree_rel.as_posix()
            source_rel = relative(resolved, source_root)
            if source_rel is not None:
                return '<translator>/' + source_rel.as_posix()
            component_rel = relative(resolved, component_root) if component_root is not None else None
            if component_rel is not None:
                suffix = component_rel.as_posix()
                return '<tree>/drivers/AdrenoMetal' + ('/' + suffix if suffix != '.' else '')
            raise ValueError('manifest path outside declared roots and configured component link')

        def normalize(value, key=''):
            if isinstance(value, dict):
                return {k: normalize(v, k) for k, v in value.items()}
            if isinstance(value, list):
                return [normalize(v, key) for v in value]
            if key == 'path' and isinstance(value, str):
                return normalize_path(value)
            return value
        normalized = (json.dumps(normalize(manifest), sort_keys=True, indent=2) + '\n').encode()
        (output / 'manifest.normalized.json').write_bytes(normalized)
        report['manifest_normalized'] = {'sha256': digest(normalized), 'bytes': len(normalized),
                                        'artifact': 'manifest.normalized.json', 'format': 'parsed TOML canonical JSON, not builder identity hash'}
    except (OSError, ValueError, TypeError):
        errors.append('Cargo.toml: missing, invalid, changed, or path outside roots')

    archive = bridge / target / 'libadreno_metal_bridge.a'
    capture('archive', archive)
    metadata = capture('archive.metadata.json', archive.with_suffix('.a.json'), copy=True)
    if metadata is not None:
        try:
            record = json.loads(metadata)
            identity = record['identity']
            if identity['target'] != target or record['sha256'] != report['files']['archive'].get('sha256'):
                raise ValueError('archive identity mismatch')
            report['archive_check'] = 'hash-and-target-match'
        except (ValueError, KeyError, TypeError):
            report['archive_check'] = 'invalid-or-mismatch'
            errors.append('archive metadata: invalid or mismatched')
    capture('bridge-build.log', bridge / ('build-' + target + '.log'), copy=True, required=False)
    capture('translator.Cargo.lock', source / 'Cargo.lock', copy=True, required=False)
    capture('builder.py', tree / 'scripts/build-adreno-metal-bridge.py', copy=True)

    def run(argv):
        try:
            result = subprocess.run(argv, cwd=tree, capture_output=True, text=True, timeout=30)
            return dict(returncode=result.returncode, stdout=result.stdout.strip(), stderr=result.stderr.strip())
        except (OSError, subprocess.TimeoutExpired) as exc:
            return dict(returncode=None, stdout='', error_type=type(exc).__name__)
    probe = probe or run
    commands = {'rustc': ['rustup', 'run', '1.98.0', 'rustc', '-vV'],
                'cargo': ['rustup', 'run', '1.98.0', 'cargo', '-Vv']}
    for name, argv in commands.items():
        result = probe(argv)
        report['tools'][name] = dict(command=argv, **result)
        if result.get('returncode') != 0 or not result.get('stdout'):
            errors.append(name + ': identity unavailable')
        elif not result['stdout'].startswith(name + ' 1.98.0 '):
            errors.append(name + ': unexpected tool version')
    # Hash rust-src lock when shipped. Its absence is explicit and does not invent a pinned std dependency graph.
    sysroot = probe(['rustup', 'run', '1.98.0', 'rustc', '--print', 'sysroot'])
    report['rust_src'] = {'sysroot_probe_returncode': sysroot.get('returncode'), 'scope': 'optional installed std source lock observation'}
    if sysroot.get('returncode') == 0 and sysroot.get('stdout'):
        capture('rust-src.Cargo.lock', Path(sysroot['stdout'].strip()) / 'lib/rustlib/src/rust/library/Cargo.lock', copy=True, required=False)
    else:
        report['rust_src']['status'] = 'sysroot-unavailable'
    report['status'] = 'incomplete' if errors else 'snapshot-complete'
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='New directory outside input tree')
    parser.add_argument('--source', type=Path)
    parser.add_argument('--target', choices=['ios', 'ios27', 'macos27', 'host'], default='ios27')
    args = parser.parse_args()
    try:
        report = collect(args.tree, args.output, args.target, args.source)
    except (OSError, ValueError) as exc:
        print('Collector setup failed: ' + type(exc).__name__)
        return 2
    print(json.dumps({'status': report['status'], 'errors': report['errors']}))
    return 0 if report['status'] == 'snapshot-complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
