import json
import os
import subprocess
import unittest
from unittest.mock import patch
from qloo_adapter import QlooAdapter, search_plan, shortlist_plan

A='11111111-1111-4111-8111-111111111111'
B='22222222-2222-4222-8222-222222222222'
C='33333333-3333-4333-8333-333333333333'


class AdapterTests(unittest.TestCase):
    def receive(self, entities):
        return patch.object(QlooAdapter, '_run', return_value={
            'status':'evidence_received', 'entities':entities, 'live_result':True})

    def test_missing_key_stops_before_execution(self):
        with patch.dict(os.environ, {}, clear=True), patch('subprocess.run') as run:
            self.assertEqual(QlooAdapter().search('Agatha Christie','book')['reason'],'credential_missing')
            run.assert_not_called()

    def test_unreviewed_seeds_never_call(self):
        with patch.object(QlooAdapter,'_run') as run:
            self.assertEqual(QlooAdapter().shortlist([A],[B],'place')['reason'],'entity_review_required')
            run.assert_not_called()

    def test_plans_are_bounded_and_use_ids(self):
        args=search_plan('Public title; $(false)','book')
        self.assertIn('Public title; $(false)',args)
        self.assertNotIn('--api-key',args)
        args=shortlist_plan([A],[B,C],'place')
        self.assertEqual(json.loads(args[args.index('--params')+1]),{'filter.results.entities':B+','+C})
        self.assertNotIn('--signal-query',args)

    def test_invalid_plans(self):
        for query,kind,take in [('', 'book',3),('x\n','book',3),('x','person',3),('x','book',True),('x','book',11)]:
            with self.subTest(query=query,kind=kind,take=take),self.assertRaises(ValueError):
                search_plan(query,kind,take)
        for ids in [[B,B],[],['--api-key'],[None],[B.upper(),B]]:
            with self.subTest(ids=ids),self.assertRaises(ValueError):
                shortlist_plan([A],ids,'place')

    def test_search_requires_review_and_handles_empty(self):
        with self.receive([{'entity_id':A,'name':'Candidate'}]):
            result=QlooAdapter().search('Candidate','book')
            self.assertEqual(result['status'],'needs_entity_review')
            self.assertFalse(result['automatic_selection'])
        with self.receive([]):
            self.assertEqual(QlooAdapter().search('Absent','book')['status'],'no_match')

    def test_complete_evidence_does_not_create_utilities(self):
        with self.receive([{'entity_id':B,'query':{'affinity':0.7}},{'entity_id':C,'affinity':0.2}]):
            result=QlooAdapter().shortlist([A],[B,C],'place',entity_choices_confirmed=True)
            self.assertEqual(result['status'],'evidence_only')
            self.assertEqual(result['affinities'],{B:0.7,C:0.2})
            self.assertFalse(result['cross_query_comparability_established'])
            self.assertFalse(result['utility_conversion_performed'])
            self.assertFalse(result['operational_facts_verified'])

    def test_missing_candidate_requires_information(self):
        with self.receive([{'entity_id':B,'affinity':0.7}]):
            result=QlooAdapter().shortlist([A],[B,C],'place',entity_choices_confirmed=True)
            self.assertEqual(result['status'],'needs_information')
            self.assertEqual(result['missing_entities'],[C])

    def test_adversarial_provider_shapes(self):
        for entities in [[{'entity_id':A,'affinity':0.5}], [{'entity_id':B,'affinity':0.5}]*2,
                         [{'entity_id':B,'affinity':float('nan')}], [{'entity_id':B,'affinity':True}],
                         [{'entity_id':B,'query':None}], [None], [{'entity_id':B}]]:
            with self.subTest(entities=entities),self.receive(entities):
                result=QlooAdapter().shortlist([A],[B],'place',entity_choices_confirmed=True)
                self.assertEqual(result['reason'],'invalid_schema')

    @patch.dict(os.environ, {'QLOO_API_KEY':'SYNTHETIC_TEST_ONLY'})
    def test_process_boundary_and_call_cap(self):
        def command(args,**kwargs):
            self.assertFalse(kwargs['shell'])
            self.assertNotIn('SYNTHETIC_TEST_ONLY',args)
            kwargs['stdout'].write(json.dumps([{'entity_id':A,'name':'Candidate'}]).encode())
            return subprocess.CompletedProcess(args,0)
        with patch('subprocess.run',side_effect=command) as run:
            adapter=QlooAdapter(max_calls=1)
            self.assertEqual(adapter.search('Candidate','book')['status'],'needs_entity_review')
            self.assertEqual(adapter.search('Candidate','book')['reason'],'call_cap')
            self.assertEqual(run.call_count,1)

    @patch.dict(os.environ, {'QLOO_API_KEY':'SYNTHETIC_TEST_ONLY'})
    def test_failures_are_single_attempt_and_redacted(self):
        for code in [3,4,5]:
            def command(args,**kwargs):
                kwargs['stdout'].write(b'{"error":true,"message":"SYNTHETIC_TEST_ONLY"}')
                kwargs['stderr'].write(b'SYNTHETIC_TEST_ONLY')
                return subprocess.CompletedProcess(args,code)
            with self.subTest(code=code),patch('subprocess.run',side_effect=command) as run:
                result=QlooAdapter().search('Candidate','book')
                self.assertEqual(result['status'],'blocked')
                self.assertNotIn('SYNTHETIC_TEST_ONLY',json.dumps(result))
                self.assertEqual(run.call_count,1)

    @patch.dict(os.environ, {'QLOO_API_KEY':'SYNTHETIC_TEST_ONLY'})
    def test_timeout_is_terminal_for_attempt(self):
        with patch('subprocess.run',side_effect=subprocess.TimeoutExpired('qloo',20)) as run:
            self.assertEqual(QlooAdapter().search('Candidate','book')['reason'],'timeout')
            self.assertEqual(run.call_count,1)

    @patch.dict(os.environ, {'QLOO_API_KEY':'SYNTHETIC_TEST_ONLY'})
    def test_malformed_and_oversized_output(self):
        for data in [b'not JSON',b'{}',b'x'*2_000_001]:
            def command(args,**kwargs):
                kwargs['stdout'].write(data)
                return subprocess.CompletedProcess(args,0)
            with self.subTest(size=len(data)),patch('subprocess.run',side_effect=command):
                self.assertEqual(QlooAdapter().search('Candidate','book')['status'],'blocked')


if __name__=='__main__':
    unittest.main(verbosity=2)
  
