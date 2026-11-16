python3 - <<'PY'
import os, pathlib, subprocess
# macOS-only hooks. The default must reproduce the ABSENT-hook path,
# a wrong value silently changes behaviour:
#   * iokit_physical_descriptor_close_notify is an existence probe:
#     tracked_ = hook && call(...) == KERN_SUCCESS, and KERN_SUCCESS is 0,
#     so returning 0 would mark every GPU pool view "tracked" while the
#     stub never reports a close -> the grant is never returned (leak).
#     Non-zero return retires the grant, like a kernel without the patch.
#   * native_legacy_request_layout is the rejection report's offset table;
#     zeroes read every field at offset 0, so it carries the same iPadOS 17
#     fallback values LegacyDisplayProbe.cpp uses.
#   * ml_static_mfree_prepare returns bool; false keeps release off.
src = ['/* weak defaults for macOS-only hooks; values match the absent-hook path */',
       '#define WEAK __attribute__((weak, visibility("hidden")))',
       'WEAK unsigned long cs_native4k_digest_bytes[2];',
       'WEAK unsigned long cs_native4k_digest_cpu[2];',
       'WEAK unsigned long cs_native4k_digest_wall[2];',
       'WEAK unsigned long cs_native4k_record_ticks;',
       'WEAK unsigned long cs_native4k_chunk_ticks;',
       'WEAK unsigned long cs_native4k_read_ticks;',
       'WEAK unsigned long cs_native4k_hash_ticks;',
       'WEAK unsigned long cs_native4k_bytes;',
       'WEAK unsigned long cs_native4k_ready_blobs;',
       'WEAK unsigned long cs_native4k_chunks_made;',
       'WEAK const unsigned native_legacy_request_layout[6] = {17, 81, 792, 804, 816, 2624};',
       'WEAK long ml_static_mfree_prepare(void) { return 0; }',
       'WEAK long iokit_physical_descriptor_close_notify(void) { return -1; }',
       'WEAK void sheng_ethernet_probe(void) {}',
       'WEAK void sheng_software_aes_probe(void) {}',
       '/* 24A446 excludes the USB host/device kext closure and omits QcomDwc3. */',
       'WEAK void qcom_dwc3_vbus(int value) { (void)value; }',
       'WEAK unsigned qcom_ucsi_start(unsigned char *out) { (void)out; return 0; }',
       'WEAK unsigned qcom_ucsi_receive(const unsigned char *in, unsigned length, unsigned char *out) { (void)in; (void)length; (void)out; return 0; }',
       'WEAK unsigned qcom_ucsi_tick(unsigned char *out) { (void)out; return 0; }',
       'WEAK int qcom_ucsi_polling(void) { return 0; }',
       'WEAK void sheng_usb_probe(void) {}',
       'WEAK long native_hooks_stub_marker(void) { return 0; }']
if os.environ['USB_PROFILE'] == '27':
    src = [line for line in src if not any(name in line for name in ('qcom_dwc3_vbus', 'qcom_ucsi_', 'sheng_usb_probe', 'USB host/device kext closure'))]
    assert not any('qcom_' in line or 'sheng_usb_probe' in line for line in src)
path = pathlib.Path('ci-device-stubs.c')
path.write_text(chr(10).join(src) + chr(10))
sdk = subprocess.check_output(['xcrun', '--sdk', 'iphoneos', '--show-sdk-path'], text=True).strip()
obj = pathlib.Path(subprocess.check_output(['pwd'], text=True).strip()) / 'ci-device-stubs.o'
subprocess.run(['xcrun', 'clang', '-arch', 'arm64e', '-mkernel', '-isysroot', sdk,
                '-c', '-o', str(obj), str(path)], check=True)
print('compiled weak stubs ->', obj, os.path.getsize(obj), 'bytes')
with open(os.environ['GITHUB_ENV'], 'a') as env:
    env.write('CI_DEVICE_STUBS=' + str(obj) + chr(10))
PY
python3 - <<'PY'
import pathlib
p = pathlib.Path('UniXNU/scripts/build-xnu-4k-baseline.sh')
t = p.read_text()
old = 'KERNEL_EXTRA_ARCHIVES="-L$KERNEL_SDKROOT/usr/local/lib/kernel -lfirehose_kernel $CRYPTO_ARCHIVE"'
forced = [
    'native_source_storage_start',
    'native_verified_block_root_authorized',
    'native_verified_block_manifest_sha384',
    'native_verified_block_volume_device',
    'native_ram_block_volume_seed',
    'native_ram_block_gpu_addon',
    'sheng_boot_watchdog_policy',
]
new = ('KERNEL_EXTRA_ARCHIVES="-L$KERNEL_SDKROOT/usr/local/lib/kernel -lfirehose_kernel $CRYPTO_ARCHIVE'
       + ''.join(' -Wl,-u,_%s' % n for n in forced)
       + '${CI_DEVICE_STUBS:+ -Wl,-force_load,$CI_DEVICE_STUBS}"')
if 'CI_DEVICE_STUBS' in t:
    print('baseline script: already patched')
elif old not in t:
    raise SystemExit('baseline script: KERNEL_EXTRA_ARCHIVES anchor not found')
else:
    p.write_text(t.replace(old, new, 1))
    print('baseline script: CI_DEVICE_STUBS force-load added')
PY
