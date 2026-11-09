"""Clear one verified orphaned Pages deployment that blocked subsequent releases.
This does not delete or unpublish the live site and never targets an arbitrary deployment.
"""
import json,os,urllib.request,urllib.error,time
repo=os.environ['GITHUB_REPOSITORY'];assert repo=='nobby11334/incidentatlas'
old='ba8c5a91470eb7e1c3a060937980ec7cad618103'
base='https://api.github.com/repos/'+repo+'/pages/deployments/'+old
headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+os.environ['PAGES_RECOVERY_TOKEN'],'X-GitHub-Api-Version':'2022-11-28'}
active={'queued','deployment_in_progress','in_progress','pending','building','deploying'}
def status():
 try:
  with urllib.request.urlopen(urllib.request.Request(base+'/status',headers=headers),timeout=20) as r:return json.load(r).get('status','unknown')
 except urllib.error.HTTPError as e:
  if e.code==404:return 'not_found'
  raise
state=status();print('Known orphaned deployment state:',state,flush=True)
if state in active:
 with urllib.request.urlopen(urllib.request.Request(base+'/cancel',headers=headers,method='POST'),timeout=20) as r:assert r.status==204
 for _ in range(10):
  state=status()
  if state not in active:break
  time.sleep(3)
 assert state not in active,'Orphaned deployment cancellation still pending'
 print('Orphaned deployment cleared:',state,flush=True)
else:print('No active orphaned deployment to cancel.',flush=True)
