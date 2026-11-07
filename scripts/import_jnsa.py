"""Extract factual fields from public JNSA appendices, keeping anonymity and provenance.
The input directory may be supplied as INCIDENT_SOURCE_CACHE.
"""
import re,json,pathlib,hashlib,datetime,os
base=pathlib.Path(os.environ.get('INCIDENT_SOURCE_CACHE','/workspace/scratch/5c7937cdc521/jnsa'))
out=pathlib.Path(__file__).resolve().parents[1]/'dist'
definitions=[
(2002,'2003.txt','https://www.jnsa.org/result/incident/2004/2004-002.pdf','https://www.jnsa.org/active/2003/active2003_1a.html',62),
(2003,'2003.txt','https://www.jnsa.org/result/incident/2004/2004-002.pdf','https://www.jnsa.org/active/2003/active2003_1a.html',57),
(2004,'2004-0.txt','https://www.jnsa.org/result/incident/2005/2005-004.pdf','https://www.jnsa.org/active/2004/active2004_1a.html',366),
(2005,'2005-0.txt','https://www.jnsa.org/result/incident/2006/2006-002.pdf','https://www.jnsa.org/result/2005/20060803_pol01/',1032),
(2006,'2006-0.txt','https://www.jnsa.org/result/incident/2008/2008-031.pdf','https://www.jnsa.org/result/2006/pol/insident/070720/',993),
(2007,'2007-0.txt','https://www.jnsa.org/result/incident/2009/2009-018.pdf','https://www.jnsa.org/result/2007/pol/incident/index.html',864),
(2008,'2008-0.txt','https://www.jnsa.org/result/incident/2009/2009-001.pdf','https://www.jnsa.org/result/2008/surv/incident/index.html',1373),
(2009,'2009-final.txt','https://www.jnsa.org/result/incident/data/2009incident_survey_v1.1.pdf','https://www.jnsa.org/result/incident/2009.html',1539),
(2010,'2010-1.txt','https://www.jnsa.org/result/incident/2011/2011-003.pdf','https://www.jnsa.org/result/incident/2010.html',1679),
(2011,'2011-1.txt','https://www.jnsa.org/result/incident/2012/2012-005.pdf','https://www.jnsa.org/result/incident/2011.html',1551),
(2012,'2012-1.txt','https://www.jnsa.org/result/incident/2014/2014-007.pdf','https://www.jnsa.org/result/incident/2012.html',2357),
(2013,'2013-1.txt','https://www.jnsa.org/result/incident/2014/2014-004.pdf','https://www.jnsa.org/result/incident/2013.html',1388),
(2014,'2014-1.txt','https://www.jnsa.org/result/incident/2016/2016-027.pdf','https://www.jnsa.org/result/incident/2014.html',1591),
(2016,'2016-2.txt','https://www.jnsa.org/result/incident/2017/2017-006.pdf','https://www.jnsa.org/result/incident/2016.html',468)]
causes=['置き忘れ','情報持ち出し','内部犯罪','内部犯罪・内部不正行為','不正な情報持ち出し','バグ・セキュリティホール','ワーム・ウイルス','紛失・置忘れ','不正アクセス','設定ミス','誤操作','管理ミス','目的外使用','盗難','その他','不明']
ap=re.compile(r'^(.*?)\s+('+'|'.join(map(re.escape,sorted(causes,key=len,reverse=True)))+r')\s*(.+?)\s+(不明|[0-9][0-9,]*)人?(?=\s|$)')
# Visually checked wrapped cells in the 2006 appendix A; values remain source facts.
wrapped2006={58:('公務(他に分類されないもの)','FD等可搬記録媒体',2000),107:('金融・保険業','紙媒体経由',1251),145:('公務(他に分類されないもの)','紙媒体経由',527),282:('情報通信業','紙媒体経由',408),431:('金融・保険業','紙媒体経由',1),464:('公務(他に分類されないもの)','その他',42),485:('金融・保険業','その他',None),497:('情報通信業','FD等可搬記録媒体',3996789),518:('医療・福祉','紙媒体経由',5),537:('サービス業(他に分類されないもの)','その他',1),538:('情報通信業','その他',14),555:('医療・福祉','その他',1),567:('医療・福祉','Email経由',3),571:('不動産業','その他',1),608:('教育・学習支援業','紙媒体経由',10),740:('情報通信業','FD等可搬記録媒体',4000000),767:('公務(他に分類されないもの)','紙媒体経由',None),922:('情報通信業','Web･Net経由',5)}
rows=[];coverage=[]
for y,file,url,index,expected in definitions:
 p=base/file;text=p.read_text();table=None;a={};b={};bcounts={};page=1
 for line in text.splitlines(keepends=True):
  # splitlines splits form feeds as separate lines
  if '\f' in line:page+=1
  if re.search(r'表\s*[AＡ]\s*'+str(y),line) or re.search(str(y)+r'\s*年.*（表Ａ）',line):table='A'
  if re.search(r'表\s*[BＢ]\s*'+str(y),line) or re.search(str(y)+r'\s*年.*（表Ｂ）',line):table='B'
  if y<=2003:
   if re.search(r'表\s*4-1[：:]\s*2003',line):table='A' if y==2003 else None
   if re.search(r'表\s*4-4[：:]\s*2003',line):table='B' if y==2003 else None
   if re.search(r'表\s*5-7[：:]',line):table='A' if y==2002 else None
   if re.search(r'表\s*5-8[：:]\s*2002',line):table='B' if y==2002 else None
  if y<=2003 and re.match(r'^\s*合計',line):table=None
  if table not in ['A','B']:continue
  if y<=2005:
   m=re.match(r'^\s*(\d+)\s+(.+)',line)
   if not m:continue
   no=int(m[1]);date=str(y);rest=m[2]
  else:
   m=re.match(r'^\s*(\d+)\s+('+str(y)+r'/\d{1,2}/\d{1,2})\s+(.+)',line)
   if not m:continue
   no=int(m[1]);date=datetime.datetime.strptime(m[2],'%Y/%m/%d').date().isoformat();rest=m[3]
  if table=='A':
   if y==2006 and no in [991,992]:rest=rest.replace('もの)盗難','もの) 盗難')
   if y==2006 and no in wrapped2006:
    industry,route,n=wrapped2006[no];a[no]=(date,industry,'内部犯罪・内部不正行為',route,n,page);continue
   z=ap.match(rest)
   if not z:
    if y==2007 and no==36:
     a[no]=(date,'公務(他に分類されないもの)','管理ミス','USB 等可搬記録媒体',3832,page)
    continue
   industry,cause,route,n=z.groups()
   if no in a:raise ValueError((y,no,'duplicate A row'))
   a[no]=(date,industry,cause,route,None if n=='不明' else int(n.replace(',','')),page)
  else:
   # B rows contain only industry and numeric/model fields.
   cols=rest.replace('千円','').replace('人','').split()
   if y<=2004:cols=cols[:-1] # final repeated No. column
   if len(cols)<10 or re.fullmatch(r'[0-9,.]+',cols[0]):continue
   try:
    amount=None if cols[-1]=='不明' else round(float(cols[-1].replace(',',''))*(1000 if y<=2003 else 10000))
    if not all(re.fullmatch(r'[0-9,.]+|不明',v) for v in cols[-9:]):continue
    count=None if cols[-9]=='不明' else int(cols[-9].replace(',',''))
    if no in b and b[no]!=amount:raise ValueError((y,no,'duplicate B amounts'))
    
    b[no]=amount;bcounts[no]=count
   except ValueError:continue
 if len(a)!=expected:raise ValueError((y,'A count',len(a),'expected',expected,'missing',sorted(set(range(1,expected+1))-set(a))[:50]))
 discrepancies=[dict(row=no,tableA=a[no][4],tableB=n) for no,n in bcounts.items() if no in a and a[no][4]!=n]
 if discrepancies:print(y,'A/B discrepancies',discrepancies)
 missing=sorted(set(range(1,max(a)+1))-set(a))
 if missing and not(y==2014 and missing==[1216]):raise ValueError((y,'ordinal gaps',missing))
 if any(d[3].isdigit() for d in a.values()):raise ValueError('Invalid numeric route')
 for no,(date,industry,cause,route,n,page) in sorted(a.items()):
  rows.append([y,no,date,industry,cause,route,n,b.get(no),page])
 coverage.append(dict(year=y,rows=len(a),expectedRows=expected,maxRow=max(a),continuous=not missing,sourceOrdinalGaps=missing,countDiscrepancies=discrepancies,estimateRows=sum(v is not None for v in b.values()),source=index,downloadUrl=url,inputFile=file,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),datePrecision='year' if y<=2005 else 'day'))
compact={'columns':['year','row','published','sector','originalCause','route','reportedCount','modelEstimate','sourcePage'],'rows':rows}
(out/'historical.json').write_text(json.dumps(compact,ensure_ascii=False,separators=(',',':')))
(out/'coverage.json').write_text(json.dumps({'checked':'2026-11-07','historical':coverage,'copyright':'出典：特定非営利活動法人 日本ネットワークセキュリティ協会（JNSA）。公開報告書の事実項目を抽出・再分類。組織名は推定していません。'},ensure_ascii=False,indent=2))
print(json.dumps({'count':len(rows),'years':[(d['year'],d['rows'],d['estimateRows']) for d in coverage]},ensure_ascii=False))
