"""TasteBridge offline decision core. No Qloo or model calls in this version."""
import math
from statistics import mean


def choose(participants, candidates, budget, required_facts=()):
    """Lexicographic max-min, then mean. Utilities are caller-supplied proxies.

    Missing scores/facts cause abstention for that candidate, not guessed values.
    Hard constraints are applied before ranking. No bookings are executed.
    """
    if not participants or len(set(participants)) != len(participants):
        raise ValueError('Participants must be nonempty and unique')
    if any(not isinstance(p, str) or not p for p in participants):
        raise ValueError('Participant identifiers must be nonempty strings')
    if type(budget) not in (int, float) or not math.isfinite(budget) or budget < 0:
        raise ValueError('Budget must be finite and nonnegative')
    seen, eligible, excluded, questions = set(), [], [], []
    for item in candidates:
        cid = item['id']
        if not isinstance(cid, str) or not cid or cid in seen:
            raise ValueError('Candidate IDs must be nonempty unique strings')
        seen.add(cid)
        votes = item.get('vetoes', [])
        if not isinstance(votes, list) or any(p not in participants for p in votes):
            raise ValueError('Unknown veto participant')
        if votes:
            excluded.append({'id': cid, 'reason': 'explicit_veto', 'by': votes})
            continue
        price = item.get('cost_per_person')
        if price is None:
            questions.append({'id': cid, 'reason': 'cost_unknown'})
            continue
        if type(price) not in (int, float) or not math.isfinite(price) or price < 0:
            raise ValueError('Cost must be finite and nonnegative')
        if price > budget:
            excluded.append({'id': cid, 'reason': 'over_budget'})
            continue
        facts = item.get('facts', {})
        failed = [k for k in required_facts if facts.get(k) is False]
        missing = [k for k in required_facts if facts.get(k) is not True and facts.get(k) is not False]
        if failed:
            excluded.append({'id': cid, 'reason': 'constraint_failed', 'facts': failed})
            continue
        if missing:
            questions.append({'id': cid, 'reason': 'facts_unknown', 'facts': missing})
            continue
        scores = item.get('utilities', {})
        if any(p not in scores or scores[p] is None for p in participants):
            questions.append({'id': cid, 'reason': 'preference_evidence_missing'})
            continue
        values = [scores[p] for p in participants]
        if any(type(v) not in (float, int) or not math.isfinite(v) or not 0 <= v <= 1 for v in values):
            raise ValueError('Utilities must be finite numbers between zero and one')
        eligible.append({'id': cid, 'minimum_proxy': min(values), 'mean_proxy': mean(values),
                         'utilities': {p: scores[p] for p in participants}, 'cost_per_person': price})
    eligible.sort(key=lambda x: (-x['minimum_proxy'], -x['mean_proxy'], x['id']))
    baseline = sorted(eligible, key=lambda x: (-x['mean_proxy'], x['id']))
    chosen = eligible[0] if eligible else None
    return {'status': 'proposal' if chosen else ('needs_information' if questions else 'no_feasible_option'),
            'selected': chosen, 'mean_only_baseline': baseline[0] if baseline else None,
            'alternatives': eligible[1:], 'excluded': excluded, 'questions': questions,
            'requires_group_confirmation': bool(chosen),
            'scope': 'one shared activity; no itinerary scheduling or bookings',
            'limitation': 'Utility proxies are not satisfaction probabilities or verified real-world facts.'}
