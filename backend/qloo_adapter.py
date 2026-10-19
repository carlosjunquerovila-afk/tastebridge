"""Server-only Qloo evidence adapter; never supplies synthetic fallback scores.

Uses the official @qloo/qloo-harness 0.1.26 CLI. Does not call a model,
approve a participant's entity choice, book, or convert affinities to utilities.
"""
import json
import math
import os
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone


TYPES = {'book', 'movie', 'artist', 'place', 'podcast', 'tv_show'}


def _ids(values, maximum):
    if not isinstance(values, list) or not 1 <= len(values) <= maximum:
        raise ValueError('Expected a bounded nonempty entity list')
    if any(not isinstance(v, str) or str(uuid.UUID(v)) != v.lower() for v in values):
        raise ValueError('Entity IDs must be canonical UUIDs')
    result = [v.lower() for v in values]
    if len(set(result)) != len(result):
        raise ValueError('Repeated entity IDs')
    return result


def search_plan(query, entity_type, take=3):
    if entity_type not in TYPES or type(take) is not int or not 1 <= take <= 10:
        raise ValueError('Unsupported entity type or result limit')
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 120 or any(ord(c) < 32 for c in query):
        raise ValueError('Expected a short public cultural entity name')
    return ['api', 'search', '--query', query.strip(), '--type', entity_type,
            '--take', str(take), '--json']


def shortlist_plan(reviewed_seeds, candidate_ids, entity_type):
    if entity_type not in TYPES:
        raise ValueError('Unsupported entity type')
    seeds, candidates = _ids(reviewed_seeds, 5), _ids(candidate_ids, 10)
    return ['api', 'insights', '--type', entity_type,
            '--signal-entities', ','.join(seeds), '--take', str(len(candidates)),
            '--params', json.dumps({'filter.results.entities': ','.join(candidates)}, separators=(',', ':')),
            '--json']


class QlooAdapter:
    def __init__(self, executable='qloo', *, max_calls=6, timeout=20):
        if type(max_calls) is not int or not 1 <= max_calls <= 20:
            raise ValueError('Call cap must be between 1 and 20')
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 1 <= timeout <= 60:
            raise ValueError('Timeout must be between 1 and 60 seconds')
        self.executable, self.remaining, self.timeout = executable, max_calls, timeout

    def _run(self, arguments):
        api_key = os.environ.get('QLOO_API_KEY', '')
        if not api_key.strip():
            return {'status': 'blocked', 'reason': 'credential_missing', 'live_result': False}
        if self.remaining <= 0:
            return {'status': 'blocked', 'reason': 'call_cap', 'live_result': False}
        self.remaining -= 1
        # Temporary files avoid unbounded in-memory capture; timeout bounds a stalled request.
        # No shell, retries, API-key argument, model calls, or raw error exposure.
        try:
            with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
                # Only this exact event origin may receive the event credential.
                # Do not inherit model keys, NODE_OPTIONS or an unrelated base URL.
                child_env = {k: os.environ[k] for k in ('PATH', 'HOME', 'SYSTEMROOT', 'TMPDIR') if k in os.environ}
                child_env.update(QLOO_API_KEY=api_key,
                                 QLOO_BASE_URL='https://hackathon.api.qloo.com',
                                 QLOO_TRUSTED_BASE_URL='https://hackathon.api.qloo.com')
                process = subprocess.run([self.executable, *arguments], stdout=output, stderr=errors,
                                         timeout=self.timeout, check=False, shell=False, env=child_env)
                size = output.tell()
                if process.returncode:
                    return {'status': 'blocked', 'reason': {3: 'authentication_failed', 4: 'entity_not_found'}.get(process.returncode, 'provider_error'), 'live_result': False}
                if size > 2_000_000:
                    return {'status': 'blocked', 'reason': 'response_too_large', 'live_result': False}
                output.seek(0)
                raw = output.read()
                if api_key.encode() in raw:
                    return {'status': 'blocked', 'reason': 'unsafe_response', 'live_result': False}
                entities = json.loads(raw)
                # Also reject JSON-escaped echoes before any value reaches the UI.
                if api_key in json.dumps(entities, ensure_ascii=False):
                    return {'status': 'blocked', 'reason': 'unsafe_response', 'live_result': False}
        except subprocess.TimeoutExpired:
            return {'status': 'blocked', 'reason': 'timeout', 'live_result': False}
        except (OSError, ValueError):
            return {'status': 'blocked', 'reason': 'invalid_or_unavailable_response', 'live_result': False}
        if not isinstance(entities, list) or len(entities) > 10:
            return {'status': 'blocked', 'reason': 'invalid_schema', 'live_result': False}
        return {'status': 'evidence_received', 'entities': entities,
                'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'provider': 'Qloo via official CLI', 'live_result': True}

    def search(self, public_name, entity_type):
        result = self._run(search_plan(public_name, entity_type))
        if result['status'] != 'evidence_received':
            return result
        try:
            items = []
            for item in result.pop('entities'):
                eid = _ids([item['entity_id']], 1)[0]
                if not isinstance(item['name'], str) or not 1 <= len(item['name']) <= 500:
                    raise ValueError('Invalid name')
                items.append({'entity_id': eid, 'name': item['name']})
            if len({i['entity_id'] for i in items}) != len(items):
                raise ValueError('Duplicate entities')
        except (KeyError, TypeError, ValueError, AttributeError):
            return {'status': 'blocked', 'reason': 'invalid_schema', 'live_result': False}
        return {**result, 'status': 'needs_entity_review' if items else 'no_match',
                'matches': items, 'automatic_selection': False}

    def shortlist(self, reviewed_seeds, candidate_ids, entity_type, *, entity_choices_confirmed=False):
        arguments = shortlist_plan(reviewed_seeds, candidate_ids, entity_type)
        candidates = _ids(candidate_ids, 10)
        if entity_choices_confirmed is not True:
            return {'status': 'blocked', 'reason': 'entity_review_required', 'live_result': False}
        result = self._run(arguments)
        if result['status'] != 'evidence_received':
            return result
        evidence = {}
        try:
            for item in result.pop('entities'):
                eid = _ids([item['entity_id']], 1)[0]
                if eid not in candidates or eid in evidence:
                    raise ValueError('Unexpected or repeated entity')
                affinity = item.get('affinity', item.get('query', {}).get('affinity'))
                if type(affinity) not in (int, float) or not math.isfinite(affinity):
                    raise ValueError('Invalid affinity')
                evidence[eid] = affinity
        except (KeyError, TypeError, ValueError, AttributeError):
            return {'status': 'blocked', 'reason': 'invalid_schema', 'live_result': False}
        missing = [eid for eid in candidates if eid not in evidence]
        return {**result, 'status': 'needs_information' if missing else 'evidence_only',
                'candidate_ids': candidates, 'reviewed_seed_ids': _ids(reviewed_seeds, 5),
                'affinities': evidence, 'missing_entities': missing,
                'cross_query_comparability_established': False,
                'utility_conversion_performed': False,
                'operational_facts_verified': False, 'group_confirmation_required': True}
