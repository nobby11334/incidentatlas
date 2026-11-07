"""Conservative publication URL identity, independent of article title or incident date."""
import re,urllib.parse,unicodedata
def orgkey(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).casefold()
def urlkey(u):
 p=urllib.parse.urlsplit(u);host=(p.hostname or '').removeprefix('www.').lower();path=urllib.parse.unquote(p.path).rstrip('/')
 path=re.sub(r'/index\.html?$','',path,flags=re.I)
 if host=='support.goodsmile.com':path=re.sub(r'(/hc/[^/]+/articles/\d+).*',r'\1',path)
 if host=='coconala.com':path=path.replace('/smartphone/news/','/news/')
 query=sorted((k,v) for k,v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith(('utm_','fbclid','gclid','_gl','_ga','yclid')))
 return host+path+('?' +urllib.parse.urlencode(query) if query else '')
