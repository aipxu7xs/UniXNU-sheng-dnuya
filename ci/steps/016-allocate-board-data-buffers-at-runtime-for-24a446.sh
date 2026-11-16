python3 - <<'PY'
"""Strict IrisMedia.cpp permanent-storage patch (68800685 layout)."""
import argparse
import hashlib
from pathlib import Path

def apply(source: str) -> str:
    if hashlib.sha256(source.encode('utf-8')).hexdigest() != '5e5d039163862ea0c31402bad42d47d2c1202da6250158b5ac11ab9b894fcd6a':
        raise ValueError('IrisMedia.cpp differs from pinned 68800685 source')

    def replace(old, new, count=1):
        nonlocal source
        actual = source.count(old)
        if actual != count:
            raise ValueError(f'Iris storage anchor expected {count}, found {actual}: {old[:100]!r}')
        source = source.replace(old, new)
    replace('Media gTable[MaxSessions];\nuint32_t gNextId = 1;\nNote gRing[RingSize];', '// Allocated once, retained for the lifetime of the driver/event thread.\n// Every access and publication is protected by the device lock.\nstruct MediaStorage {\n    Media table[MaxSessions];\n    Note ring[RingSize];\n};\nMediaStorage *gStorage;\nuint32_t gNextId = 1;')
    replace('IOLock *lock() { return QcomIrisDeviceLock(); }', 'IOLock *lock() { return QcomIrisDeviceLock(); }\n// Called without the device lock: allocation may block. Losers free only\n// their unpublished candidate; the published storage is never reclaimed.\nbool ensureStorage() {\n    IOLock *l = lock();\n    IOLockLock(l);\n    const bool ready = gStorage != nullptr;\n    IOLockUnlock(l);\n    if (ready) return true;\n    MediaStorage *candidate = static_cast<MediaStorage *>(IOMalloc(sizeof(MediaStorage)));\n    if (candidate) memset(candidate, 0, sizeof *candidate);\n    IOLockLock(l);\n    if (!gStorage && candidate) { gStorage = candidate; candidate = nullptr; }\n    const bool published = gStorage != nullptr;\n    IOLockUnlock(l);\n    if (candidate) IOFree(candidate, sizeof *candidate);\n    return published;\n}')
    replace('bool gThreadStarted;', 'bool gThreadStarted, gThreadStarting;')
    replace('Media *find(uint32_t id) {', 'Media *find(uint32_t id) {\n    if (!gStorage) return nullptr;')
    replace('for (Media &m : gTable)', 'for (Media &m : gStorage->table)')
    replace('for (Media &candidate : gTable)', 'for (Media &candidate : gStorage->table)')
    replace('void note(const Note &n) {', 'void note(const Note &n) {\n    if (!gStorage) return;')
    replace('gRing[gHead++ % RingSize]', 'gStorage->ring[gHead++ % RingSize]')
    replace('gRing[gTail++ % RingSize]', 'gStorage->ring[gTail++ % RingSize]')
    replace('&gRing', '&gStorage', 2)
    replace('while (gHead == gTail)', 'while (!gStorage || gHead == gTail)')
    replace("/* ---- the firmware's callbacks", "// Reserve startup under the lock, but create the thread outside it. A failed\n// creation releases the reservation so either set_sink or open can retry.\nbool startEventThread() {\n    IOLock *l = lock();\n    IOLockLock(l);\n    const bool start = gStorage && gSink && !gThreadStarted && !gThreadStarting;\n    if (start) gThreadStarting = true;\n    IOLockUnlock(l);\n    if (start) {\n        thread_t thread;\n        if (kernel_thread_start(eventThread, nullptr, &thread) == KERN_SUCCESS) thread_deallocate(thread);\n        else {\n            IOLockLock(l);\n            gThreadStarting = false;\n            IOLockUnlock(l);\n            return false;\n        }\n        IOLockLock(l);\n        gThreadStarted = true;\n        gThreadStarting = false;\n        IOLockUnlock(l);\n    }\n    return true;\n}\n\n/* ---- the firmware's callbacks")
    replace('    const bool start = !gThreadStarted;\n    gThreadStarted = true;\n    IOLockUnlock(lock());\n    if (start) {\n        thread_t thread;\n        if (kernel_thread_start(eventThread, nullptr, &thread) == KERN_SUCCESS) thread_deallocate(thread);\n    }\n}', '    IOLockUnlock(lock());\n    // Keep the sink even on allocation failure; open can retry initialization.\n    if (ensureStorage()) startEventThread();\n}')
    replace('    if (!iris_media_is_up(device) || !session) return Enodev;', '    if (!iris_media_is_up(device) || !session) return Enodev;\n    if (!ensureStorage()) return Enomem;\n    if (!startEventThread()) return Enomem;')
    replace('    Media *m = nullptr;', '    if (gSink && !gThreadStarted) { IOLockUnlock(lock()); return Ebusy; }\n    Media *m = nullptr;')
    if 'gTable' in source or 'gRing' in source:
        raise ValueError('unconverted Iris array reference')
    return source
p = Path('device/drivers/QcomIris/kernel/IrisMedia.cpp')
original = p.read_text(encoding="utf-8")
patched = apply(original)
assert patched != original
p.write_text(patched, encoding="utf-8")
print("STORAGE PATCH APPLIED", str(p))
"""Strict fixed-68800685 BootUiTraceProbe permanent-storage transformation.

Only begin's sole BootProcessWorker caller may allocate. Published readers still
use trace_lock; acquire/release of the permanent pointer publishes initialization,
not subsequent mutable data. No free/replacement is permitted during kernel life.
"""
import argparse
import hashlib
from pathlib import Path
import re
SOURCE_BLOB = 'c8ec96989880ee6623d1b04c5854863e8896ebe7'
FIELDS = ('samples', 'draft', 'published', 'hot_prev', 'sample_k')
ENTRIES = {'void boot_ui_trace_begin(void) {': 'begin', 'void boot_ui_trace_task(task_t task,unsigned index,int pid,const char *name,unsigned slide) {': 'return;', 'void boot_ui_trace_publish(void) {': 'return;', 'unsigned boot_ui_trace_role_rows(unsigned role,char rows[][120],unsigned max,unsigned detail) {': 'return 0;', 'unsigned boot_ui_trace_hot_rows(char rows[][120],unsigned max) {': 'return 0;', 'int boot_ui_trace_role_peer(unsigned role) {': 'return -1;', 'void boot_ui_trace_snapshot(unsigned seconds) {': 'return;'}
STORAGE = '// UI trace storage is allocated once by BootProcessWorker and never freed.\n// The pointer publishes initialization; trace_lock still protects published data.\nstruct bt_trace_storage {\n struct bt_entry samples[BT_MAX_THREADS];\n struct bt_groups draft,published;\n struct bt_prev hot_prev[BT_ROLES][BT_MAX_THREADS];\n uint64_t sample_k[BT_MAX_THREADS][BT_KFRAMES];\n};\nstatic struct bt_trace_storage *bt_trace_storage_ptr;\nvoid *IOMallocAligned(vm_size_t,vm_offset_t);\n'
BEGIN = '\n struct bt_trace_storage *storage=__atomic_load_n(&bt_trace_storage_ptr,__ATOMIC_ACQUIRE);\n if(!storage) {\n  // Only the single capture worker calls begin; allocate outside all trace locks.\n  storage=IOMallocAligned(sizeof(*storage),__alignof__(struct bt_trace_storage));\n  if(!storage)return; // Retry next pass; readers safely return while unavailable.\n  memset(storage,0,sizeof(*storage));\n  __atomic_store_n(&bt_trace_storage_ptr,storage,__ATOMIC_RELEASE);\n }\n'

def once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('UI storage anchor must occur exactly once: ' + repr(old))
    return source.replace(old, new, 1)

def apply(source: str) -> str:
    raw = source.encode('utf-8')
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\x00' + raw).hexdigest()
    if blob != SOURCE_BLOB:
        raise ValueError('UI storage source drift/already patched: expected ' + SOURCE_BLOB + ', got ' + blob)
    source = once(source, 'static struct bt_entry samples[BT_MAX_THREADS];', '')
    source = once(source, 'static struct bt_prev hot_prev[BT_ROLES][BT_MAX_THREADS];', '')
    source = once(source, 'static struct bt_groups draft,published;', '')
    source = once(source, 'static uint64_t sample_k[BT_MAX_THREADS][BT_KFRAMES],sample_event[BT_MAX_THREADS];', 'static uint64_t sample_event[BT_MAX_THREADS];')
    source = once(source, 'void *IOMallocAligned(vm_size_t,vm_offset_t);', '')
    token = re.compile('//[^\\n]*|/\\*.*?\\*/|"(?:\\\\.|[^"\\\\])*"|\'(?:\\\\.|[^\'\\\\])*\'|[A-Za-z_][A-Za-z_0-9]*', re.S)
    source = token.sub(lambda m: 'storage->' + m[0] if m[0] in FIELDS else m[0], source)
    for signature, result in ENTRIES.items():
        guard = BEGIN if result == 'begin' else '\n struct bt_trace_storage *storage=__atomic_load_n(&bt_trace_storage_ptr,__ATOMIC_ACQUIRE);\n if(!storage)' + result + '\n'
        source = once(source, signature, signature + guard)
    source = once(source, 'void boot_ui_trace_begin(void) {', STORAGE + '\nvoid boot_ui_trace_begin(void) {')
    if source.count('__atomic_load_n(&bt_trace_storage_ptr,__ATOMIC_ACQUIRE)') != 7:
        raise ValueError('missing UI storage entry guard')
    if source.count('__atomic_store_n(&bt_trace_storage_ptr,storage,__ATOMIC_RELEASE)') != 1:
        raise ValueError('invalid UI storage publication')
    return source
p = Path('device/package/BootUiTraceProbe.c')
original = p.read_text(encoding="utf-8")
patched = apply(original)
assert patched != original
p.write_text(patched, encoding="utf-8")
print("STORAGE PATCH APPLIED", str(p))
PY
