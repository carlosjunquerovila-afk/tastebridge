import io
import json
import os
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.parse import urlsplit, parse_qs
from qloo_http import QlooHTTPAdapter, NoRedirect, LIMIT

A='11111111-1111-4111-8111-111111111111'
B='22222222-2222-4222-8222-222222222222'
KEY='FAKE_TEST_CREDENTIAL'

class Response(io.BytesIO):
    status=200

@patch.dict(os.environ,{'QLOO_API_KEY':KEY,'QLOO_EVENT_ACCESS_CONFIRMED':'1'})
class TransportTests(unittest.TestCase):
    def adapter(self,payload):
        opener=Mock()
        raw=payload if isinstance(payload,bytes) else json.dumps(payload).encode()
        opener.open.return_value=Response(raw)
        return QlooHTTPAdapter(opener=opener),opener

    def test_search_exact_origin_parameters_and_provenance(self):
        a,o=self.adapter({'results':[{'entity_id':A,'name':'Example'}]})
        r=a.search('Public book','book')
        req=o.open.call_args.args[0]
        self.assertEqual(urlsplit(req.full_url).netloc,'hackathon.api.qloo.com')
        self.assertEqual(parse_qs(urlsplit(req.full_url).query),{'query':['Public book'],'types':['urn:entity:book'],'take':['3']})
        self.assertNotIn(KEY,req.full_url)
        self.assertEqual(r['status'],'needs_entity_review')
        self.assertEqual(len(r['response_sha256']),64)
        self.assertNotIn(KEY,json.dumps(r))

    def test_shortlist_uses_same_ids_and_never_utilities(self):
        a,o=self.adapter({'results':{'entities':[{'entity_id':B,'query':{'affinity':0.8}}]}})
        r=a.shortlist([A],[B],'place',entity_choices_confirmed=True)
        self.assertEqual(r['affinities'],{B:0.8})
        self.assertEqual(r['request']['parameters']['filter.results.entities'],B)
        self.assertFalse(r['utility_conversion_performed'])

    def test_http_failures_redacted_no_retry(self):
        for code,reason in [(401,'authentication_failed'),(403,'access_denied'),(404,'entity_not_found'),(429,'rate_limited'),(500,'provider_error'),(302,'redirect_rejected')]:
            with self.subTest(code=code):
                a,o=self.adapter({})
                o.open.side_effect=HTTPError('https://hackathon.api.qloo.com',code,KEY,{},None)
                r=a.search('Example','book')
                self.assertEqual(r['reason'],reason)
                self.assertEqual(o.open.call_count,1)
                self.assertNotIn(KEY,json.dumps(r))

    def test_missing_access_does_not_spend_budget(self):
        for env in [{'QLOO_API_KEY':''},{'QLOO_EVENT_ACCESS_CONFIRMED':'0'}]:
            a,o=self.adapter({})
            with patch.dict(os.environ,env): self.assertEqual(a.search('Example','book')['status'],'blocked')
            o.open.assert_not_called()
            self.assertEqual(a.remaining,20)

    def test_bad_shapes_and_secret_echo(self):
        for payload in [b'not json',{},[],{'results':{}},{'error':True,'results':[]}, {'results':[{'entity_id':A,'name':KEY}]}]:
            a,o=self.adapter(payload)
            r=a.search('Example','book')
            self.assertEqual(r['status'],'blocked')
            self.assertNotIn(KEY,json.dumps(r))

    def test_oversized_read_and_timeout(self):
        a,o=self.adapter(b'x'*(LIMIT+1))
        self.assertEqual(a.search('Example','book')['reason'],'response_too_large')
        a,o=self.adapter({});o.open.side_effect=TimeoutError(KEY)
        self.assertEqual(a.search('Example','book')['reason'],'timeout')

    def test_budget_includes_failed_attempts(self):
        a,o=self.adapter({});a.remaining=1;o.open.side_effect=TimeoutError()
        a.search('Example','book')
        self.assertEqual(a.search('Example','book')['reason'],'call_cap')
        self.assertEqual(o.open.call_count,1)

    def test_redirect_handler_refuses_forwarding(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,'Found',{},'https://wrong.invalid'))

if __name__=='__main__':unittest.main()
  
