"""Apply individually reviewed changes once, preserving any later dated editorial changes."""
import json,pathlib
R=pathlib.Path(__file__).resolve().parents[1];p=R/'dist/data.json';data=json.loads(p.read_text());byid={r['id']:r for r in data}
for update in json.loads((R/'sources/reviewed-updates.json').read_text()):
 old=byid.get(update['id'])
 if old is None:data.append(update);byid[update['id']]=update
 elif (old.get('checked') or '')<update['checked']:
  old.update(update)
p.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
