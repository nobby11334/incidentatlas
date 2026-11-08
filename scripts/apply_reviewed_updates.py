"""Apply individually reviewed changes once, preserving any later dated editorial changes."""
import json,pathlib
R=pathlib.Path(__file__).resolve().parents[1];p=R/'dist/data.json';data=json.loads(p.read_text());byid={r['id']:r for r in data}
for update in json.loads((R/'sources/reviewed-updates.json').read_text()):
 old=byid.get(update['id'])
 if old is None:data.append(update);byid[update['id']]=update
 elif (old.get('checked') or '')<update['checked']:
  old.update(update)
p.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
# Reviewed findings also enter the discovery ledger; keep every pre-existing key and source.
ledger_path=R/'dist/reconciliation.json';ledger=json.loads(ledger_path.read_text());bykey={r['key']:r for r in ledger['records']}
for update in json.loads((R/'sources/reviewed-updates.json').read_text()):
 key='reviewed-'+update['id'];urls=[u for _,u in update['sources']]
 bykey[key]=dict(key=key,organization=update['org'],published=update['published'],inventory='個別一次資料探索',discovery=urls[0],primaryUrls=urls,recordIds=[update['id']],result='一次資料を個別参照した項目あり')
ledger['records']=list(bykey.values());ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,separators=(',',':')))
manifest_path=R/'dist/source-manifest.json';manifest=json.loads(manifest_path.read_text());rows=ledger['records']
manifest['discovered']=manifest['accounted']=len(rows)
manifest['sources']=[dict(name=n,discovered=len(rs),accounted=len(rs),linked=sum(bool(r.get('recordIds')) for r in rs),pending=sum(not r.get('recordIds') for r in rs),first=min((r['published'] for r in rs if r['published']),default=None),last=max((r['published'] for r in rs if r['published']),default=None)) for n in sorted({r['inventory'] for r in rows}) for rs in [[r for r in rows if r['inventory']==n]]]
manifest['months']=[dict(month=m,discovered=len(rs),linked=sum(bool(r.get('recordIds')) for r in rs),pending=sum(not r.get('recordIds') for r in rs)) for m in sorted({r['published'][:7] or '日付未特定' for r in rows}) for rs in [[r for r in rows if (r['published'][:7] or '日付未特定')==m]]]
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')))
