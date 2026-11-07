"""Refresh all three original discovery inventories without replacing editorial records."""
import json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];P=ROOT/'source-cache/all-cache';P.mkdir(parents=True,exist_ok=True);archive=ROOT/'source-cache/public-archive'
if archive.exists():subprocess.run(['git','pull','--ff-only'],cwd=archive,check=True)
else:subprocess.run(['git','clone','--depth=1','https://github.com/piyokango/SecurityIncidentArchive.git',str(archive)],check=True)
subprocess.run(['python','scripts/collect_sources.py',str(archive)],cwd=ROOT,check=True)
read=lambda p:json.loads(p.read_text());ledger=read(ROOT/'dist/reconciliation.json');bykey={r['key']:r for r in ledger['records']}
for d in read(P/'details.json'):
 if d['key'] not in bykey:
  bykey[d['key']]=dict(key=d['key'],organization=d['org'],published=d.get('published',''),inventory=d['inventory'],discovery=d['discovery'],primaryUrls=d.get('primaryUrls',[]),result='新規索引記録・本文確認待ち')
 else:
  r=bykey[d['key']];r['primaryUrls']=sorted(set(r.get('primaryUrls',[])+d.get('primaryUrls',[])))
ledger['records']=list(bykey.values());(ROOT/'dist/reconciliation.json').write_text(json.dumps(ledger,ensure_ascii=False,separators=(',',':')))
print('Refreshed original inventories',len(ledger['records']),flush=True)
