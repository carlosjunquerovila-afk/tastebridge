import {fixture,guests} from './engine.mjs';
import {createSession} from './session.mjs';
const session=createSession();
const $=s=>document.querySelector(s);let items=fixture(),result=null;
const pct=n=>Math.round(n*100)+' / 100';
function cards(){
 $('#candidates').replaceChildren();
 for(const c of items){
  const el=document.createElement('article');el.className='card';
  el.innerHTML=`<div class="card-top"><div><h3>${c.name}</h3><small>${c.detail}</small></div><span class="price">€${c.cost}</span></div><div class="scores"></div>`;
  c.scores.forEach((v,i)=>{const label=document.createElement('label');label.textContent=guests[i]+' ';const out=document.createElement('output');out.textContent=v==null?'Unknown':pct(v);label.append(out);const slider=document.createElement('input');slider.type='range';slider.min='0';slider.max='100';slider.step='5';slider.value=v==null?'50':String(v*100);slider.setAttribute('aria-label',`${guests[i]} preference for ${c.name}`);slider.addEventListener('input',()=>{c.scores[i]=Number(slider.value)/100;out.textContent=pct(c.scores[i]);render();});label.append(slider);el.querySelector('.scores').append(label);});
  for(const guest of guests){const label=document.createElement('label');label.className='check';const veto=document.createElement('input');veto.type='checkbox';veto.checked=(c.vetoes??[]).includes(guest);veto.addEventListener('change',()=>{c.vetoes=(c.vetoes??[]).filter(g=>g!==guest);if(veto.checked)c.vetoes.push(guest);render();});label.append(veto,document.createTextNode(guest+' vetoes this option'));el.append(label);}$('#candidates').append(el);
 }
}
function render(){
 $('#confirmation').textContent='';
 try{const raw=$('#budget').value;result=session.update(items,raw.trim()===''?NaN:Number(raw),$('#access').checked);}catch(e){result=null;$('#result').textContent=e.message;$('#confirm').disabled=true;$('#export').disabled=true;return;}
 $('#export').disabled=false;$('#confirm').disabled=!result.selected;
 const s=result.selected,b=result.baseline;
 $('#result').innerHTML=s?`<p class="proposal">${s.name}</p><div class="metrics"><div class="metric"><strong>${pct(s.min)}</strong><span>Lowest preference proxy</span></div><div class="metric"><strong>${pct(s.mean)}</strong><span>Group average proxy</span></div><div class="metric"><strong>€${s.cost}</strong><span>Fictional cost per guest</span></div></div><p class="explain">This option has the strongest lowest score among the options that pass the current constraints. Ask the group before treating the proposal as a shared decision.</p><p class="comparison"><strong>Average-only comparison:</strong> ${b.name} — lowest ${pct(b.min)}, average ${pct(b.mean)}. ${s.id===b.id?'Both rules agree in this scenario.':(s.mean < b.mean ? 'This proposal lowers the average to improve the weakest match.' : 'The average is tied; this proposal improves the weakest match.')}</p>`:`<p class="proposal">${result.questions.length?'We need more information.':'No option meets these constraints.'}</p><p>No recommendation is being made. Review the constraints or resolve the unknowns below.</p>`;
 const issues=document.createElement('div');issues.className='issues';for(const [title,rows]of [['Held for clarification',result.questions],['Excluded',result.excluded]]){const col=document.createElement('div');const h=document.createElement('h3');h.textContent=title;col.append(h);const ul=document.createElement('ul');if(!rows.length){const li=document.createElement('li');li.textContent='None';ul.append(li);}for(const row of rows){const li=document.createElement('li');li.textContent=items.find(x=>x.id===row.id).name+': '+row.reason;ul.append(li);}col.append(ul);issues.append(col);}$('#result').append(issues);
}
function reset(){items=fixture($('#scenario').value);$('#budget').value='25';$('#access').checked=true;cards();render();}
$('#scenario').addEventListener('change',reset);$('#reset').addEventListener('click',reset);$('#budget').addEventListener('input',render);$('#access').addEventListener('change',render);
$('#confirm').addEventListener('click',()=>{if(result?.selected){session.confirm();$('#confirmation').textContent='Confirmed in this local test only. Individual group consent is not verified. No booking or message has been sent.';}});
$('#export').addEventListener('click',()=>{if(!result)return;const data=session.export();const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='tastebridge-decision.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
cards();render();
