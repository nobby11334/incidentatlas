'use strict';
const YearlyEvidence={
 aggregate(rows,{basis='source',from=2002,to=2026}={}){
  const years=new Map();let unknown=0,outside=0;
  for(const d of rows){
   // A disclosure, recognition, judgment or settlement date is not an occurrence date.
   const valid=basis!=='event'||(d.date&&!/認知|検知|和解|講演|可能性|判決/.test(d.dateLabel||''));
   const date=valid?(basis==='event'?d.date:d.published):null;
   if(!date||!/^\d{4}(?:-|$)/.test(date)){unknown++;continue}
   const year=Number(date.slice(0,4));
   if(year<from||year>to){outside++;continue}
   if(!years.has(year))years.set(year,{year,named:0,anonymous:0,total:0});
   const point=years.get(year);point[d.anonymous?'anonymous':'named']++;point.total++;
  }
  const series=[];for(let y=from;y<=to;y++)series.push(years.get(y)||{year:y,named:0,anonymous:0,total:0});
  return {series,unknown,outside,total:series.reduce((n,x)=>n+x.total,0)};
 }
};
