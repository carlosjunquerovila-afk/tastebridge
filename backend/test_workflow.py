import copy
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from datetime import timedelta
from unittest.mock import patch

from workflow import Workflow, ordinal, stamp
from server import make_server
from qloo_adapter import QlooAdapter

IDS = [f'{i:08d}-1111-4111-8111-111111111111' for i in range(1, 10)]


class SyntheticAdapter(QlooAdapter):
    """Test-only provider; no credentials, subprocesses or external requests."""
    def __init__(self):
        super().__init__(max_calls=20)
        self.calls=[]; self.missing=False

    def search(self, query, entity_type):
        self.calls.append(('search',query,entity_type));self.remaining-=1
        i=int(query)
        return {'status':'needs_entity_review','matches':[{'entity_id':IDS[i],'name':'Fictional '+query}],
                'live_result':False,'automatic_selection':False}

    def shortlist(self, seeds, candidates, entity_type, **kwargs):
        self.calls.append(('shortlist',seeds,list(candidates)));self.remaining-=1
        # Different absolute scales, same shortlist. Only within-query ordering is meaningful.
        scores=([1000,900,100] if seeds[0] in IDS[:2] else [1,2,3])
        values={k:scores[IDS.index(k)-3] for k in candidates}
        if self.missing: values.pop(next(iter(values)))
        return {'status':'needs_information' if self.missing else 'evidence_only',
                'affinities':values,'live_result':False,'provenance':'SYNTHETIC_TEST_ONLY'}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.provider=SyntheticAdapter();self.app=Workflow(self.provider)
        self.ready=patch.object(self.app,'availability',return_value={'configured':True,'reason':'SYNTHETIC_TEST_ONLY'})
        self.ready.start();self.addCleanup(self.ready.stop)
        self.s=self.app.call('create',{'participants':3,'budget':25,'required_facts':['step_free']})
        self.sid=self.s['session_id']

    def call(self,action,**args):
        out=self.app.call(action,{'session_id':self.sid,'revision':self.s['revision'],**args})
        if 'participants' in out:self.s=out
        return out

    def seed(self,number,participant):
        r=self.call('search',role='seed',query=str(number),entity_type='movie')
        self.call('confirm_entity',search_id=r['search_id'],entity_id=IDS[number],participant=participant,reviewed=True)

    def candidate(self,number,cost=20,step_free=True,vetoes=None):
        r=self.call('search',role='candidate',query=str(number))
        self.call('confirm_entity',search_id=r['search_id'],entity_id=IDS[number],reviewed=True)
        self.call('candidate_facts',entity_id=IDS[number],cost_per_person=cost,facts={'step_free':step_free},
                  vetoes=vetoes or [],source_note='SYNTHETIC TEST HOST CONFIRMATION',observed_at=stamp().isoformat(),reviewed=True)

    def prepare(self):
        for i,p in enumerate(self.s['participants']):self.seed(i,p)
        for i in (3,4,5):self.candidate(i)

    def test_ordinal_monotonic_invariance_ties_single(self):
        scores={'a':8,'b':8,'c':2}
        self.assertEqual(ordinal(scores),ordinal({k:v*7+21 for k,v in scores.items()}))
        self.assertEqual(ordinal(scores),{'a':.75,'b':.75,'c':0})
        self.assertEqual(ordinal({'one':100000}),{'one':.5})
        for v in (True,float('nan'),float('inf')):
            with self.assertRaises(ValueError):ordinal({'a':v})

    def test_full_flow_counterfactual_and_single_call_per_guest(self):
        self.prepare();r=self.call('evaluate')
        self.assertEqual(r['result']['selected']['id'],IDS[4])
        self.assertEqual(r['result']['mean_only_baseline']['id'],IDS[3])
        self.assertEqual(r['result']['selected']['minimum_proxy'],.5)
        self.assertFalse(r['live_result']);self.assertFalse(r['booking_performed'])
        self.assertTrue(r['requires_group_confirmation'])
        calls=[c for c in self.provider.calls if c[0]=='shortlist']
        self.assertEqual(len(calls),3);self.assertTrue(all(c[2]==IDS[3:6] for c in calls))
        self.assertEqual(r,self.call('evaluate'));self.assertEqual(len(self.provider.calls),9)

    def test_credential_absence_stops_real_adapter(self):
        app=Workflow();s=app.call('create',{'participants':2,'budget':20})
        with patch.dict(os.environ,{},clear=True),patch.object(app.adapter,'search') as run:
            r=app.call('search',{'session_id':s['session_id'],'revision':0,'role':'seed','query':'Dune','entity_type':'movie'})
            self.assertEqual(r['reason'],'credential_missing');run.assert_not_called()

    def test_entity_review_rejects_invention_and_missing_consent(self):
        r=self.call('search',role='seed',query='0',entity_type='movie')
        for eid,confirmed in [(IDS[1],True),(IDS[0],False)]:
            with self.assertRaises(ValueError):self.call('confirm_entity',search_id=r['search_id'],entity_id=eid,participant='guest_1',reviewed=confirmed)
        self.assertEqual(self.s['participants']['guest_1'],[])

    def test_stale_revision_rejects_before_provider(self):
        self.seed(0,'guest_1');count=len(self.provider.calls)
        with self.assertRaises(ValueError):self.app.call('search',{'session_id':self.sid,'revision':0,'role':'candidate','query':'3'})
        self.assertEqual(len(self.provider.calls),count)

    def test_missing_seed_blocks_retrieval(self):
        self.seed(0,'guest_1');self.candidate(3)
        self.assertEqual(self.call('evaluate')['reason'],'reviewed_entities_required')
        self.assertFalse(any(c[0]=='shortlist' for c in self.provider.calls))

    def test_hard_constraints_before_provider_and_ranking(self):
        for i,p in enumerate(self.s['participants']):self.seed(i,p)
        self.candidate(3,cost=30);self.candidate(4,vetoes=['guest_1']);self.candidate(5,step_free=None)
        r=self.call('evaluate');self.assertEqual(r['status'],'needs_information')
        self.assertFalse(any(c[0]=='shortlist' for c in self.provider.calls))

    def test_missing_provider_entity_stops_whole_proposal_and_no_retry(self):
        self.prepare();self.provider.missing=True
        r=self.call('evaluate');self.assertEqual(r['status'],'blocked');self.assertIsNone(r['proposal'])
        before=len(self.provider.calls);self.assertEqual(r,self.call('evaluate'));self.assertEqual(before,len(self.provider.calls))

    def test_facts_mutation_invalidates_cache_and_changes_hash(self):
        self.prepare();first=self.call('evaluate')
        self.call('candidate_facts',entity_id=IDS[4],cost_per_person=21,facts={'step_free':True},vetoes=[],
                  source_note='SYNTHETIC UPDATED SOURCE',observed_at=stamp().isoformat(),reviewed=True)
        second=self.call('evaluate');self.assertNotEqual(first['snapshot_sha256'],second['snapshot_sha256'])
        self.assertEqual(second['result']['selected']['cost_per_person'],21)

    def test_expired_facts_invalidate_cached_proposal(self):
        self.prepare();self.call('evaluate')
        for c in self.app.sessions[self.sid]['candidates'].values():c['observed_at']=(stamp()-timedelta(days=2)).isoformat()
        r=self.call('evaluate');self.assertEqual(r['status'],'needs_information')

    def test_invalid_facts_and_future_timestamp_do_not_mutate(self):
        self.candidate(3);before=copy.deepcopy(self.s)
        for price,dt in [(True,stamp()),(20,stamp()+timedelta(hours=1)),(20,stamp()-timedelta(days=2))]:
            with self.assertRaises(ValueError):self.call('candidate_facts',entity_id=IDS[3],cost_per_person=price,facts={'step_free':True},vetoes=[],source_note='SYNTHETIC',observed_at=dt.isoformat(),reviewed=True)
        self.assertEqual(before,self.s)

    def test_remove_seed_invalidates_evidence_and_requires_new_review(self):
        self.prepare();self.call('evaluate')
        self.call('remove_entity',entity_id=IDS[0],participant='guest_1')
        self.assertEqual(self.call('evaluate')['reason'],'reviewed_entities_required')

    def test_single_feasible_candidate_does_not_spend_calls(self):
        for i,p in enumerate(self.s['participants']):self.seed(i,p)
        self.candidate(3)
        self.assertEqual(self.call('evaluate')['reason'],'at_least_two_feasible_options_for_comparison')
        self.assertFalse(any(c[0]=='shortlist' for c in self.provider.calls))

    def test_flat_evidence_does_not_invent_preference(self):
        self.prepare()
        with patch.object(self.provider,'shortlist',return_value={'status':'evidence_only','affinities':dict.fromkeys(IDS[3:6],.5),'live_result':False}):
            r=self.call('evaluate');self.assertEqual(r['reason'],'no_discriminating_taste_evidence');self.assertIsNone(r['proposal'])


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.app=Workflow();self.server=make_server(0,self.app)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.finish)
        self.base=f'http://127.0.0.1:{self.server.server_port}'
        self.client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with self.client.open(self.base+'/api/status',timeout=3) as r:self.status=json.load(r)

    def finish(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)

    def post(self,action,args,**headers):
        req=urllib.request.Request(self.base+'/api/tool',data=json.dumps({'action':action,'arguments':args}).encode(),
            headers={'Content-Type':'application/json','X-TasteBridge-Token':self.status['csrf'],**headers})
        with self.client.open(req,timeout=3) as r:return json.load(r)

    def test_actual_loopback_create_search_block_and_state(self):
        with patch.dict(os.environ,{},clear=True),patch('subprocess.run') as provider:
            s=self.post('create',{'participants':2,'budget':25})
            args={'session_id':s['session_id'],'revision':0,'role':'seed','query':'Dune','entity_type':'movie'}
            r=self.post('search',args);self.assertEqual(r['reason'],'credential_missing');provider.assert_not_called()
            state=self.post('state',{'session_id':s['session_id']});self.assertEqual(len(state['participants']),2)

    def test_foreign_origin_and_bad_token_rejected(self):
        for headers in [{'Origin':'https://attacker.example'},{'X-TasteBridge-Token':'wrong'}]:
            with self.assertRaises(urllib.error.HTTPError) as cm:self.post('create',{'participants':2,'budget':25},**headers)
            self.assertEqual(cm.exception.code,403)

    def test_rebinding_host_rejected(self):
        req=urllib.request.Request(self.base+'/api/status',headers={'Host':'attacker.example'})
        with self.assertRaises(urllib.error.HTTPError) as cm:self.client.open(req,timeout=3)
        self.assertEqual(cm.exception.code,403)

    def test_real_http_full_synthetic_flow(self):
        fake=SyntheticAdapter();self.app.adapter=fake
        with patch.object(self.app,'availability',return_value={'configured':True,'reason':'SYNTHETIC_TEST_ONLY'}):
            s=self.post('create',{'participants':3,'budget':25});sid=s['session_id'];rev=0
            for i in range(6):
                role='seed' if i<3 else 'candidate'
                r=self.post('search',{'session_id':sid,'revision':rev,'role':role,'query':str(i),'entity_type':'movie'})
                s=self.post('confirm_entity',{'session_id':sid,'revision':rev,'search_id':r['search_id'],'entity_id':IDS[i],
                                              'participant':f'guest_{i+1}','reviewed':True});rev=s['revision']
                if i>=3:
                    s=self.post('candidate_facts',{'session_id':sid,'revision':rev,'entity_id':IDS[i],'cost_per_person':20,
                                                   'facts':{},'vetoes':[],'source_note':'SYNTHETIC HTTP TEST',
                                                   'observed_at':stamp().isoformat(),'reviewed':True});rev=s['revision']
            result=self.post('evaluate',{'session_id':sid,'revision':rev})
            self.assertEqual(result['result']['selected']['id'],IDS[4]);self.assertFalse(result['live_result'])


if __name__=='__main__':unittest.main(verbosity=2)
  
