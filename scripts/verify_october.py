import json,pathlib
p=pathlib.Path(__file__).resolve().parents[1]/'dist';data=json.loads((p/'data.json').read_text());audit=json.loads((p/'october-2026-audit.json').read_text());by={d['id']:d for d in data};added=[d for d in data if d.get('collectionBatch')=='2026-10-reconciliation']
assert len(by)==len(data)
assert len(added)==audit['addedRecords'] and len(added)>=600
assert audit['discoveryRecords']==922
for d in added:
 assert d['published'].startswith('2026-10') and d['sources']
 assert all(u.startswith(('https://','http://')) and 'radineer.asia' not in u and 'incidents.seory.co.jp' not in u for _,u in d['sources'])
 if d.get('verification')=='一次資料の機械照合・詳細精査前':assert d.get('confirmed') is None and d.get('potential') is None and d.get('loss') is None
for ident,n in [('burgerking-2026',11180000),('nikkei-devcloud-2026',150000)]:assert by[ident]['confirmed']==n
assert by['nifty-line-2026']['potential']==18000
assert by['lawson-mail-2026']['confirmed'] is None and by['lawson-mail-2026']['reportedCount'] is None
med=next(d for d in added if 'メドレー' in d['org']);assert med['confirmed'] is None and med['potential'] is None and med['reportedCount'] is None
book=next(d for d in added if 'ブックオフコーポレーション' in d['org']);assert book['confirmed']==6427735 and book['unit']=='件'
gmo=next(d for d in added if 'GMOリサーチ' in d['org']);assert gmo['confirmed']==894082 and gmo['loss']==2869500
assert {'nikkei-workspace-2026','nikkei-m365-2026','nikkei-devcloud-2026'}<=set(by)
print('October source links, uncertainty, separate incidents, quantitative units and major corrections checked.')
