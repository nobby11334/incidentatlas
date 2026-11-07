import urllib.request, urllib.parse, re, json, concurrent.futures, pathlib, subprocess
root=pathlib.Path('/workspace/scratch/5c7937cdc521/jnsa');root.mkdir(exist_ok=True)
def fetch(u):return urllib.request.urlopen(u,timeout=45).read()
def page(y):
 u=f'https://www.jnsa.org/result/incident/{y}.html'
 try:
  b=fetch(u);s=b.decode('shift_jis',errors='replace');(root/f'{y}.html').write_text(s)
  links=[urllib.parse.urljoin(u,x) for x in re.findall(r'href=["\x27]([^"\x27]+)',s) if '.pdf' in x.lower()]
  return {'year':y,'index':u,'pdfs':list(dict.fromkeys(links))}
 except Exception as e:return {'year':y,'index':u,'error':str(e)}
res=list(concurrent.futures.ThreadPoolExecutor(4).map(page,range(2007,2019)))
(root/'discovery.json').write_text(json.dumps(res,ensure_ascii=False,indent=2))
print(json.dumps(res,ensure_ascii=False,indent=2))
