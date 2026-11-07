"""Validate that one HTML version selects one immutable asset/data snapshot."""
import pathlib,json,re,hashlib
root=pathlib.Path(__file__).resolve().parents[1];site=root/'_site';m=json.loads((site/'deployment.json').read_text());html=(site/'index.html').read_text();digest=lambda b:hashlib.sha256(b).hexdigest()
assert digest(html.encode())==m['indexSha256']
for name,path in m['assets'].items():
 assert re.search(r'\.[0-9a-f]{20}\.',path),path
 assert (site/path).read_bytes()==(root/'dist'/name).read_bytes()
for name in ['app.js','review.js','yearly.js','style.css']:assert m['assets'][name] in html
assert html.index(m['bootstrap'])<html.index(m['assets']['app.js'])
boot=(site/m['bootstrap']).read_text();assert 'IncidentAtlasAssets' in boot
for k,v in m['assets'].items():assert json.dumps(k)+':'+json.dumps(v) in boot
app=(root/'dist/app.js').read_text();assert "review='all'" in app and "setReview('all')" in app
assert "fetch(ASSET_URLS[u]||u,{cache:'no-store'})" in app
assert "ledger.records.filter(r=>!r.recordIds?.length).map" in app
r=json.loads((site/m['assets']['reconciliation.json']).read_text())['records'];records=json.loads((site/m['assets']['data.json']).read_text());h=json.loads((site/m['assets']['historical.json']).read_text())
print('One-version asset snapshot verified. Initial all-record view:',len(records)+len(h['rows'])+sum(not d.get('recordIds') for d in r),'records, including',sum(not d.get('recordIds') for d in r),'explicitly unverified discovery candidates.')
