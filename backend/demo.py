import json
from engine import choose

PARTICIPANTS = ['guest_a', 'guest_b', 'guest_c']

def fixture():
    # Entirely fictional test data, NOT Qloo responses or real venues.
    return [
        {'id': 'majority_favourite', 'cost_per_person': 20, 'facts': {'step_free': True},
         'utilities': dict(zip(PARTICIPANTS, [.95, .95, .05]))},
        {'id': 'shared_middle_ground', 'cost_per_person': 18, 'facts': {'step_free': True},
         'utilities': dict(zip(PARTICIPANTS, [.60, .60, .60]))},
        {'id': 'unverified_access', 'cost_per_person': 12, 'facts': {},
         'utilities': dict(zip(PARTICIPANTS, [.9, .9, .9]))},
        {'id': 'too_expensive', 'cost_per_person': 80, 'facts': {'step_free': True},
         'utilities': dict(zip(PARTICIPANTS, [1, 1, 1]))},
    ]

if __name__ == '__main__':
    result = choose(PARTICIPANTS, fixture(), 25, ['step_free'])
    print(json.dumps({'mode': 'SYNTHETIC_OFFLINE_FIXTURE', 'qloo_connected': False,
                      'result': result}, indent=2))
  
