"""Download the exact public reports declared in import_jnsa.py; requires pdftotext."""
import ast,pathlib,os,subprocess,urllib.request
root=pathlib.Path(__file__).resolve().parent
module=ast.parse((root/'import_jnsa.py').read_text())
defs=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='definitions' for t in n.targets))
cache=pathlib.Path(os.environ.get('INCIDENT_SOURCE_CACHE',str(root.parent/'source-cache')));cache.mkdir(parents=True,exist_ok=True)
for year,filename,url,index,expected in defs:
 text=cache/filename;pdf=text.with_suffix('.pdf')
 if not pdf.exists():
  req=urllib.request.Request(url,headers={'User-Agent':'IncidentAtlas source verification'})
  with urllib.request.urlopen(req,timeout=90) as r:pdf.write_bytes(r.read())
 if not text.exists():subprocess.run(['pdftotext','-layout',str(pdf),str(text)],check=True)
 print(year,filename)
