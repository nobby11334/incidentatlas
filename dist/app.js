'use strict';
let data=[],filtered=[],coverage=null,current=null,lastFocus=null,page=1,kind='all',review='all';
const ASSET_URLS=globalThis.IncidentAtlasAssets||{};
const $=id=>document.getElementById(id);
const esc=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'","&#39;");
const fmt=n=>n==null?'未収録':n.toLocaleString('ja-JP');
const money=n=>n==null?'本版未収録':n>=1e8?(n/1e8).toLocaleString('ja-JP',{maximumFractionDigits:2})+' 億円':fmt(n)+' 円';
const causes={'置き忘れ':'紛失','情報持ち出し':'持ち出し違反','内部犯罪':'内部不正','不正アクセス':'外部攻撃','ワーム・ウイルス':'マルウェア感染','内部犯罪・内部不正行為':'内部不正','不正な情報持ち出し':'持ち出し違反','誤操作':'操作ミス','設定ミス':'設定ミス','管理ミス':'管理ミス','紛失・置忘れ':'紛失','盗難':'盗難','バグ・セキュリティホール':'ソフトウェア不備','目的外使用':'目的外利用','その他':'その他','不明':'不明'};
const scale=d=>Math.max(d.confirmed??0,d.potential??0,d.reportedCount??0);
const eventDate=d=>ReviewEvidence.occurrence(d);
const periodDate=d=>$('basis').value==='event'?eventDate(d):d.published;
const selectedKind=(d,k)=>k==='all'||(k==='anonymous'?d.anonymous:!d.anonymous);
function severity(d){
 if(ReviewEvidence.needsReview(d))return [0,'精査前','確認が不足しているためレベルを付与していません'];
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
 filtered=data.filter(d=>ReviewEvidence.matches(d,review)&&selectedKind(d,kind)&&(!q||d.searchText.includes(q))&&(!$('type').value||($('type').value==='未確認'?ReviewEvidence.needsReview(d):!ReviewEvidence.needsReview(d)&&d.type===$('type').value))&&(!$('sector').value||d.sector===$('sector').value)&&(!$('level').value||severity(d)[0]==$('level').value)&&(!$('year').value||periodDate(d).startsWith($('year').value))&&(!$('month').value||periodDate(d).startsWith($('month').value))&&(!$('cia').value||(!ReviewEvidence.needsReview(d)&&d.cia.includes($('cia').value)))&&(!$('supplier').checked||d.scope.includes('委託'))&&(!$('status').value||({confirmed:d.confirmed!=null,potential:d.potential!=null,reported:d.reportedCount!=null,money:d.loss!=null,model:d.modelEstimate!=null,discovery:ReviewEvidence.quality(d)==='discovery',mechanical:ReviewEvidence.quality(d)==='mechanical',curated:ReviewEvidence.quality(d)==='curated'}[$('status').value])));
 const sort=$('sort').value;
 filtered.sort((a,b)=>sort==='old'?eventDate(a).localeCompare(eventDate(b)):sort==='level'?severity(b)[0]-severity(a)[0]:sort==='number'?(b.confirmed??-1)-(a.confirmed??-1):sort==='money'?(b.loss??-1)-(a.loss??-1):sort==='model'?(b.modelEstimate??-1)-(a.modelEstimate??-1):sort==='scale'?scale(b)-scale(a):b.published.localeCompare(a.published));
 const size=Number($('pagesize').value),pages=Math.max(1,Math.ceil(filtered.length/size));page=Math.min(page,pages);
 const start=(page-1)*size,shown=filtered.slice(start,start+size);
 $('count').textContent=fmt(filtered.length)+' / '+fmt(data.length)+' レコード';
 $('empty').hidden=!!filtered.length;$('prev').disabled=page<=1;$('next').disabled=page>=pages;
 $('pageinfo').textContent=filtered.length?fmt(start+1)+'–'+fmt(start+shown.length)+' 件 / '+fmt(filtered.length)+' 件　'+page+' / '+pages+' ページ':'0 件';
 $('rows').innerHTML=shown.map(d=>{
 const preliminary=ReviewEvidence.needsReview(d);
 const n=preliminary?null:d.confirmed??d.potential??d.reportedCount;
 const amount=d.loss!=null?money(d.loss):d.modelEstimate!=null?money(d.modelEstimate):'本版未収録';
 const amountLabel=d.loss!=null?d.lossKind:d.modelEstimate!=null?'JNSAモデル・実損ではない':'実額・推計とも未収録';
 return '<tr><td>'+badge(d)+'</td><td><button class="org" data-id="'+esc(d.id)+'">'+esc(d.org)+'</button><div class="reviewbadges">'+reviewBadges(d)+'</div><div class="title">'+esc(d.title)+'</div><time class="date">'+esc(d.published?d.published.replaceAll('-','.'):'日付未特定')+' '+esc(d.publicationKind||'公表')+(d.anonymous?' · 匿名個票':'')+'</time></td><td><span class="badge">'+esc(preliminary?'分類は精査前':d.type)+'</span><span class="sub">'+esc(preliminary?'原資料で確認してください':d.method)+'</span></td><td><div class="number">'+(n!=null?fmt(n)+' '+esc(d.unit):'—')+'</div><span class="sub">'+esc(preliminary?'数量の意味・被害有無は未精査':d.status)+(d.confirmed!=null&&d.potential!=null?'<br>おそれ '+fmt(d.potential)+' '+esc(d.unit):'')+'</span></td><td><div class="'+(d.loss!=null||d.modelEstimate!=null?'number':'sub')+'">'+amount+'</div><span class="sub '+(d.modelEstimate!=null?'modeltag':'')+'">'+esc(amountLabel)+'</span></td><td><button class="cellbtn" data-id="'+esc(d.id)+'" aria-label="'+esc(d.org)+'の詳細">↗</button></td></tr>';
 }).join('');
 document.querySelectorAll('[data-id]').forEach(b=>b.onclick=()=>openDetail(data.find(d=>d.id===b.dataset.id),b));
 $('reviewsummary').textContent={discovery:'発見用索引に記載された探索候補です。一次資料の本文・被害有無・日付は未確認で、確定した事故として扱いません。',named:'実名公表記録を確認段階にかかわらず表示しています。精査前の記録はラベルで区別し、分類や数量を確定値として扱いません。',curated:'原資料を個別参照した実名公表記録です。全項目の精査完了や被害の確定を意味しません。',mechanical:'探索用の精査前記録です。攻撃分類・レベルは付与せず、数量は原資料で確認してください。',anonymous:'匿名調査個票と歴史資料です。実名記録との重複は未排除。',all:'公表記録・匿名歴史資料・本文確認待ちの探索候補をすべて表示しています。確認段階をラベルで区別し、独立事故数とは扱いません。'}[review];
 $('csv').textContent='↓ 条件に合う全'+fmt(filtered.length)+'件をCSV出力';
}
function reviewBadges(d){return '<span class="badge quality '+ReviewEvidence.quality(d)+'">'+esc(ReviewEvidence.label(d))+'</span><span class="badge evidence">'+esc(ReviewEvidence.state(d))+'</span>'+(ReviewEvidence.followup(d)?'<span class="badge">続報表記あり</span>':'')}
function showModal(d,focus){lastFocus=focus;d.showModal()}
function openDetail(d,b){
 current=d;const l=severity(d),preliminary=ReviewEvidence.needsReview(d);
 const countLabel=d.reportedCount!=null?'原資料の対象規模（確認状況は未分離）':'可能性・対象規模（確認済みと合算不可）';
 const v=preliminary?null:d.reportedCount??d.potential;
 $('detailcontent').innerHTML='<div class="eyebrow">'+(d.discoveryOnly?'DISCOVERY CANDIDATE / ':'PUBLIC RECORD / ')+esc(d.id.toUpperCase())+'</div><h2>'+esc(d.org)+'</h2><p>'+esc(d.title)+'</p>'+badge(d)+' <span class="badge">'+esc(preliminary?'分類は精査前':d.type)+'</span> <span class="badge">'+esc(d.scope)+'</span>'+(d.anonymous?'<div class="notice">組織名が原資料にない匿名個票です。実名公表記録との重複は未排除です。</div>':'')+'<div class="detailgrid"><div><small>確認済み漏えい</small><b>'+fmt(preliminary?null:d.confirmed)+(d.confirmed!=null?' '+esc(d.unit):'')+'</b></div><div><small>'+countLabel+'</small><b>'+fmt(v)+(v!=null?' '+esc(d.unit):'')+'</b></div><div><small>'+esc(d.dateLabel||'発生・認知・公開開始日')+'</small><b>'+esc(d.date||'未特定')+'</b></div><div><small>'+esc(d.publicationKind||'初回公表日')+'</small><b>'+esc(d.published)+'</b></div></div><h3>手口・侵入経路</h3><p>'+esc(preliminary?'手口・侵入経路は未精査。原資料をご確認ください。':d.method+' ／ '+d.entry)+'</p><h3>情報の種類と業務影響</h3><p>'+esc(d.data)+'<br>'+esc(d.impact)+'</p><h3>実額・会社の費用見込額</h3><p><b>'+money(d.loss)+(d.loss!=null?'（'+esc(d.lossKind)+'）':'')+'</b><br>'+esc(d.lossNote||'本版では金額未収録。非公表またはゼロと断定するものではありません。')+'</p>'+(d.modelEstimate!=null?'<div class="modelbox"><h3>原資料のJNSAモデルによる想定損害賠償額</h3><strong>'+money(d.modelEstimate)+'</strong><p>JNSAが当時のモデルで試算した値です。実損・支払額・裁判の認容額ではありません。現在のリスク評価にはそのまま適用できません。</p></div>':'')+'<h3>暫定レベルの根拠</h3><p>'+esc(l[2])+'。影響の軸：'+esc(preliminary?'未精査':d.cia.join('・')||'未特定')+'。当サイトの独自分類。モデル推計額はレベル判定に使いません。</p><div class="notice">'+esc(d.note)+'</div><h3>出典・収録根拠</h3><div class="sources">'+d.sources.map(s=>'<a href="'+esc(s[1])+'" target="_blank" rel="noopener noreferrer">'+esc(s[0])+' ↗</a>').join('')+'</div><div class="detailfoot">情報時点：'+esc(d.asof)+' ／ 資料確認：2026-11-07'+(d.sourceRow?'<br>原資料：No.'+d.sourceRow+' ／ PDF p.'+d.sourcePage:'')+'<br>公表資料時点の調査範囲・推計の限界があります。</div><p><button class="outline" id="usecalc">この事案の件数を試算に使う →</button> <button class="outline" id="copylink">詳細リンクを表示</button></p><p id="linktext"></p>';
 $('detailcontent').insertAdjacentHTML('afterbegin','<div class="reviewbadges">'+reviewBadges(d)+'</div><p class="sub">組織の掲載は被害の確定・責任の認定を意味しません。確認は各項目の出典・時点に限られます。</p>');
 $('detailcontent').insertAdjacentHTML('beforeend','<p><a class="outline correction" href="'+esc(ReviewEvidence.correction(d))+'" target="_blank" rel="noopener noreferrer">この記録の訂正を報告する ↗</a></p><p class="sub">GitHubログインが必要・投稿は公開。個人情報や漏えいデータそのものは投稿しないでください。</p>');
 if(d.publicQuantities?.length)$('detailcontent').insertAdjacentHTML('beforeend','<h3>原資料の数量（範囲・内数は未分離、合算不可）</h3><div class="tablewrap"><table style="min-width:450px"><thead><tr><th>数量の種類</th><th>公表値</th><th>確認状況</th></tr></thead><tbody>'+d.publicQuantities.map(q=>'<tr><td>'+esc(q.label)+'</td><td>'+fmt(q.value)+' '+esc(q.unit)+'</td><td>'+esc(q.certainty)+'</td></tr>').join('')+'</tbody></table></div>');
 if(d.relatedIncidentGroups?.length)$('detailcontent').insertAdjacentHTML('beforeend','<h3>関連する提供元・サービスのグループ</h3><p>'+d.relatedIncidentGroups.map(esc).join(' / ')+'。同一原因の影響先を別の公表記録として含む可能性があります。</p>');
 showModal($('detail'),b);
 $('usecalc').disabled=preliminary||[d.confirmed,d.potential,d.reportedCount].every(x=>x==null);
 $('usecalc').onclick=()=>{$('detail').close();switchView('calc');$('n').value=d.confirmed??d.potential??d.reportedCount??0;calculate();$('n').focus()};
 $('copylink').onclick=()=>{$('linktext').textContent=location.origin+location.pathname+'#incident='+encodeURIComponent(d.id)};
}
function switchView(v){
 for(const name of ['list','analysis','calc','coverage'])$(name+'view').hidden=name!==v;
 document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===v));
 if(v==='analysis')drawCharts();
}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>switchView(b.dataset.view));
function setReview(value){review=value;document.querySelectorAll('[data-review]').forEach(x=>{x.classList.toggle('selected',x.dataset.review===review);x.setAttribute('aria-pressed',String(x.dataset.review===review))})}
document.querySelectorAll('[data-review]').forEach(b=>b.onclick=()=>{setReview(b.dataset.review);render(true)});
for(const id of ['q','type','sector','level','cia','supplier','status','sort','pagesize'])$(id).addEventListener(id==='q'?'input':'change',()=>render(true));
$('prev').onclick=()=>{page--;render()};$('next').onclick=()=>{page++;render()};
$('more').onclick=()=>{$('extra').hidden=!$('extra').hidden;$('more').textContent=$('extra').hidden?'詳細条件 ＋':'詳細条件 −'};
$('reset').onclick=()=>{for(const id of ['q','type','sector','level','year','month','cia','status'])$(id).value='';$('supplier').checked=false;$('sort').value='new';$('basis').value='published';synchronizePeriod();kind='all';setReview('all');render(true)};
function synchronizePeriod(changed){
 const chosen=$('month').value;
 if(changed==='month'&&chosen)$('year').value=chosen.slice(0,4);
 const year=$('year').value;
 const months=[...new Set(data.map(periodDate).map(s=>s.slice(0,7)).filter(m=>/^\d{4}-\d{2}$/.test(m)&&(!year||m.startsWith(year))))].sort().reverse();
 $('month').innerHTML='<option value="">すべての月</option>'+months.map(m=>'<option value="'+m+'">'+m+'</option>').join('');
 if(months.includes(chosen))$('month').value=chosen;
 const dateLabel=$('basis').value==='event'?'発生日（判明分）':'公表・資料日';
 $('periodsummary').textContent=dateLabel+'：'+($('month').value||year||'全期間')+($('basis').value==='event'?'（発生日不明・認知日・和解日等のみの記録は除外）':'。年月の選択肢は収録データに合わせて更新します。');
}
for(const id of ['year','month','basis'])$(id).onchange=()=>{synchronizePeriod(id);render(true)};
$('latestperiod').onclick=()=>{const latest=data.map(periodDate).map(s=>s.slice(0,7)).filter(m=>/^\d{4}-\d{2}$/.test(m)).sort().at(-1);if(latest){$('year').value='';synchronizePeriod();$('month').value=latest;synchronizePeriod('month');render(true)}};
$('allperiod').onclick=()=>{$('year').value='';$('month').value='';synchronizePeriod();render(true)};
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
 const fields=['discoveryOnly','reviewStage','publicationEvidence','followupIndicator','id','org','title','anonymous','published','publicationKind','date','dateLabel','asof','sector','type','originalCause','method','entry','scope','cia','confirmed','potential','reportedCount','unit','status','loss','lossKind','lossNote','modelEstimate','sourceRow','sourcePage','verification','relatedIncidentGroups','publicQuantities','note','sources'];
 const escape=v=>{let s=String(v??'');if(/^[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"'};
 const csv='\ufeff'+fields.join(',')+'\r\n'+filtered.map(d=>fields.map(k=>escape(k==='reviewStage'?ReviewEvidence.label(d):k==='publicationEvidence'?ReviewEvidence.state(d):k==='followupIndicator'?(ReviewEvidence.followup(d)?'原題等に続報表記あり':'未判定'):k==='sources'?d.sources.map(s=>s.join(': ')).join(' | '):k==='publicQuantities'?JSON.stringify(d[k]||[]):Array.isArray(ReviewEvidence.exportValue(d,k))?ReviewEvidence.exportValue(d,k).join(' / '):ReviewEvidence.exportValue(d,k))).join(',')).join('\r\n');
 const a=document.createElement('a'),url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8;'}));a.href=url;a.download='incident-atlas-20261107.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
function bars(id,values,total){
 $(id).innerHTML=Object.entries(values).sort((a,b)=>b[1]-a[1]).map(([k,v])=>'<div class="barrow">'+esc(k)+'<span>'+fmt(v)+' 件</span><div class="bar"><i style="width:'+v/Math.max(total,1)*100+'%"></i></div></div>').join('');
}
function drawCharts(){
 const rows=data.filter(d=>!d.discoveryOnly&&selectedKind(d,$('analysiskind').value)&&ReviewEvidence.matches(d,$('analysisreview').value));
 bars('bars',rows.reduce((a,d)=>(a[ReviewEvidence.needsReview(d)?'分類は精査前':d.type]=(a[ReviewEvidence.needsReview(d)?'分類は精査前':d.type]||0)+1,a),{}),rows.length);
 bars('ciabars',rows.reduce((a,d)=>((ReviewEvidence.needsReview(d)?['影響は精査前']:d.cia).forEach(x=>a[x]=(a[x]||0)+1),a),{}),rows.length);
 drawYearChart(rows);
}
$('analysiskind').onchange=drawCharts;$('analysisreview').onchange=drawCharts;

function drawYearChart(rows){
 const basis=$('yearbasis').value,event=basis==='event',to=Math.max(2026,...data.map(d=>Number(d.published.slice(0,4)))),all=$('yearrange').value==='all';
 const dates=rows.flatMap(d=>event?(d.date&&!/認知|検知|和解|講演|可能性|判決/.test(d.dateLabel||'')?[d.date]:[]):[d.published]).filter(Boolean).map(s=>Number(s.slice(0,4)));
 const from=all?Math.min(2002,...dates):2002;
 const result=YearlyEvidence.aggregate(rows,{basis,from,to}),series=result.series;
 const maximum=Math.max(1,...series.map(x=>x.total)),step=maximum<=5?1:Math.pow(10,Math.floor(Math.log10(maximum)))/2,top=Math.ceil(maximum/step)*step;
 const width=Math.max(850,series.length*34+80),height=340,left=62,right=18,plot=width-left-right,bottom=260,plotHeight=220,slot=plot/series.length,barWidth=Math.max(5,slot*.62);
 const ticks=[...new Set(Array.from({length:5},(_,i)=>Math.round(top*i/4)))];
 let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+width+' '+height+'" style="min-width:'+width+'px" role="img" aria-labelledby="annualtitle annualdesc"><title id="annualtitle">'+(event?'発生年判明分の収録記録':'調査・公表年別の収録記録')+'の件数</title><desc id="annualdesc">'+from+'年から'+to+'年、合計'+fmt(result.total)+'レコード。実名と匿名の重複は未排除。正確な値は下の年別表に掲載。</desc>';
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
 $('yearnote').textContent=(event?'発生日・不正アクセス開始日が記録された事案を集計。認知日・検知日・和解日・可能性の日付だけの事案は除外しています。':'匿名個票は調査対象年、実名公表記録は公表・資料年で集計。発生年の統計ではありません。')+' 本文確認待ちの探索候補はグラフから除外。確認段階：'+$('analysisreview').selectedOptions[0].textContent+'。表示期間：'+from+'～'+to+'年、'+fmt(result.total)+'レコード。'+(result.unknown?'日付未特定・基準不適合 '+fmt(result.unknown)+'件を除外。':'')+(result.outside?'期間外 '+fmt(result.outside)+'件を除外。':'');
 $('yearsummary').innerHTML='<div class="tablewrap"><table class="annualtable"><thead><tr><th>年</th><th>実名</th><th>匿名・歴史</th><th>計</th><th>収録状況</th></tr></thead><tbody>'+series.map(d=>'<tr><td>'+d.year+'</td><td>'+fmt(d.named)+'</td><td>'+fmt(d.anonymous)+'</td><td>'+fmt(d.total)+'</td><td>'+(event?(d.total?'発生日判明分':'該当データなし'):coverage.historical.some(c=>c.year===d.year)?'JNSA資料内の全行を照合':d.total?'個別収録のみ':'未収録')+'</td></tr>').join('')+'</tbody></table></div>';
}
$('yearbasis').onchange=drawCharts;$('yearrange').onchange=drawCharts;

function hydrate(row){
 const [year,no,published,sector,cause,route,reportedCount,modelEstimate,sourcePage]=row,source=coverage.historical.find(x=>x.year===year);
 return {id:'jnsa-'+year+'-'+String(no).padStart(4,'0'),org:'組織名非掲載 / '+sector,title:(causes[cause]||cause)+'・'+route,date:null,published,publicationKind:source.datePrecision==='year'?'調査対象年（公表日未特定）':'資料記載日',asof:String(year),sector,type:causes[cause]||'不明',method:cause,entry:route,scope:'不明',cia:['機密性'],confirmed:null,potential:null,reportedCount,unit:'人',status:'調査人数・確認状況未分離',data:'情報項目は本版未抽出',impact:'原資料の個票。被害人数には紛失・可能性等を含む場合があります。',note:'原資料は組織名を掲載していません。実名公表記録との照合・重複排除は未完了。被害人数を実流出確認人数に読み替えないでください。'+(source.countDiscrepancies?.some(x=>x.row===no)?' 原資料の表Aと表Bの人数に不一致があるため人数は表Aを採用。推計額は表Bの原表記です。':'' ),anonymous:true,recordKind:'調査個票',originalCause:cause,route,sourceRow:no,sourcePage,modelEstimate,sources:[['JNSA '+year+'年調査報告書・個票No.'+no+'（PDF p.'+sourcePage+'）',source.source]]};
}
function hydrateCandidate(r,checked){
 return {id:'candidate-'+r.key,org:r.organization,title:'一次資料本文の確認待ち（事故・被害の確定ではありません）',published:r.published||'',publicationKind:'発見用索引の記載日（公表・発生の別は未確認）',date:null,asof:checked,sector:'未確認',type:'未確認',method:'未確認',entry:'未確認',scope:'未確認',cia:[],confirmed:null,potential:null,reportedCount:null,unit:'件',status:r.result,data:'対象情報・数量・被害有無は未確認。'+(r.indexCause?' 索引記載の原因（未照合）：'+r.indexCause:'')+(r.indexQuantity?' 索引記載の数量（未照合・集計対象外）：'+r.indexQuantity:''),impact:'発見用索引の掲載情報のみ。一次資料の本文と組織・事案の照合が未完了です。',note:'発見済みの資料を隠さず検索できるようにした探索候補です。独立した事故・被害・責任を認定したものではありません。残る確認：'+r.result,anonymous:false,discoveryOnly:true,verification:'索引情報のみ・一次資料本文未確認',recordKind:'探索候補',sources:[['発見用索引（一次情報ではありません）',r.discovery],...(r.discoveryAliases||[]).map(a=>['同一資料の別索引',a.url]),...r.primaryUrls.map(u=>['一次資料の候補（未照合）',u])]};
}
async function initialize(){
 const get=async u=>{const r=await fetch(ASSET_URLS[u]||u,{cache:'no-store'});if(!r.ok)throw new Error(u);return r.json()};
 try{
 const [named,historical,cov,ledger]=await Promise.all([get('data.json'),get('historical.json'),get('coverage.json'),get('reconciliation.json')]);coverage=cov;
 data=[...named,...historical.rows.map(hydrate),...ledger.records.filter(r=>!r.recordIds?.length&&!r.duplicateOfKey).map(r=>hydrateCandidate(r,ledger.checked))];
 data.forEach(d=>{d.searchText=[d.id,d.org,d.title,d.sector,d.type,d.method,d.entry,d.data,d.note].join(' ').toLowerCase()});
 $('navtotal').textContent=fmt(data.length);$('total').textContent=fmt(data.length);
 const n=data.filter(d=>!d.anonymous&&!d.discoveryOnly).length,anon=data.filter(d=>d.anonymous).length;
 Promise.resolve(ledger).then(a=>{$('sourcepending').innerHTML=a.records.filter(r=>!r.recordIds?.length&&!r.duplicateOfKey).slice(0,100).map(r=>'<tr><td>'+esc(r.published||'未特定')+'</td><td>'+esc(r.organization)+'</td><td>'+esc(r.result)+'</td><td><a href="'+esc(r.discovery)+'" target="_blank" rel="noopener noreferrer">公表資料の索引 ↗</a></td></tr>').join('')}).catch(()=>{});
 get('source-manifest.json').then(a=>{$('sourcecheck').textContent='確認日：'+a.checked+'。発見 '+fmt(a.discovered)+'資料／照合結果を記録 '+fmt(a.accounted)+'資料／掲載記録との照合 '+fmt(a.linked)+'資料／確認待ち '+fmt(a.pending)+'資料。'+a.completeness;const rows=a.sources.map(x=>'<tr><td>'+esc(x.name)+'</td><td>'+fmt(x.discovered)+'</td><td>'+fmt(x.linked)+'</td><td>'+fmt(x.pending)+'</td></tr>');$('sourcesummary').innerHTML=rows.join('');$('sourcemonths').innerHTML=a.months.map(x=>'<tr><td>'+esc(x.month)+'</td><td>'+fmt(x.discovered)+'</td><td>'+fmt(x.linked)+'</td><td>'+fmt(x.pending)+'</td></tr>').join('')}).catch(()=>{$('sourcecheck').textContent='収集範囲を読み込めませんでした。JSONをご確認ください。'});
 get('october-2026-audit.json').then(a=>{$('monthaudittext').textContent='探索した索引記録 '+fmt(a.discoveryRecords)+'件、組織・出典URLを照合した候補 '+fmt(a.discoveryGroupsAfterUrlOrgMatch)+'件。当事者本文を取得して登録 '+fmt(a.addedRecords)+'件、既存記録への出典統合 '+a.mergedIntoExisting.length+'件、確認待ち '+fmt(a.pendingGroups)+'件。資料確認：'+a.checked+'。本文取得・機械照合は全項目の精査完了を意味しません。';$('pendingmonth').innerHTML=a.records.filter(r=>['本文確認待ち','組織と原文の照合待ち'].includes(r.result)).map(r=>'<tr><td>'+esc(r.organization)+'</td><td>'+esc(r.result)+'</td><td>'+r.primaryUrls.map(u=>'<a href="'+esc(u)+'" target="_blank" rel="noopener noreferrer">当事者資料 ↗</a>').join('<br>')+'</td></tr>').join('')}).catch(()=>{$('monthaudittext').textContent='照合結果を読み込めませんでした。JSONで確認できます。'});
 $('qualitycounts').textContent='個別整理 '+fmt(data.filter(d=>ReviewEvidence.quality(d)==='curated').length)+' ／ 精査前 '+fmt(data.filter(d=>ReviewEvidence.quality(d)==='mechanical').length)+' ／ 匿名・歴史 '+fmt(anon)+' ／ 探索候補 '+fmt(data.filter(d=>d.discoveryOnly).length)+' レコード';
 $('kindcounts').innerHTML=n+' <em>/</em> '+fmt(anon);
 $('yearcounts').innerHTML=coverage.historical.length+'<span>年分</span>';
 $('moneycounts').innerHTML=data.filter(d=>d.loss!=null).length+' <em>/</em> '+fmt(data.filter(d=>d.modelEstimate!=null).length);
 for(const [id,key] of [['type','type'],['sector','sector'],['year','published']]){
 const vals=id==='year'?[...new Set(data.flatMap(x=>[x.published.slice(0,4),(x.date||x.published).slice(0,4)]))]:[...new Set(data.map(x=>x[key]))];
 vals.filter(v=>v).sort((a,b)=>id==='year'?b.localeCompare(a):a.localeCompare(b,'ja')).forEach(v=>{let o=document.createElement('option');o.value=v;o.textContent=v;$(id).append(o)});
 }
 $('coveragebody').innerHTML=coverage.historical.sort((a,b)=>a.year-b.year).map(d=>'<tr><td>'+d.year+'年</td><td>'+fmt(d.rows)+'</td><td>'+(d.continuous?'1～'+d.maxRow+'を照合':'1～'+d.maxRow+'（原資料の1216は欠番）')+'</td><td><a href="'+esc(d.source)+'" target="_blank" rel="noopener noreferrer">報告書掲載ページ ↗</a></td></tr>').join('');
 synchronizePeriod();render();calculate();
 if(location.hash==='#analysis')switchView('analysis');
 $('policyjump').onclick=()=>{$('publication').scrollIntoView({behavior:'smooth'});};
 const match=location.hash.match(/^#incident=(.+)$/);
 if(match){const d=data.find(x=>x.id===decodeURIComponent(match[1]));if(d)openDetail(d,null)}
 }catch(e){$('empty').hidden=false;$('empty').textContent='公開版が更新されたか、資料を読み込めませんでした。ページを再読み込みしてください。';$('count').textContent='読み込みエラー'}
}
initialize();
