const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const model=vm.runInNewContext(fs.readFileSync('dist/yearly.js','utf8')+';YearlyEvidence');
const named=JSON.parse(fs.readFileSync('dist/data.json','utf8'));
const h=JSON.parse(fs.readFileSync('dist/historical.json','utf8'));
const records=named.concat(h.rows.map(r=>({published:r[2],date:null,anonymous:true})));
const source=model.aggregate(records,{basis:'source',from:1971,to:2026});
assert.equal(source.total,records.length);assert.equal(source.unknown,0);assert.equal(source.outside,0);
assert.equal(source.series.find(x=>x.year===2005).anonymous,1032);
assert.equal(source.series.find(x=>x.year===2014).anonymous,1591);
const recent=model.aggregate(records,{basis:'source',from:2002,to:2026});
assert.equal(recent.total+recent.outside,records.length);assert.equal(recent.outside,records.filter(d=>Number(d.published.slice(0,4))<2002).length);
const events=model.aggregate([
 {published:'2025-01-01',date:'2024-12-31'},
 {published:'2025-01-01',date:'2024-12-31',dateLabel:'認知日'},
 {published:'2025-01-01',date:'2024-12-31',dateLabel:'検知日'},
 {published:'1983',date:'1971-02-18',dateLabel:'和解日'},
 {published:'2025-01-01',date:null,anonymous:true},
 {published:'2025-01-01',date:'2024-08-01',dateLabel:'不正アクセス開始日（以降）'},
 {published:'2025-01-01',date:'2024-08-01',dateLabel:'不正アクセス開始の可能性'}
],{basis:'event',from:1971,to:2026});
assert.equal(events.total,2);assert.equal(events.unknown,5);assert.equal(events.series.find(x=>x.year===2024).total,2);
assert.equal(model.aggregate(records.filter(d=>d.anonymous),{basis:'event'}).total,0);
console.log('Annual counts reconcile; event dates do not fall back to disclosure, recognition, settlement or uncertain dates.');
