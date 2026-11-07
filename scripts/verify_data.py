"""Validate ingestion invariants and source-verified cases, without substituting unknowns."""
import json,pathlib,collections
root=pathlib.Path(__file__).resolve().parents[1]/'dist'
h=json.loads((root/'historical.json').read_text());rows=h['rows'];c=json.loads((root/'coverage.json').read_text());named=json.loads((root/'data.json').read_text())
assert len(rows)>=15320
by={(r[0],r[1]):r for r in rows};assert len(by)==len(rows)
assert len({d['id'] for d in named})==len(named) and len(named)>=41
assert sum(not d['anonymous'] for d in named)>=40
for x in c['historical']:
 group=[r for r in rows if r[0]==x['year']]
 assert len(group)==x['rows']==x['expectedRows']
 assert all(r[2].startswith(str(x['year'])) for r in group)
for r in rows:
 assert len(r)==9 and r[3] and r[4] and r[5] and not r[5].isdigit()
 assert r[6] is None or isinstance(r[6],int) and r[6]>=0
 assert r[7] is None or isinstance(r[7],int) and r[7]>=0
 assert r[8]>=1
assert by[2002,1][6]==1900 and by[2002,1][7]==11400000 # source 千円
assert by[2003,15][6]==2 and by[2003,15][7]==4000
assert by[2005,82][6]==8 and by[2005,82][7]==264000 # discrepancy preserved
assert by[2006,497][6]==3996789
assert by[2007,36][6]==3832
assert (2014,1216) not in by
assert any(r[6] is None for r in rows)
print(json.dumps({'editorial':len(named),'anonymousAppendix':len(rows),'total':len(named)+len(rows),'modelAmounts':sum(r[7] is not None for r in rows),'sourceYears':len(c['historical'])}))
