python3 - <<'PY'
import hashlib, os
with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
    out.write('key=data-seed-v1-' + hashlib.sha256(os.environ['SEED'].encode()).hexdigest()[:16] + '\n')
PY
