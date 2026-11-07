"""Release checks for source identity, merged provenance and reviewed publication aliases."""
import collections,json,pathlib
from publication_identity import urlkey,orgkey
R=pathlib.Path(__file__).resolve().parents[1];read=lambda p:json.loads(p.read_text());data=read(R/'dist/data.json');ledger=read(R/'dist/reconciliation.json')['records'];byid={r['id']:r for r in data};keys={}
for r in data:
 if r.get('anonymous'):continue
 for _,u in r['sources']:
  k=(orgkey(r['org']),urlkey(u));assert k not in keys or keys[k]==r['id'],('Duplicate source',k);keys[k]=r['id']
 for old in r.get('mergedPublications',[]):
  assert old['id'] not in byid
  assert {u for _,u in old['sources']}.issubset({u for _,u in r['sources']})
for rule in read(R/'sources/publication-merges.json'):
 assert all(i not in byid for i in rule['duplicateIds'])
 assert set(rule['evidence']).issubset({u for _,u in byid[rule['canonicalId']]['sources']})
bykey={r['key']:r for r in ledger}
for r in ledger:
 assert all(i in byid for i in r.get('recordIds',[]))
 if r.get('duplicateOfKey'):
  target=bykey[r['duplicateOfKey']];assert not target.get('duplicateOfKey')
  assert any(a['key']==r['key'] for a in target.get('discoveryAliases',[]))
print('Duplicate source identities and retained provenance verified:',len(data),'public records')
