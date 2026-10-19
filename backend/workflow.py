"""Bounded local workflow. Model-readable tools, explicit reviews, no bookings."""
import copy
import hashlib
import json
import math
import os
import secrets
from datetime import datetime, timezone

from engine import choose
from qloo_adapter import QlooAdapter
from qloo_http import QlooHTTPAdapter


def stamp():
    return datetime.now(timezone.utc)


def finite(value, low, high):
    return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


def ordinal(scores):
    """Midrank of each option within ONE complete shared shortlist. Not utility."""
    n = len(scores)
    if not n or any(not finite(v, -1e100, 1e100) for v in scores.values()):
        raise ValueError('Invalid affinity evidence')
    if n == 1:
        return {key: 0.5 for key in scores}
    return {key: (sum(v < score for v in scores.values()) +
                  0.5 * (sum(v == score for v in scores.values()) - 1)) / (n - 1)
            for key, score in scores.items()}


class Workflow:
    def __init__(self, adapter=None):
        # One adapter/call cap for the process, not a new budget per web request.
        self.adapter = adapter or QlooHTTPAdapter(max_calls=20)
        self.sessions = {}

    def availability(self):
        enabled = os.environ.get('QLOO_EVENT_ACCESS_CONFIRMED') == '1'
        key = bool(os.environ.get('QLOO_API_KEY'))
        return {'configured': enabled and key, 'credential_present': key,
                'event_free_access_confirmed': enabled,
                'remaining_process_calls': self.adapter.remaining,
                'authentication_verified': False,
                'reason': 'ready_for_bounded_attempt' if enabled and key else
                          ('credential_missing' if not key else 'event_access_not_confirmed')}

    def _provider(self, method, *args, **kwargs):
        ready = self.availability()
        if not ready['configured']:
            return {'status': 'blocked', 'reason': ready['reason'], 'live_result': False}
        return getattr(self.adapter, method)(*args, **kwargs)

    def _session(self, sid):
        s = self.sessions.get(sid)
        if s is None or (stamp() - s['created']).total_seconds() > 1200:
            raise ValueError('Session expired or unknown')
        return s

    def _touch(self, s):
        s['revision'] += 1
        s['cache'] = None

    def _snapshot(self, s):
        return {'revision': s['revision'], 'participants': copy.deepcopy(s['participants']),
                'candidates': copy.deepcopy(s['candidates']), 'budget': s['budget'],
                'required_facts': s['required_facts'], 'provider': self.availability(),
                'scope': 'One shared activity; no bookings or personal identity verification'}

    def call(self, action, data):
        if not isinstance(data, dict):
            raise ValueError('Object required')
        if action == 'create':
            count, budget = data.get('participants'), data.get('budget')
            if type(count) is not int or not 2 <= count <= 6 or not finite(budget, 0, 10000):
                raise ValueError('Use 2–6 guests and a finite per-person budget')
            required = data.get('required_facts', [])
            if required not in ([], ['step_free']):
                raise ValueError('Unsupported required facts')
            self.sessions = {k:v for k,v in self.sessions.items() if (stamp()-v['created']).total_seconds() <= 1200}
            if len(self.sessions) >= 8:
                raise ValueError('Local session capacity reached')
            sid = secrets.token_urlsafe(24)
            s = {'created': stamp(), 'revision': 0, 'budget': budget, 'required_facts': required,
                 'participants': {f'guest_{i+1}': [] for i in range(count)},
                 'candidates': {}, 'searches': {}, 'cache': None}
            self.sessions[sid] = s
            return {'session_id': sid, **self._snapshot(s)}
        s = self._session(data.get('session_id'))
        if action == 'state':
            return self._snapshot(s)
        if data.get('revision') != s['revision'] or type(data.get('revision')) is not int:
            raise ValueError('Stale revision: reload before changing or evaluating')
        if action == 'search':
            role = data.get('role')
            if role not in ('seed', 'candidate'):
                raise ValueError('Unknown search role')
            kind = 'place' if role == 'candidate' else data.get('entity_type')
            result = self._provider('search', data.get('query'), kind)
            if result['status'] == 'needs_entity_review':
                search_id = secrets.token_urlsafe(16)
                if len(s['searches']) >= 20:
                    s['searches'].pop(next(iter(s['searches'])))
                s['searches'][search_id] = {'role': role, 'matches': copy.deepcopy(result['matches'])}
                result = {**result, 'search_id': search_id}
            return result
        if action == 'confirm_entity':
            search = s['searches'].get(data.get('search_id'))
            if not search or data.get('reviewed') is not True:
                raise ValueError('An explicit review of returned search results is required')
            entity = next((e for e in search['matches'] if e['entity_id'] == data.get('entity_id')), None)
            if entity is None:
                raise ValueError('Entity was not returned by this search')
            if search['role'] == 'seed':
                participant = data.get('participant')
                if participant not in s['participants']:
                    raise ValueError('Unknown guest')
                seeds = s['participants'][participant]
                if entity not in seeds:
                    if len(seeds) >= 3:
                        raise ValueError('At most three reviewed seeds per guest')
                    seeds.append(copy.deepcopy(entity))
            else:
                eid = entity['entity_id']
                if eid not in s['candidates']:
                    if len(s['candidates']) >= 5:
                        raise ValueError('At most five reviewed places')
                    s['candidates'][eid] = {**copy.deepcopy(entity), 'cost_per_person': None,
                                            'facts': {}, 'vetoes': [], 'source_note': '', 'observed_at': None}
            self._touch(s)
            return self._snapshot(s)
        if action == 'candidate_facts':
            item = s['candidates'].get(data.get('entity_id'))
            price, facts, vetoes = data.get('cost_per_person'), data.get('facts'), data.get('vetoes', [])
            source = data.get('source_note')
            if item is None or data.get('reviewed') is not True:
                raise ValueError('Review a current candidate first')
            if not finite(price, 0, 10000) or not isinstance(facts, dict) or set(facts)-{'step_free'}:
                raise ValueError('Invalid price or facts')
            if any(v is not True and v is not False and v is not None for v in facts.values()):
                raise ValueError('Facts must be true, false or unknown')
            if not isinstance(vetoes, list) or any(v not in s['participants'] for v in vetoes) or len(set(vetoes)) != len(vetoes):
                raise ValueError('Invalid veto guest')
            if not isinstance(source, str) or not 3 <= len(source) <= 400 or any(ord(c)<32 for c in source):
                raise ValueError('Record the public source or explicit host confirmation')
            try:
                observed = datetime.fromisoformat(data['observed_at'])
                age = (stamp()-observed).total_seconds()
                if observed.tzinfo is None or not 0 <= age <= 86400:
                    raise ValueError()
            except (KeyError, TypeError, ValueError):
                raise ValueError('Facts need a timezone-aware observation within the last 24 hours')
            item.update(cost_per_person=price, facts=copy.deepcopy(facts), vetoes=list(vetoes),
                        source_note=source, observed_at=observed.isoformat())
            self._touch(s)
            return self._snapshot(s)
        if action == 'remove_entity':
            eid, participant = data.get('entity_id'), data.get('participant')
            if participant is None:
                if eid not in s['candidates']:
                    raise ValueError('Unknown candidate')
                del s['candidates'][eid]
            else:
                if participant not in s['participants'] or not any(e['entity_id']==eid for e in s['participants'][participant]):
                    raise ValueError('Unknown guest seed')
                s['participants'][participant] = [e for e in s['participants'][participant] if e['entity_id']!=eid]
            self._touch(s)
            return self._snapshot(s)
        if action == 'evaluate':
            return self.evaluate(s)
        raise ValueError('Unknown tool action')

    def evaluate(self, s):
        if s['cache'] is not None:
            if s['cache'].get('status') == 'proposal' and any(
                c['observed_at'] and (stamp()-datetime.fromisoformat(c['observed_at'])).total_seconds() > 86400
                for c in s['candidates'].values()
            ):
                s['cache'] = None
            else:
                return copy.deepcopy(s['cache'])
        participants = list(s['participants'])
        missing = [p for p, seeds in s['participants'].items() if not seeds]
        if missing or not s['candidates']:
            return {'status': 'needs_information', 'reason': 'reviewed_entities_required',
                    'guests_missing_seeds': missing, 'live_result': False}
        candidates = []
        for eid, c in s['candidates'].items():
            current = c['observed_at'] and 0 <= (stamp()-datetime.fromisoformat(c['observed_at'])).total_seconds() <= 86400
            candidates.append({'id': eid, 'cost_per_person': c['cost_per_person'] if current else None,
                               'facts': c['facts'] if current else {}, 'vetoes': c['vetoes'],
                               'utilities': {p:0.5 for p in participants}})
        # Temporary equal ranks are ONLY used to apply the original hard constraints.
        admission = choose(participants, candidates, s['budget'], s['required_facts'])
        admitted = ([admission['selected']] if admission['selected'] else []) + admission['alternatives']
        ids = sorted(c['id'] for c in admitted)
        if not ids:
            return {'status': admission['status'], 'reason': 'no_current_feasible_candidates',
                    'excluded': admission['excluded'], 'questions': admission['questions'], 'live_result': False}
        if len(ids) < 2:
            return {'status':'needs_information','reason':'at_least_two_feasible_options_for_comparison',
                    'excluded':admission['excluded'],'questions':admission['questions'],'live_result':False}
        evidence = {}
        for participant in participants:
            result = self._provider('shortlist', [v['entity_id'] for v in s['participants'][participant]],
                                    ids, 'place', entity_choices_confirmed=True)
            if result['status'] != 'evidence_only' or set(result.get('affinities', {})) != set(ids):
                blocked = {'status': 'blocked', 'reason': result.get('reason', 'complete_affinity_evidence_required'),
                           'participant': participant, 'live_result': False, 'proposal': None,
                           'revision': s['revision'], 'automatic_retry': False}
                s['cache'] = blocked
                return copy.deepcopy(blocked)
            evidence[participant] = result
            if len(set(result['affinities'].values())) < 2:
                s['cache'] = {'status':'needs_information','reason':'no_discriminating_taste_evidence',
                              'participant':participant,'proposal':None,'live_result':False,'automatic_retry':False}
                return copy.deepcopy(s['cache'])
        if any((stamp()-datetime.fromisoformat(s['candidates'][eid]['observed_at'])).total_seconds()>86400 for eid in ids):
            return {'status':'needs_information', 'reason':'facts_expired_during_query', 'live_result':False}
        ranks = {p: ordinal(r['affinities']) for p, r in evidence.items()}
        active = [dict(c, utilities={p:ranks[p][c['id']] for p in participants})
                  for c in candidates if c['id'] in ids]
        result = choose(participants, active, s['budget'], s['required_facts'])
        result['excluded'] = admission['excluded']
        result['questions'] = admission['questions']
        result['limitation'] = 'Midranks are a declared decision policy, not comparable raw affinities, satisfaction or probabilities. Rankings depend on the reviewed shortlist.'
        fingerprint = hashlib.sha256(json.dumps({'revision':s['revision'], 'seeds':s['participants'],
                                                 'candidates':s['candidates'], 'budget':s['budget'],
                                                 'required_facts':s['required_facts']},sort_keys=True).encode()).hexdigest()
        out = {'status': 'proposal', 'revision':s['revision'], 'snapshot_sha256':fingerprint,
               'live_result': all(r.get('live_result') is True for r in evidence.values()),
               'provider_evidence':evidence, 'rank_policy':'within-query midrank on identical feasible shortlist',
               'result':result, 'facts_provenance':'USER_REPORTED_NOT_INDEPENDENTLY_VERIFIED',
               'tied_top_ids':[c['id'] for c in [result['selected']]+result['alternatives']
                               if c['minimum_proxy']==result['selected']['minimum_proxy'] and c['mean_proxy']==result['selected']['mean_proxy']],
               'requires_group_confirmation':True, 'booking_performed':False}
        s['cache'] = copy.deepcopy(out)
        return out
