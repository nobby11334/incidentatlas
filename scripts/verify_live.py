"""Verify public Pages content from the deployment runner after CDN propagation."""
import sys,os,pathlib,urllib.request,urllib.parse,json,hashlib,time
base,commit=sys.argv[1:3]
assert base=='https://nobby11334.github.io/incidentatlas/',base
root=pathlib.Path(__file__).resolve().parents[1]/'dist'
files=['data.json','historical.json','source-manifest.json','review.js','app.js']
def get(name):
 url=urllib.parse.urljoin(base,name)+'?source='+urllib.parse.quote(commit,safe='')
 req=urllib.request.Request(url,headers={'Cache-Control':'no-cache','User-Agent':'IncidentAtlas-deployment-verification'})
 with urllib.request.urlopen(req,timeout=20) as r:
  assert r.status==200,(name,r.status)
  return r.read()
for attempt in range(6):
 try:
  manifest=json.loads(get('deployment.json'))
  assert manifest['sourceCommit']==commit,'CDN still serves an earlier commit'
  for name in files:
   expected=hashlib.sha256((root/name).read_bytes()).hexdigest()
   assert manifest['sha256'][name]==expected,(name,'manifest differs from checked-out source')
   assert hashlib.sha256(get(name)).hexdigest()==expected,(name,'public bytes differ from source')
  assert '継続更新中のβ版' in get('').decode('utf-8')
  print('Public GitHub Pages HTTP 200, source commit and all five data/JS hashes verified:',commit)
  break
 except Exception as e:
  if attempt==5:raise
  print('Waiting for Pages propagation:',type(e).__name__,str(e),flush=True)
  time.sleep(10)
