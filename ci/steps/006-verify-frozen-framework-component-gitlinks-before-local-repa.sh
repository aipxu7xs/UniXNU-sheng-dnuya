python3 - <<'PY'
import pathlib,subprocess,json,tomllib
root=pathlib.Path('UniXNU')
def git(path,*args):return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
FRAMEWORK='71b8a5a3d78edfe6404a706c1ebccd9915fb3c5e'
PINS={'drivers/ArmCpu': 'acba4ee2674cfb23434431feb124871ae9b3b581', 'drivers/Adreno740': '1c9029bc3216a39d9e514ba41dee12e95e8f3598', 'drivers/AdrenoMetal': '54c18dcffc359d21f4e620c3b38b3908cecc46a5', 'drivers/RamBlock': '00a6e5dd6bb1709e817e13daec7986308cfb6d0f', 'drivers/DarwinBoot': '5243c68ec332a227fe3680cd5da6d5a0e127035c', 'kits/XnuPrelink': '440589b0c31625f17edf363e24b3c82c51c70bb9'}
assert git(root,'rev-parse','HEAD')==FRAMEWORK,'framework checkout differs'
for relative,pin in PINS.items():
 sub=root/relative
 assert git(sub,'rev-parse','HEAD')==pin,(relative,'checkout')
 assert git(root,'ls-files','--stage','--',relative).split()[1]==pin,(relative,'index gitlink')
 assert git(root,'rev-parse','HEAD:'+relative)==pin,(relative,'committed gitlink')
 assert not git(sub,'status','--porcelain'),relative+' has unreviewed edits before local repairs'
print('FROZEN_COMPONENT_SOURCES',json.dumps(PINS,sort_keys=True))
PY
