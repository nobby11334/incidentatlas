'use strict';
let data=[],filtered=[],coverage=null,current=null,lastFocus=null,page=1,kind='all';
const $=id=>document.getElementById(id);
const esc=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'","&#39;");
const fmt=n=>n==null?'未収録':n.toLocaleString('ja-JP');
const money=n=>n==null?'本版未収録':n>=1e8?(n/1e8).toLocaleString('ja-JP',{maximumFractionDigits:2})+' 億円':fmt(n)+' 円';
const causes={'置き忘れ':'紛失','情報持ち出し':'持ち出し違反','内部犯罪':'内部不正','不正アクセス':'外部攻撃','ワーム・ウイルス':'マルウェア感染','内部犯罪・内部不正行為':'内部不正','不正な情報持ち出し':'持ち出し違反','誤操作':'操作ミス','設定ミス':'設定ミス','管理ミス':'管理ミス','紛失・置忘れ':'紛失','盗難':'盗難','バグ・セキュリティホール':'ソフトウェア不備','目的外使用':'目的外利用','その他':'その他','不明':'不明'};
const scale=d=>Math.max(d.confirmed??0,d.potential??0,d.reportedCount??0);
const eventDate=d=>d.date||d.published;
const selectedKind=(d,k)=>k==='all'||(k==='anonymous'?d.anonymous:!d.anonymous);
function severity(d){
 if(d.cia.includes('可用性')||d.loss>=1e9)return [4,'甚大',d.cia.includes('可用性')?'業務停止・可用性影響':'公表実額・会社見込額10億円以上'];
 const n=scale(d);
 if(n>=1e5||d.loss>=1e8)return [3,'大規模',d.confirmed>=1e5?'確認規模10万以上':d.reportedCount>=1e5?'調査資料の人数10万以上（実流出確認ではない）':'対象・可能性を含む規模10万以上'];
 if(n>=1000)return [2,'中規模','対象・調査規模1,000以上'];
 if(n>0)return [1,'限定','収録規模1,000未満'];
 return [0,'未判定','評価に必要な情報不足'];
}
function badge(d){const l=severity(d);return '<span class="badge level l'+l[0]+'">'+(l[0]?'L'+l[0]+' '+l[1]:l[1])+'</span>'}
function render(reset=false){
 if(reset===true)page=1;
 const q=$('q').value.trim().toLowerCase();
 filtered=data.filter(d=>selectedKind(d,kind)&&(!q||d.searchText.includes(q))&&(!$('type').value||d.type===$('type').value)&&(!$('sector').value||d.sector===$('sector').value)&&(!$('level').value||severity(d)[0]==$('level').value)&&(!$('year').value||($('basis').value==='event'?eventDate(d):d.published).startsWith($('year').value))&&(!$('cia').value||d.cia.includes($('cia').value))&&(!$('supplier').checked||d.scope.includes('委託'))&&(!$('status').value||({confirmed:d.confirmed!=null,potential:d.potential!=null,reported:d.reportedCount!=null,money:d.loss!=null,model:d.modelEstimate!=null}[$('status').value])));
 const sort=$('sort').value;
 filtered.sort((a,b)=>sort==='old'?eventDate(a).localeCompare(eventDate(b)):sort==='level'?severity(b)[0]-severity(a)[0]:sort==='number'?(b.confirmed??-1)-(a.confirmed??-1):sort==='money'?(b.loss??-1)-(a.loss??-1):sort==='model'?(b.modelEstimate??-1)-(a.modelEstimate??-1):sort==='scale'?scale(b)-scale(a):b.published.localeCompare(a.published));
 const size=Number($('pagesize').value),pages=Math.max(1,Math.ceil(filtered.length/size));page=Math.min(page,pages);
 const start=(page-1)*size,shown=filtered.slice(start,start+size);
 $('count').textContent=fmt(filtered.length)+' / '+fmt(data.length)+' レコード';
 $('empty').hidden=!!filtered.length;$('prev').disabled=page<=1;$('next').disabled=page>=pages;
 $('pageinfo').textContent=filtered.length?fmt(start+1)+'–'+fmt(start+shown.length)+' 件 / '+fmt(filtered.length)+' 件　'+page+' / '+pages+' ページ':'0 件';
 $('rows').innerHTML=shown.map(d=>{
 const n=d.confirmed??d.potential??d.reportedCount;
 const amount=d.loss!=null?money(d.loss):d.modelEstimate!=null?money(d.modelEstimate):'本版未収録';
 const amountLabel=d.loss!=null?d.lossKind:d.modelEstimate!=null?'JNSAモデル・実損ではない':'実額・推計とも未収録';
 return '<tr><td>'+badge(d)+'</td><td><button class="org" data-id="'+esc(d.id)+'">'+esc(d.org)+'</button><div class="title">'+esc(d.title)+'</div><time class="date">'+esc(d.published.replaceAll('-','.'))+' '+esc(d.publicationKind||'公表')+(d.anonymous?' · 匿名個票':'')+'</time></td><td><span class="badge">'+esc(d.type)+'</span><span class="sub">'+esc(d.method)+'</span></td><td><div class="number">'+(n!=null?fmt(n)+' '+esc(d.unit):'—')+'</div><span class="sub">'+esc(d.status)+(d.confirmed!=null&&d.potential!=null?'<br>おそれ '+fmt(d.potential)+' '+esc(d.unit):'')+'</span></td><td><div class="'+(d.loss!=null||d.modelEstimate!=null?'number':'sub')+'">'+amount+'</div><span class="sub '+(d.modelEstimate!=null?'modeltag':'')+'">'+esc(amountLabel)+'</span></td><td><button class="cellbtn" data-id="'+esc(d.id)+'" aria-label="'+esc(d.org)+'の詳細">↗</button></td></tr>';
 }).join('');
 document.querySelectorAll('[data-id]').forEach(b=>b.onclick=()=>openDetail(data.find(d=>d.id===b.dataset.id),b));
 $('csv').textContent='↓ 条件に合う全'+fmt(filtered.length)+'件をCSV出力';
}
function showModal(d,focus){lastFocus=focus;d.showModal()}
function openDetail(d,b){
 current=d;const l=severity(d);
 const countLabel=d.reportedCount!=null?'調査資料の被害人数（確認状況は未分離）':'可能性・対象規模（確認済みと合算不可）';
 const v=d.reportedCount??d.potential;
 $('detailcontent').innerHTML='<div class="eyebrow">INCIDENT RECORD / '+esc(d.id.toUpperCase())+'</div><h2>'+esc(d.org)+'</h2><p>'+esc(d.title)+'</p>'+badge(d)+' <span class="badge">'+esc(d.type)+'</span> <span class="badge">'+esc(d.scope)+'</span>'+(d.anonymous?'<div class="notice">組織名が原資料にない匿名個票です。実名事案との重複は未排除です。</div>':'')+'<div class="detailgrid"><div><small>確認済み漏えい</small><b>'+fmt(d.confirmed)+(d.confirmed!=null?' '+esc(d.unit):'')+'</b></div><div><small>'+countLabel+'</small><b>'+fmt(v)+(v!=null?' '+esc(d.unit):'')+'</b></div><div><small>'+esc(d.dateLabel||'発生・認知・公開開始日')+'</small><b>'+esc(d.date||'未特定')+'</b></div><div><small>'+esc(d.publicationKind||'初回公表日')+'</small><b>'+esc(d.published)+'</b></div></div><h3>手口・侵入経路</h3><p>'+esc(d.method)+' ／ '+esc(d.entry)+'</p><h3>情報の種類と業務影響</h3><p>'+esc(d.data)+'<br>'+esc(d.impact)+'</p><h3>実額・会社の費用見込額</h3><p><b>'+money(d.loss)+(d.loss!=null?'（'+esc(d.lossKind)+'）':'')+'</b><br>'+esc(d.lossNote||'本版では金額未収録。非公表またはゼロと断定するものではありません。')+'</p>'+(d.modelEstimate!=null?'<div class="modelbox"><h3>原資料のJNSAモデルによる想定損害賠償額</h3><strong>'+money(d.modelEstimate)+'</strong><p>JNSAが当時のモデルで試算した値です。実損・支払額・裁判の認容額ではありません。現在のリスク評価にはそのまま適用できません。</p></div>':'')+'<h3>暫定レベルの根拠</h3><p>'+esc(l[2])+'。影響の軸：'+esc(d.cia.join('・'))+'。当サイトの独自分類。モデル推計額はレベル判定に使いません。</p><div class="notice">'+esc(d.note)+'</div><h3>出典・収録根拠</h3><div class="sources">'+d.sources.map(s=>'<a href="'+esc(s[1])+'" target="_blank" rel="noopener noreferrer">'+esc(s[0])+' ↗</a>').join('')+'</div><div class="detailfoot">情報時点：'+esc(d.asof)+' ／ 資料確認：2026-11-07'+(d.sourceRow?'<br>原資料：No.'+d.sourceRow+' ／ PDF p.'+d.sourcePage:'')+'<br>公表資料時点の調査範囲・推計の限界があります。</div><p><button class="outline" id="usecalc">この事案の件数を試算に使う →</button> <button class="outline" id="copylink">詳細リンクを表示</button></p><p id="linktext"></p>';
 showModal($('detail'),b);
 $('usecalc').onclick=()=>{$('detail').close();switchView('calc');$('n').value=d.confirmed??d.potential??d.reportedCount??0;calculate();$('n').focus()};
 $('copylink').onclick=()=>{$('linktext').textContent=location.origin+location.pathname+'#incident='+encodeURIComponent(d.id)};
}
function switchView(v){
 for(const name of ['list','analysis','calc','coverage'])$(name+'view').hidden=name!==v;
 document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===v));
 if(v==='analysis')drawCharts();
}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>switchView(b.dataset.view));
document.querySelectorAll('[data-kind]').forEach(b=>b.onclick=()=>{kind=b.dataset.kind;document.querySelectorAll('[data-kind]').forEach(x=>x.classList.toggle('selected',x===b));render(true)});
for(const id of ['q','type','sector','level','year','basis','cia','supplier','status','sort','pagesize'])$(id).addEventListener(id==='q'?'input':'change',()=>render(true));
$('prev').onclick=()=>{page--;render()};$('next').onclick=()=>{page++;render()};
$('more').onclick=()=>{$('extra').hidden=!$('extra').hidden;$('more').textContent=$('extra').hidden?'詳細条件 ＋':'詳細条件 −'};
$('reset').onclick=()=>{for(const id of ['q','type','sector','level','year','cia','status'])$(id).value='';$('supplier').checked=false;$('sort').value='new';$('basis').value='published';kind='all';document.querySelectorAll('[data-kind]').forEach(x=>x.classList.toggle('selected',x.dataset.kind==='all'));render(true)};
$('about').onclick=()=>showModal($('method'),$('about'));
document.querySelectorAll('dialog').forEach(d=>{
 d.querySelector('.close').onclick=()=>d.close();
 d.onclick=e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close()}};
 d.addEventListener('close',()=>lastFocus?.focus());
});
function calculate(){
 const v=id=>Math.max(0,Number($(id).value)||0);
 const a=v('n')*v('unitcost'),b=v('fixed'),c=v('days')*v('daily'),d=v('other'),e=v('recovery');
 $('estimate').textContent=money(Math.max(0,a+b+c+d-e));
 $('formula').textContent='対応費 '+money(a)+' ＋ 固定費 '+money(b)+' ＋ 事業影響 '+money(c)+' ＋ その他 '+money(d)+' − 回収 '+money(e);
}
for(const id of ['n','unitcost','fixed','days','daily','other','recovery'])$(id).oninput=calculate;
$('csv').onclick=()=>{
 const fields=['id','org','title','anonymous','published','publicationKind','date','dateLabel','asof','sector','type','originalCause','method','entry','scope','cia','confirmed','potential','reportedCount','unit','status','loss','lossKind','lossNote','modelEstimate','sourceRow','sourcePage','note','sources'];
 const escape=v=>{let s=String(v??'');if(/^[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"'};
 const csv='\ufeff'+fields.join(',')+'\r\n'+filtered.map(d=>fields.map(k=>escape(k==='sources'?d.sources.map(s=>s.join(': ')).join(' | '):Array.isArray(d[k])?d[k].join(' / '):d[k])).join(',')).join('\r\n');
 const a=document.createElement('a'),url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8;'}));a.href=url;a.download='incident-atlas-20261107.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
function bars(id,values,total){
 $(id).innerHTML=Object.entries(values).sort((a,b)=>b[1]-a[1]).map(([k,v])=>'<div class="barrow">'+esc(k)+'<span>'+fmt(v)+' 件</span><div class="bar"><i style="width:'+v/Math.max(total,1)*100+'%"></i></div></div>').join('');
}
function drawCharts(){
 const rows=data.filter(d=>selectedKind(d,$('analysiskind').value));
 bars('bars',rows.reduce((a,d)=>(a[d.type]=(a[d.type]||0)+1,a),{}),rows.length);
 bars('ciabars',rows.reduce((a,d)=>(d.cia.forEach(x=>a[x]=(a[x]||0)+1),a),{}),rows.length);
 drawYearChart(rows);
}
$('analysiskind').onchange=drawCharts;

function drawYearChart(rows){
 const basis=$('yearbasis').value,event=basis==='event',to=Math.max(2026,...data.map(d=>Number(d.published.slice(0,4)))),all=$('yearrange').value==='all';
 const dates=rows.flatMap(d=>event?(d.date&&!/認知|検知|和解|講演|可能性|判決/.test(d.dateLabel||'')?[d.date]:[]):[d.published]).filter(Boolean).map(s=>Number(s.slice(0,4)));
 const from=all?Math.min(2002,...dates):2002;
 const result=YearlyEvidence.aggregate(rows,{basis,from,to}),series=result.series;
 const maximum=Math.max(1,...series.map(x=>x.total)),step=maximum<=5?1:Math.pow(10,Math.floor(Math.log10(maximum)))/2,top=Math.ceil(maximum/step)*step;
 const width=Math.max(850,series.length*34+80),height=340,left=62,right=18,plot=width-left-right,bottom=260,plotHeight=220,slot=plot/series.length,barWidth=Math.max(5,slot*.62);
 const ticks=[...new Set(Array.from({length:5},(_,i)=>Math.round(top*i/4)))];
 let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+width+' '+height+'" style="min-width:'+width+'px" role="img" aria-labelledby="annualtitle annualdesc"><title id="annualtitle">'+(event?'発生年が判明している事案':'調査・公表年別の収録事案')+'の件数</title><desc id="annualdesc">'+from+'年から'+to+'年、合計'+fmt(result.total)+'レコード。実名と匿名の重複は未排除。正確な値は下の年別表に掲載。</desc>';
 ticks.forEach(n=>{const y=bottom-n/top*plotHeight;svg+='<line x1="'+left+'" x2="'+(width-right)+'" y1="'+y+'" y2="'+y+'" stroke="#dde3df"/><text x="'+(left-10)+'" y="'+(y+4)+'" text-anchor="end" fill="#65757c" font-size="11">'+fmt(Math.round(n))+'</text>'});
 series.forEach((d,i)=>{
  const x=left+i*slot+(slot-barWidth)/2,nh=d.named/top*plotHeight,ah=d.anonymous/top*plotHeight;
  const full=!event&&coverage.historical.some(c=>c.year===d.year),status=event?(d.total?'発生日判明分':'該当データなし'):full?'JNSA資料内の全行を収録（国内全事故の網羅ではない）':d.total?'個別事案のみ・収録不足':'未収録';
  svg+='<g><title>'+d.year+'年：'+fmt(d.total)+'レコード（実名 '+fmt(d.named)+'、匿名 '+fmt(d.anonymous)+'）。'+status+'</title><rect x="'+x+'" y="'+(bottom-ah)+'" width="'+barWidth+'" height="'+ah+'" fill="#43765e"/><rect x="'+x+'" y="'+(bottom-ah-nh)+'" width="'+barWidth+'" height="'+nh+'" fill="#b08b47"/>';
  if(!d.total)svg+='<text x="'+(x+barWidth/2)+'" y="'+(bottom-8)+'" text-anchor="middle" fill="#9aa59e" font-size="10">—</text>';
  if(series.length<=30||i%2===0||i===series.length-1)svg+='<text transform="translate('+(x+barWidth/2)+','+(bottom+16)+') rotate(-45)" text-anchor="end" fill="#52676c" font-size="11">'+d.year+'</text>';
  svg+='<rect x="'+x+'" y="318" width="'+barWidth+'" height="4" fill="'+(full?'#43765e':d.total?'#b08b47':'#d9dfda')+'"/><rect x="'+(left+i*slot)+'" y="35" width="'+slot+'" height="290" fill="transparent"/></g>';
 });
 svg+='</svg>';$('yearchart').innerHTML=svg;
 $('yearnote').textContent=(event?'発生日・不正アクセス開始日が記録された事案を集計。認知日・検知日・和解日・可能性の日付だけの事案は除外しています。':'匿名個票は調査対象年、実名事案は公表・資料年で集計。発生年の統計ではありません。')+' 表示期間：'+from+'～'+to+'年、'+fmt(result.total)+'レコード。'+(result.unknown?'日付未特定・基準不適合 '+fmt(result.unknown)+'件を除外。':'')+(result.outside?'期間外 '+fmt(result.outside)+'件を除外。':'');
 $('yearsummary').innerHTML='<div class="tablewrap"><table class="annualtable"><thead><tr><th>年</th><th>実名</th><th>匿名・歴史</th><th>計</th><th>収録状況</th></tr></thead><tbody>'+series.map(d=>'<tr><td>'+d.year+'</td><td>'+fmt(d.named)+'</td><td>'+fmt(d.anonymous)+'</td><td>'+fmt(d.total)+'</td><td>'+(event?(d.total?'発生日判明分':'該当データなし'):coverage.historical.some(c=>c.year===d.year)?'JNSA資料内の全行を照合':d.total?'個別収録のみ':'未収録')+'</td></tr>').join('')+'</tbody></table></div>';
}
$('yearbasis').onchange=drawCharts;$('yearrange').onchange=drawCharts;

function hydrate(row){
 const [year,no,published,sector,cause,route,reportedCount,modelEstimate,sourcePage]=row,source=coverage.historical.find(x=>x.year===year);
 return {id:'jnsa-'+year+'-'+String(no).padStart(4,'0'),org:'組織名非掲載 / '+sector,title:(causes[cause]||cause)+'・'+route,date:null,published,publicationKind:source.datePrecision==='year'?'調査対象年（公表日未特定）':'資料記載日',asof:String(year),sector,type:causes[cause]||'不明',method:cause,entry:route,scope:'不明',cia:['機密性'],confirmed:null,potential:null,reportedCount,unit:'人',status:'調査人数・確認状況未分離',data:'情報項目は本版未抽出',impact:'原資料の個票。被害人数には紛失・可能性等を含む場合があります。',note:'原資料は組織名を掲載していません。実名事案との照合・重複排除は未完了。被害人数を実流出確認人数に読み替えないでください。'+(source.countDiscrepancies?.some(x=>x.row===no)?' 原資料の表Aと表Bの人数に不一致があるため人数は表Aを採用。推計額は表Bの原表記です。':'' ),anonymous:true,recordKind:'調査個票',originalCause:cause,route,sourceRow:no,sourcePage,modelEstimate,sources:[['JNSA '+year+'年調査報告書・個票No.'+no+'（PDF p.'+sourcePage+'）',source.source]]};
}
async function initialize(){
 const get=async u=>{const r=await fetch(u);if(!r.ok)throw new Error(u);return r.json()};
 try{
 const [named,historical,cov]=await Promise.all([get('data.json'),get('historical.json'),get('coverage.json')]);coverage=cov;
 data=[...named,...historical.rows.map(hydrate)];
 data.forEach(d=>{d.searchText=[d.id,d.org,d.title,d.sector,d.type,d.method,d.entry,d.data,d.note].join(' ').toLowerCase()});
 $('navtotal').textContent=fmt(data.length);$('total').textContent=fmt(data.length);
 const n=data.filter(d=>!d.anonymous).length,anon=data.length-n;
 $('kindcounts').innerHTML=n+' <em>/</em> '+fmt(anon);
 $('yearcounts').innerHTML=coverage.historical.length+'<span>年分</span>';
 $('moneycounts').innerHTML=data.filter(d=>d.loss!=null).length+' <em>/</em> '+fmt(data.filter(d=>d.modelEstimate!=null).length);
 for(const [id,key] of [['type','type'],['sector','sector'],['year','published']]){
 const vals=id==='year'?[...new Set(data.flatMap(x=>[x.published.slice(0,4),(x.date||x.published).slice(0,4)]))]:[...new Set(data.map(x=>x[key]))];
 vals.sort((a,b)=>id==='year'?b.localeCompare(a):a.localeCompare(b,'ja')).forEach(v=>{let o=document.createElement('option');o.value=v;o.textContent=v;$(id).append(o)});
 }
 $('coveragebody').innerHTML=coverage.historical.sort((a,b)=>a.year-b.year).map(d=>'<tr><td>'+d.year+'年</td><td>'+fmt(d.rows)+'</td><td>'+(d.continuous?'1～'+d.maxRow+'を照合':'1～'+d.maxRow+'（原資料の1216は欠番）')+'</td><td><a href="'+esc(d.source)+'" target="_blank" rel="noopener noreferrer">報告書掲載ページ ↗</a></td></tr>').join('');
 render();calculate();
 if(location.hash==='#analysis')switchView('analysis');
 const match=location.hash.match(/^#incident=(.+)$/);
 if(match){const d=data.find(x=>x.id===decodeURIComponent(match[1]));if(d)openDetail(d,null)}
 }catch(e){$('empty').hidden=false;$('empty').textContent='データの読み込みに失敗しました。再読み込みしてください。';$('count').textContent='読み込みエラー'}
}
initialize();
