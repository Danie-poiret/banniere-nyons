const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {active, query, time, parisDate, usable, escape} = require('../assets/bus-nyons.js');
const now = Date.parse('2026-10-10T12:00:00Z');
const service = {start:'20261001', end:'20261231', week:[1,1,1,1,1,0,0], added:['20261010'], removed:['20261012']};
assert(active(service,'2026-10-10')); assert(!active(service,'2026-10-11')); assert(!active(service,'2026-10-12')); assert(!active(service,'2027-01-01'));
assert(active({start:'',end:'',week:[0,0,0,0,0,0,0],added:['20261010'],removed:[]},'2026-10-10'));
const source={status:'available',checkedAt:'2026-10-10T11:00:00Z',start:'20261001',end:'20261231'};
assert(!usable({...source,checkedAt:'2026-10-05T00:00:00Z'},'2026-10-10',now));
assert(!usable({...source,checkedAt:'2027-01-01T00:00:00Z'},'2026-10-10',now));
assert(!usable(source,'2027-01-01',now));
const data={sources:{d:source},routes:{r:{number:'D36',source:'d'}},services:{s:service},stops:{n:{name:'Nyons',city:'Nyons',nyons:true},m:{name:'Gare',city:'Montélimar',nyons:false}},trips:[
 {id:'out',route:'r',service:'s',stops:[['n',28800,28800,0,1],['m',32400,32400,1,0]]},
 {id:'in',route:'r',service:'s',stops:[['m',36000,36000,0,1],['n',39600,39600,1,0]]},
 {id:'restricted',route:'r',service:'s',stops:[['n',43200,43200,1,0],['m',46800,46800,1,0]]},
 {id:'reserved',route:'r',service:'s',stops:[['n',50400,50400,2,1],['m',54000,54000,1,0]]}]};
const opts={date:'2026-10-10',sense:'out',line:'',stop:'',city:''};
assert.equal(query(data,opts,now).length,2); assert(query(data,opts,now)[1].reservation);
assert.equal(query(data,{...opts,sense:'in'},now).length,1);
assert.equal(query(data,{...opts,city:'Avignon'},now).length,0);
assert.equal(query(data,{...opts,date:'2026-10-11'},now).length,0);
assert.equal(query(data,{...opts,date:'2027-01-01'},now).length,0);
data.trips.push({...data.trips[0],id:'duplicate'}); assert.equal(query(data,opts,now).length,2);
data.services.night={start:'20261009',end:'20261009',week:[1,1,1,1,1,1,1],added:[],removed:[]};
data.trips.push({id:'night',route:'r',service:'night',stops:[['n',88200,88200,0,1],['m',91800,91800,1,0]]});
assert.equal(query(data,opts,now)[0].depart,1800); assert.equal(time(88200),'00:30 (lendemain)');
assert.equal(parisDate(new Date('2026-10-10T23:30:00Z')),'2026-10-11');
assert.equal(parisDate(new Date('2026-10-25T01:30:00Z')),'2026-10-25');
assert.equal(escape('<img onerror="x">'),'&lt;img onerror=&quot;x&quot;&gt;');
const file=path.resolve(__dirname,'../assets/bus-nyons.json');
if(fs.existsSync(file)){
 const real=JSON.parse(fs.readFileSync(file,'utf8')),clock=Date.parse(real.generatedAt);
 const date=parisDate(new Date(clock));
 for(const trip of real.trips){assert(real.routes[trip.route]);assert(real.services[trip.service]);for(const stop of trip.stops)assert(real.stops[stop[0]]);}
 const zou=Object.entries(real.routes).find(([id,r])=>r.number==='924');
 const rows=zou ? query(real,{...opts,date,line:zou[0],city:'Avignon'},clock) : [];
 assert(rows.every(r=>r.from.city==='Nyons'&&r.to.city==='Avignon'));
 console.log(JSON.stringify({checks:'OK',routes:Object.values(real.routes).map(r=>r.number).sort(),regularTrips:real.trips.length,date,zouDepartureTimes:rows.map(r=>time(r.depart))}));
}else console.log('Schedule edge cases: OK');
