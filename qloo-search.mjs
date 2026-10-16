// Trusted Node.js process only. Never import this module into the browser bundle.
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const execute=promisify(execFile);
const origin='https://hackathon.api.qloo.com';
export function createQlooSearch({apiKey,run=execute,maxCalls=3,timeoutMs=15000}={}){
 if(!Number.isInteger(maxCalls)||maxCalls<1||maxCalls>20)throw Error('Invalid call budget');
 if(!Number.isInteger(timeoutMs)||timeoutMs<1||timeoutMs>30000)throw Error('Invalid timeout');
 let calls=0;
 return async function searchCulturalEntity(query){
  if(typeof query!=='string'||!query.trim()||query.length>160||/[\x00-\x1f\x7f]/.test(query))return {status:'invalid_query'};
  if(typeof apiKey!=='string'||!apiKey.trim())return {status:'credential_required'};
  if(calls>=maxCalls)return {status:'call_budget_exhausted'};
  calls++;
  try{
   const {stdout}=await run('qloo',['api','search','--query',query.trim(),'--json'],{
    shell:false,timeout:timeoutMs,killSignal:'SIGKILL',maxBuffer:512*1024,
    env:{PATH:process.env.PATH,HOME:process.env.HOME,QLOO_API_KEY:apiKey,
      QLOO_BASE_URL:origin,QLOO_TRUSTED_BASE_URL:origin}
   });
   // Never leak an echoed credential even if a provider or CLI unexpectedly emits it.
   if(typeof stdout!=='string'||stdout.includes(apiKey))return {status:'unsafe_response'};
   let payload;try{payload=JSON.parse(stdout);}catch{return {status:'invalid_json'};}
   if(JSON.stringify(payload).includes(apiKey))return {status:'unsafe_response'};
   if(!payload||typeof payload!=='object'||Array.isArray(payload))return {status:'invalid_response'};
   // Raw evidence only: API result schema and entity meaning still require validation.
   return {status:'unvalidated_evidence',source:'qloo_cli_search',
    retrieved_at:new Date().toISOString(),requires_entity_review:true,
    ready_for_ranking:false,payload};
  }catch(error){
   // Do not forward stdout/stderr, messages, credentials or raw upstream errors.
   return {status:error?.code==='ENOENT'?'harness_missing':error?.killed?'timeout':'upstream_failure'};
  }
 };
}
