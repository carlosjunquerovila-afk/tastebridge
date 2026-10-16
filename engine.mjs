export const guests=['Guest A','Guest B','Guest C'];
export function decide(items,budget,access){
 if(!Array.isArray(items))throw Error('Candidates must be an array');
 if(typeof access!=='boolean')throw Error('Access requirement must be true or false');
 if(!Number.isFinite(budget)||budget<0) throw Error('Enter a valid nonnegative budget.');
 const valid=[],excluded=[],questions=[],ids=new Set();
 for(const c of items){
  if(!c||typeof c!=='object'||Array.isArray(c))throw Error('Invalid candidate');
  if(typeof c.id!=='string'||!c.id||ids.has(c.id))throw Error('Candidate IDs must be nonempty and unique');
  ids.add(c.id);
  const vetoes=c.vetoes??(c.veto?['Guest C']:[]);
  if(!Array.isArray(vetoes)||vetoes.some(g=>!guests.includes(g)))throw Error('Unknown veto participant');
  if(vetoes.length){excluded.push({id:c.id,reason:[...new Set(vetoes)].join(', ')+' vetoed this option'});continue;}
  if(c.cost==null){questions.push({id:c.id,reason:'Confirm the price'});continue;}
  if(!Number.isFinite(c.cost)||c.cost<0)throw Error('Invalid price');
  if(c.cost>budget){excluded.push({id:c.id,reason:'Above the per-person budget'});continue;}
  if(access&&c.access===false){excluded.push({id:c.id,reason:'Step-free requirement not met'});continue;}
  if(access&&c.access!==true){questions.push({id:c.id,reason:'Verify step-free access with the venue'});continue;}
  if(c.scores==null){questions.push({id:c.id,reason:'Missing preference evidence'});continue;}
  if(!Array.isArray(c.scores))throw Error('Preference evidence must be an array');
  const scores=Array.from(c.scores);
  if(scores.some(s=>s!=null&&(typeof s!=='number'||!Number.isFinite(s)||s<0||s>1)))throw Error('Invalid preference proxy');
  if(scores.length!==3||scores.some(s=>s==null)){questions.push({id:c.id,reason:'Missing preference evidence'});continue;}
  valid.push({...c,min:Math.min(...c.scores),mean:c.scores.reduce((a,b)=>a+b,0)/3});
 }
 const tie=(a,b)=>a.id<b.id?-1:a.id>b.id?1:0;
 valid.sort((a,b)=>b.min-a.min||b.mean-a.mean||tie(a,b));
 const average=[...valid].sort((a,b)=>b.mean-a.mean||tie(a,b));
 return {selected:valid[0]??null,baseline:average[0]??null,excluded,questions,alternatives:valid.slice(1)};
}
export function fixture(mode='conflict'){
 const rows=[{id:'majority',name:'Late-night listening room',detail:'Fictional music-led evening',cost:20,access:true,scores:[.95,.95,.05]},
 {id:'bridge',name:'Gallery & acoustic courtyard',detail:'Fictional shared cultural activity',cost:18,access:true,scores:[.6,.6,.6]},
 {id:'unknown',name:'Independent cinema loft',detail:'Fictional venue · access unverified',cost:12,access:null,scores:[.9,.9,.9]},
 {id:'premium',name:'Private studio encounter',detail:'Fictional premium experience',cost:80,access:true,scores:[1,1,1]}];
 if(mode==='aligned')rows[0].scores=[.95,.9,.9];
 if(mode==='missing')rows.forEach(r=>r.scores[2]=null);
 return rows;
}
