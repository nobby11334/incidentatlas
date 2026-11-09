"""Accept only a provably preserved generated-data commit made during collection.
Anything outside generated files, or any changed prior record, remains a hard conflict.
"""
import json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];P=R/'source-cache/all-cache'
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
subprocess.run(['git','fetch','origin','main'],cwd=R,check=True)
if git('rev-parse','HEAD')!=git('rev-parse','origin/main'):
 changed=set(git('diff','--name-only','HEAD','origin/main').splitlines())
 allowed={'dist/data.json','dist/reconciliation.json','dist/source-manifest.json','dist/duplicate-audit.json'}
 assert changed<=allowed,'Concurrent source/editorial files changed; refusing to overwrite'
 baseline={r['id']:r for r in json.loads((P/'baseline.json').read_text())}
 remote=json.loads(git('show','origin/main:dist/data.json'))
 assert all(baseline.get(r['id'])==r for r in remote),'Concurrent record edits differ from protected baseline'
 ledger={r['key']:r for r in json.loads((P/'ledger-baseline.json').read_text())['records']}
 for r in json.loads(git('show','origin/main:dist/reconciliation.json'))['records']:
  assert r['key'] in ledger,'Concurrent discovery entry missing from collection'
  local=ledger[r['key']]
  assert {k:v for k,v in r.items() if k!='primaryUrls'}=={k:v for k,v in local.items() if k!='primaryUrls'},'Concurrent discovery edits differ'
  assert set(r.get('primaryUrls',[]))<=set(local.get('primaryUrls',[])),'Concurrent source URL would be lost'
 # Only move the local parent; collected working files are retained and normal push stays fast-forward.
 subprocess.run(['git','reset','--soft',git('rev-parse','origin/main')],cwd=R,check=True)
 print('Preserved concurrent generated-data commit; normal fast-forward collection commit is now possible.',flush=True)
