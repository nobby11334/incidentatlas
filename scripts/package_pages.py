"""Create a version-consistent static release using content-addressed assets."""
import pathlib,json,re,hashlib,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];SOURCE=ROOT/'dist';OUT=ROOT/'_site'
def digest(b):return hashlib.sha256(b).hexdigest()
if OUT.exists():shutil.rmtree(OUT)
shutil.copytree(SOURCE,OUT)
files=sorted(p for p in SOURCE.iterdir() if p.suffix in ['.js','.css','.json'] and p.name!='deployment.json')
assets={}
for p in files:
 name=p.stem+'.'+digest(p.read_bytes())[:20]+p.suffix
 (OUT/name).write_bytes(p.read_bytes());assets[p.name]=name
bootstrap=('globalThis.IncidentAtlasAssets=Object.freeze('+json.dumps(assets,separators=(',',':'))+');\n').encode()
bootname='assets.'+digest(bootstrap)[:20]+'.js';(OUT/bootname).write_bytes(bootstrap)
html=(SOURCE/'index.html').read_text()
html=re.sub(r'((?:src|href)=["\'])([^"\']+)(["\'])',lambda m:m[1]+assets.get(m[2],m[2])+m[3],html)
html=html.replace('<script ', '<script src="'+bootname+'"></script><script ',1)
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
manifest=json.loads((SOURCE/'deployment.json').read_text()) if (SOURCE/'deployment.json').exists() else {'sourceCommit':commit,'sha256':{n:digest((SOURCE/n).read_bytes()) for n in ['data.json','historical.json','source-manifest.json','review.js','app.js']}}
manifest['assets']=assets;manifest['bootstrap']=bootname;manifest['indexSha256']=digest(html.encode())
html=html.replace('</head>','<meta name="incident-atlas-release" content="'+manifest['sourceCommit']+'"></head>')
manifest['indexSha256']=digest(html.encode());(OUT/'index.html').write_text(html)
(OUT/'deployment.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')))
assert all((OUT/n).exists() for n in assets.values())
print('Version-consistent Pages release:',manifest['sourceCommit'],len(assets),'content-addressed assets')
