python3 - <<'PY'
import runpy,json,pathlib
report=runpy.run_path('reviewed-source-bundle/ufs.py')['apply']('device','UniXNU')
pathlib.Path('reviewed-ufs-report.json').write_text(json.dumps(report,indent=2))
print('REVIEWED_UFS_PIN',json.dumps(report))
PY
