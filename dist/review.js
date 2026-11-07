'use strict';
// Display policy: editorial review, disclosure evidence and independent incidents are separate.
const ReviewEvidence={
 legacyEditorialIds:new Set(["asahi", "askul", "kadokawa", "dmm", "jal", "line", "ntt", "toyota-location", "toyota-map", "amagasaki", "bunkyo", "nenkin", "waseda-1998", "uji-1999", "lawson-2003", "yahoobb-2004", "dion-2006", "dnp-2007", "psn-2011", "benesse-2014", "jal-2014", "jtb-dtravel-2016", "persol-2017", "coincheck-2018", "takufile-2019", "7pay-2019", "kanagawa-hdd-2019", "zojirushi-2019", "nintendo-2020", "capcom-2020", "mhipower-2020", "kawasaki-2020", "projectweb-2021", "omiai-2021", "handa-2021", "fujitsu-malware-2024", "iij-smx-2025", "idcf-2026", "sourcenext-2026", "jnsa-check-2026"]),
 quality(d){
  if(d.anonymous)return 'anonymous';
  if(d.verification==='一次資料を個別確認した項目あり')return 'curated';
  if(d.reviewStage==='curated'||this.legacyEditorialIds.has(d.id))return 'curated';
  return 'mechanical';
 },
 label(d){return {curated:'個別整理・項目ごとに確認',mechanical:'機械照合・詳細精査前',anonymous:'匿名・歴史資料'}[this.quality(d)]},
 matches(d,mode){return mode==='all'||this.quality(d)===mode},
 followup(d){return /続報|第[2-9２-９二三四五六七八九十]+[報信]|追加報告|経過報告/.test((d.title||'')+' '+(/未分離|未特定|不明/.test(d.publicationKind||'')?'':d.publicationKind||''))},
 state(d){
  const text=(d.title||'')+' '+(d.status||'');
  if(d.publicationStatus==='denied')return '被害否定の公表・原資料参照';
  if(/(?:漏[え洩]い|流出|不正アクセス).{0,15}(?:はない|はありません|確認されていません|認められません)/.test(text))return '否定表現あり・個別確認が必要';
  if(this.quality(d)==='mechanical')return '被害有無・範囲は精査前';
  if(d.anonymous)return '調査個票・実流出確認とは別';
  if(d.confirmed>0)return '漏えい確認の公表値あり';
  if(d.potential!=null)return '可能性・対象範囲の公表';
  return '被害有無・範囲は原資料参照';
 },
 needsReview(d){return this.quality(d)==='mechanical'||/^(?:否定表現|被害否定)/.test(this.state(d))},
 occurrence(d){return d.date&&!/認知|検知|和解|講演|可能性|判決/.test(d.dateLabel||'')?d.date:''},
 exportValue(d,key){
  if(this.needsReview(d)){
   if(['confirmed','potential','reportedCount'].includes(key))return null;
   if(['type','method','entry','cia','scope'].includes(key))return '未精査';
  }
  return d[key];
 },
 correction(d){
  const title='[訂正依頼] '+(d?d.id:'記録・表示について');
  const body='対象レコードID: '+(d?d.id:'')+'\n対象ページ: '+(d?'https://nobby11334.github.io/incidentatlas/#incident='+encodeURIComponent(d.id):'https://nobby11334.github.io/incidentatlas/')+'\n誤りと思われる箇所:\n修正内容:\n根拠となる公開一次資料URL:\n資料の公表日・更新日:\n\n個人情報・漏えいデータそのもの・認証情報は記載しないでください。';
  return 'https://github.com/nobby11334/incidentatlas/issues/new?title='+encodeURIComponent(title)+'&body='+encodeURIComponent(body);
 }
};
if(typeof module!=='undefined')module.exports=ReviewEvidence;
