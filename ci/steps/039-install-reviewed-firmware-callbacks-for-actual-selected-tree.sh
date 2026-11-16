python3 - <<'PY'
import runpy,json,pathlib
report=runpy.run_path('reviewed-source-bundle/firmware/install.py')['install']('UniXNU','device')
pathlib.Path('reviewed-firmware-install.json').write_text(json.dumps(report,indent=2))
print('REVIEWED_FIRMWARE_HOOK_INSTALL',json.dumps(report))
PY
