import copy
import unittest
from engine import choose
from demo import PARTICIPANTS as P, fixture


class DecisionTests(unittest.TestCase):
    def test_minority_tradeoff_against_mean_baseline(self):
        r = choose(P, fixture(), 25, ['step_free'])
        self.assertEqual(r['selected']['id'], 'shared_middle_ground')
        self.assertEqual(r['mean_only_baseline']['id'], 'majority_favourite')
        self.assertGreater(r['selected']['minimum_proxy'], r['mean_only_baseline']['minimum_proxy'])
        self.assertLess(r['selected']['mean_proxy'], r['mean_only_baseline']['mean_proxy'])

    def test_veto_dominates_scores(self):
        c = fixture()[1]; c['vetoes'] = ['guest_c']
        r = choose(P, [c], 25)
        self.assertIsNone(r['selected'])
        self.assertEqual(r['excluded'][0]['reason'], 'explicit_veto')

    def test_unknown_access_cannot_be_inferred_from_taste(self):
        r = choose(P, [fixture()[2]], 25, ['step_free'])
        self.assertEqual(r['status'], 'needs_information')
        self.assertIsNone(r['selected'])

    def test_known_constraint_failure(self):
        c = fixture()[0]; c['facts']['step_free'] = False
        self.assertEqual(choose(P, [c], 25, ['step_free'])['status'], 'no_feasible_option')

    def test_missing_score_abstains(self):
        c = fixture()[0]; del c['utilities']['guest_c']
        self.assertEqual(choose(P, [c], 25)['status'], 'needs_information')

    def test_invalid_scores_rejected(self):
        for invalid in (True, -1, 1.1, float('nan'), float('inf'), '0.5'):
            with self.subTest(value=invalid):
                c = fixture()[0]; c['utilities']['guest_c'] = invalid
                with self.assertRaises(ValueError): choose(P, [c], 25)

    def test_budget_boundary_and_unknown_cost(self):
        c = fixture()[0]
        self.assertIsNotNone(choose(P, [c], 20)['selected'])
        self.assertIsNone(choose(P, [c], 19.99)['selected'])
        c['cost_per_person'] = None
        self.assertEqual(choose(P, [c], 25)['status'], 'needs_information')

    def test_order_independent_does_not_mutate(self):
        c = fixture(); original = copy.deepcopy(c)
        self.assertEqual(choose(P, c, 25), choose(list(reversed(P)), list(reversed(c)), 25))
        self.assertEqual(c, original)

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError): choose(P + [P[0]], fixture(), 25)
        with self.assertRaises(ValueError): choose(P, [fixture()[0], fixture()[0]], 25)

    def test_invalid_budget_and_unknown_veto(self):
        for b in (True, -1, float('nan')):
            with self.assertRaises(ValueError): choose(P, fixture(), b)
        c = fixture()[0]; c['vetoes'] = ['stranger']
        with self.assertRaises(ValueError): choose(P, [c], 25)

    def test_empty_candidates_and_confirmation(self):
        self.assertEqual(choose(P, [], 25)['status'], 'no_feasible_option')
        self.assertTrue(choose(P, fixture(), 25)['requires_group_confirmation'])

if __name__ == '__main__': unittest.main()
