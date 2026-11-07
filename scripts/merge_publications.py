"""Apply only explicitly reviewed publication aliases; preserve all original source URLs."""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text())
def apply():
 data=read(ROOT/'dist/data.json');byid={r['id']:r for r in data};aliases={};rules=read(ROOT/'sources/publication-merges.json')
 for rule in rules:
  canonical=byid[rule['canonicalId']]
  assert canonical['org']==rule['organization'] and canonical['published']==rule['published']
  for old in rule['duplicateIds']:
   aliases[old]=canonical['id'];duplicate=byid.get(old)
   if not duplicate:continue
   assert duplicate['org']==canonical['org'] and duplicate['published']==canonical['published']
   canonical['sources']=[list(s) for s in dict.fromkeys(tuple(s) for s in canonical['sources']+duplicate['sources'])]
   canonical['discoverySources']=list(dict.fromkeys(canonical.get('discoverySources',[])+duplicate.get('discoverySources',[])))
   canonical['mergedRecordIds']=list(dict.fromkeys(canonical.get('mergedRecordIds',[])+[old]))
   canonical['mergeReason']=rule['reason'];canonical['mergeChecked']=rule['checked']
 data=[r for r in data if r['id'] not in aliases]
 ledger=read(ROOT/'dist/reconciliation.json')
 for row in ledger['records']:
  if row.get('recordIds'):row['recordIds']=sorted({aliases.get(i,i) for i in row['recordIds']})
 for name,value in [('data.json',data),('reconciliation.json',ledger)]:
  (ROOT/'dist'/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')))
 assert all(old not in {r['id'] for r in data} for old in aliases)
 for rule in rules:
  assert set(rule['evidence']).issubset({u for label,u in byid[rule['canonicalId']]['sources']})
 print('Reviewed publication aliases',len(aliases),'canonical public records',len(data),flush=True)
if __name__=='__main__':apply()
