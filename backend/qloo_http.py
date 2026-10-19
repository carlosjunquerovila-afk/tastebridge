"""Bounded direct Qloo transport. No redirects, retries or fixture fallback.

Request parameters match the official harness 0.1.26 api search/insights.
The shared superclass validates entities and affinities after transport.
"""
import hashlib
import json
import os
import socket
import threading
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from qloo_adapter import QlooAdapter

ORIGIN = 'https://hackathon.api.qloo.com'
LIMIT = 2_000_000

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class QlooHTTPAdapter(QlooAdapter):
    def __init__(self, *, max_calls=20, timeout=20, opener=None):
        super().__init__(max_calls=max_calls, timeout=timeout)
        self.opener = opener or build_opener(ProxyHandler({}), NoRedirect())
        self.lock = threading.Lock()

    def _run(self, arguments):
        key = os.environ.get('QLOO_API_KEY', '')
        if not key.strip():
            return self.block('credential_missing')
        if os.environ.get('QLOO_EVENT_ACCESS_CONFIRMED') != '1':
            return self.block('event_access_not_confirmed')
        # Plans are produced by the inherited validated search/shortlist methods.
        def flag(name):
            return arguments[arguments.index(name)+1]
        kind = flag('--type')
        if arguments[:2] == ['api', 'search']:
            endpoint = '/search'
            params = {'query':flag('--query'), 'types':'urn:entity:'+kind, 'take':flag('--take')}
        elif arguments[:2] == ['api', 'insights']:
            endpoint = '/v2/insights'
            params = {'filter.type':'urn:entity:'+kind,
                      'signal.interests.entities':flag('--signal-entities'),
                      'filter.results.entities':json.loads(flag('--params'))['filter.results.entities'],
                      'take':flag('--take')}
        else:
            return self.block('invalid_request')
        with self.lock:
            if self.remaining <= 0:
                return self.block('call_cap')
            self.remaining -= 1
            request = Request(ORIGIN+endpoint+'?'+urlencode(params),
                              headers={'X-Api-Key':key, 'Accept':'application/json'})
            try:
                with self.opener.open(request, timeout=self.timeout) as response:
                    if response.status != 200:
                        return self.http_failure(response.status)
                    raw = response.read(LIMIT+1)
                if len(raw)>LIMIT:
                    return self.block('response_too_large')
                if key.encode() in raw:
                    return self.block('unsafe_response')
                payload=json.loads(raw)
                if key in json.dumps(payload, ensure_ascii=False):
                    return self.block('unsafe_response')
                if not isinstance(payload,dict) or payload.get('error'):
                    return self.block('invalid_schema')
                results=payload.get('results')
                entities=results if endpoint=='/search' else results.get('entities') if isinstance(results,dict) else None
                if not isinstance(entities,list) or len(entities)>10:
                    return self.block('invalid_schema')
            except HTTPError as error:
                error.close()
                return self.http_failure(error.code)
            except (TimeoutError, socket.timeout):
                return self.block('timeout')
            except URLError as error:
                return self.block('timeout' if isinstance(error.reason,TimeoutError) else 'network_failure')
            except (ValueError, OSError, UnicodeError):
                return self.block('invalid_or_unavailable_response')
        return {'status':'evidence_received','entities':entities,'provider':'Qloo HTTPS API',
                'retrieved_at':datetime.now(timezone.utc).isoformat(),'live_result':True,
                'request':{'origin':ORIGIN,'endpoint':endpoint,'parameters':params},
                'response_sha256':hashlib.sha256(raw).hexdigest()}

    @staticmethod
    def block(reason):
        return {'status':'blocked','reason':reason,'live_result':False}

    def http_failure(self, code):
        reason={401:'authentication_failed',403:'access_denied',404:'entity_not_found',
                429:'rate_limited'}.get(code,'redirect_rejected' if 300<=code<400 else 'provider_error')
        return {**self.block(reason),'http_status':code}
