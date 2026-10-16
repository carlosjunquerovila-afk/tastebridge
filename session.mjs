import {decide} from './engine.mjs';
export function createSession(){
 let snapshot=null,confirmed=null;
 return {
  update(items,budget,access){
   snapshot=null;confirmed=null;
   const result=decide(items,budget,access);
   snapshot=structuredClone({mode:'SYNTHETIC_OFFLINE_FIXTURE',qloo_connected:false,
    scope:'single activity',inputs:{items,budget,require_step_free:access},result});
   return result;
  },
  confirm(){
   if(!snapshot?.result.selected)throw Error('No proposal to confirm');
   confirmed={candidate_id:snapshot.result.selected.id,kind:'local_test_confirmation',
    group_consent_verified:false,booking_created:false};
  },
  export(){
   if(!snapshot)throw Error('No valid decision to export');
   return structuredClone({...snapshot,confirmation:confirmed,
    status:confirmed?'confirmed_in_local_test':'not_confirmed'});
  }
 };
}
