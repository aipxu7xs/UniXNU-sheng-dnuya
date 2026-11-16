for name in amss.bin m3.bin board-2.bin; do
  curl -fsSL --retry 3 -o "firmware/wcn7850/$name" \
    "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/plain/ath12k/WCN7850/hw2.0/$name?id=$LINUX_FIRMWARE" ||
  curl -fsSL --retry 3 -o "firmware/wcn7850/$name" \
    "https://gitlab.com/kernel-firmware/linux-firmware/-/raw/$LINUX_FIRMWARE/ath12k/WCN7850/hw2.0/$name"
done
python3 - <<'PY'
import hashlib, json, pathlib
folder = pathlib.Path('firmware/wcn7850')
for name, want in json.loads((folder / 'manifest.json').read_text())['files'].items():
    data = (folder / name).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if len(data) != want['bytes'] or digest != want['sha256']:
        raise SystemExit(f'{name}: {len(data)} bytes sha256 {digest} differs from firmware/wcn7850/manifest.json')
    print(f'{name}: {len(data)} bytes sha256 {digest} matches the manifest')
PY
