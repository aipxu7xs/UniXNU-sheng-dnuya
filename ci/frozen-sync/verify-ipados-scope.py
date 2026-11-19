"""Verify source selection for sheng/iPadOS 27, independently of source synchronization."""
import argparse
import hashlib
import json
from pathlib import Path
import tomllib
EXPECTED = {'UniXNU/scripts/make-gpu-addon.py': 'a7132ff58fd92bda2995f49d3344224a6ee14d1ae7801a9646dda529d1617979', 'UniXNU/scripts/build-boot-runtime.py': '7ff232fa13dcf3b9c3c8ad42d1d3def664503421b2b2820d099a97d507b6a729', 'UniXNU/scripts/build-fileset-release-reference.py': 'ddb66164bca695a7ff329b71d2088277d106494a11930b11e88176fc369d86c0'}

def verify(root):
    board = tomllib.loads((root / 'device/board.toml').read_text())
    assert board['board']['os_profile'] == 'ipados-27.0.1-24A446'
    assert board['adt']['defaults']['u32']['sleep-disabled'] == 1
    args = board['payload']['kernel_args']
    selected = board.get('os_overrides', {}).get('ipados-27.0.1-24A446', {})
    args = selected.get('payload', {}).get('kernel_args', args)
    assert not any(a.startswith('platform-sleep=') and a != 'platform-sleep=0' for a in args)
    assert not any('macos' in a.lower() for a in args)
    assert 'data-persist=2' in args
    for name, digest in EXPECTED.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    text = (root / 'UniXNU/scripts/build-boot-runtime.py').read_text()
    assert 'ICON_CACHE_FUNCTION' not in text
    assert 'org.unixnu.icon-cache.generation' not in text
    reference = (root / 'UniXNU/scripts/build-fileset-release-reference.py').read_text()
    assert 'def target_define(' not in reference
    assert '-DXNU_TARGET_OS_IOS' in reference
    return dict(status='PASS_SOURCE_SCOPE', profile=board['board']['os_profile'],
                source_synchronization_is_separate_from_activation=True,
                platform_sleep_enabled=False, desktop_icon_cache_adopted=False,
                data_preservation_argument='data-persist=2', exact_shared_builders=EXPECTED,
                native_compilation_verified=False, hardware_verified=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.workspace.resolve(strict=True)), indent=2))
