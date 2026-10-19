// Actual application controller under a small simulated DOM, not browser rendering.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.events={};this.value='';this.disabled=false;this.checked=false;this._text='';}
 set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 append(...nodes){this.children.push(...nodes);}prepend(...nodes){this.children.unshift(...nodes);}replaceChildren(...nodes){this._text='';this.children=[...nodes];}
 addEventListener(name,fn){this.events[name]=fn;}
}
const ids={};for(const id of ['connection','message','guests','budget','access','create','current','evaluate','reload','guest','kind','seedQuery','placeQuery','searchSeed','searchPlace','seedMatches','placeMatches','facts','proposal','evidence']){ids[id]=new Element(['create','evaluate','reload','searchSeed','searchPlace'].includes(id)?'button':['guests','budget','access','seedQuery','placeQuery'].includes(id)?'input':['guest','kind'].includes(id)?'select':'div');ids[id].id=id;}
ids.guests.value='3';ids.budget.value='25';
const all=()=>Object.values(ids).flatMap(root=>{const walk=e=>[e,...e.children.flatMap(walk)];return walk(root);});
let calls=[],responseQueue=[];
const context=vm.createContext({document:{getElementById:id=>ids[id],createElement:t=>new Element(t),querySelectorAll:selector=>all().filter(e=>selector.split(',').includes(e.tag))},Option:class extends Element{constructor(t,v){super('option');this.textContent=t;this.value=v;}},Date,JSON,Number,Map,Error,fetch:async(url,options)=>{if(url==='/api/status')return{json:async()=>({csrf:'TEST_TOKEN',configured:false,reason:'credential_missing'})};calls.push(JSON.parse(options.body));if(!responseQueue.length)throw new Error('Unexpected test request');const value=responseQueue.shift();return{ok:true,json:async()=>await value};}});
vm.runInContext(fs.readFileSync(__dirname+'/app.js','utf8')+'\nthis.test={get drafts(){return drafts;}};',context);
const tick=()=>new Promise(r=>setImmediate(r));
const state=()=>({session_id:'SYNTHETIC_SESSION',revision:0,budget:25,required_facts:[],participants:{guest_1:[],guest_2:[],guest_3:[]},candidates:{a:{name:'<script>synthetic</script>',cost_per_person:10,facts:{},source_note:'Synthetic host',observed_at:new Date(Date.now()-60000).toISOString(),vetoes:[]},b:{name:'Second fictional place',cost_per_person:12,facts:{},source_note:'Synthetic host',observed_at:new Date(Date.now()-60000).toISOString(),vetoes:[]}}});
const input=(card,label)=>card.children.find(e=>e.tag==='label'&&e._text===label).children[0];
const button=(card,label)=>card.children.find(e=>e.tag==='button'&&e._text===label);
(async()=>{
 const passed=[];await tick();assert.equal(ids.evaluate.disabled,true);passed.push('No comparison before session');
 responseQueue.push(state());await ids.create.onclick();assert.equal(ids.evaluate.disabled,false);assert.equal(ids.facts.children[0].children[0].textContent,'<script>synthetic</script>');passed.push('Provider names rendered as text, not HTML');
 let [a,b]=ids.facts.children;let price=input(a,'Price per guest (€)');price.value='19';price.events.input();assert.equal(ids.evaluate.disabled,true);assert.equal(context.test.drafts.size,1);passed.push('Unsaved edit disables evaluation and invalidates old evidence');
 let bprice=input(b,'Price per guest (€)');bprice.value='23';bprice.events.input();let updated=state();updated.revision=1;updated.candidates.a.cost_per_person=19;responseQueue.push(updated);await button(a,'Save reviewed facts').onclick();assert.equal(input(ids.facts.children[1],'Price per guest (€)').value,'23');assert.equal(context.test.drafts.size,1);assert.equal(ids.evaluate.disabled,true);passed.push('Saving one candidate preserves another unsaved edit');
 button(ids.facts.children[1],'Discard edits').onclick();assert.equal(ids.evaluate.disabled,false);assert.equal(input(ids.facts.children[1],'Price per guest (€)').value,12);passed.push('Explicit discard restores recorded value');
 let resolve;responseQueue.push(new Promise(r=>resolve=r));const pending=ids.evaluate.onclick();await tick();assert.equal(ids.create.disabled,true);assert.equal(input(ids.facts.children[0],'Price per guest (€)').disabled,true);const before=calls.length;await ids.searchPlace.onclick();assert.equal(calls.length,before);passed.push('Pending operation serializes actions and locks editable inputs');
 resolve({status:'blocked',reason:'credential_missing'});await pending;assert.match(ids.proposal.textContent,/No proposal/);assert.doesNotMatch(ids.proposal.textContent,/Lowest guest rank/);passed.push('Provider block clears previous proposal');
 const current=state();current.revision=2;responseQueue.push(current);await ids.reload.onclick();assert.equal(ids.evaluate.disabled,false);passed.push('Reload leaves a usable current session');
 console.log(JSON.stringify({mode:'SIMULATED_DOM_WITH_ACTUAL_APP_JS',passed:passed.length,checks:passed,browser_rendering:false,external_provider_calls:0},null,2));
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
  
