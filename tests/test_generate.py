import unittest
import sys
import os
from typing import List
from collections import Counter

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from nt_lotto.nt_core.generate import (
    propose_combo_candidates,
    select_portfolio,
    run_global_qa,
    _calculate_macro_stats,
    QUOTA,
    ComboCandidate,
    QAReport
)

class TestGenerate(unittest.TestCase):
    def setUp(self):
        # Mock pool of 22 numbers
        self.mock_pool = list(range(1, 23)) # 1 to 22
        
    def test_macro_stats(self):
        # 1,2,3,4,5,6
        stats = _calculate_macro_stats([1,2,3,4,5,6])
        self.assertEqual(stats['sum'], 21)
        self.assertEqual(stats['odd'], 3) # 1,3,5
        self.assertEqual(stats['max_run'], 6)
        
    def test_propose_candidates(self):
        # Should generate C(22,6) combos, filtered
        candidates = propose_combo_candidates(
            engine_id="TEST",
            pool=self.mock_pool,
            engine_topk={},
            ssot_sorted_df=None,
            features_cache=None,
            limit=100
        )
        self.assertGreater(len(candidates), 0)
        self.assertLessEqual(len(candidates), 100)
        # Check structure
        self.assertIsInstance(candidates[0], ComboCandidate)
        self.assertEqual(len(candidates[0].numbers), 6)
        
    def test_select_portfolio_strict_quota(self):
        # Generate enough candidates for all engines
        candidates_by_engine = {}
        for eng, count in QUOTA.items():
            # Generate dummy candidates
            # We need them to be non-overlapping enough to pick 50
            # With pool of 22, overlap 2 is hard.
            # Let's use a larger pool for this test to ensure it passes selection logic
            # or rely on the logic finding a valid subset if possible.
            # Actually, standard pool is 22. If logic is robust, it attempts.
            # If it fails to find 50, it reports size < 50.
            
            # To test selection MECHANISM, I'll provide distinct sets if needed, 
            # but let's try with the real function using the mock pool.
            
            cands = propose_combo_candidates("TEST", self.mock_pool, {}, None, None, limit=500)
            # Re-assign engine id
            final_cands = []
            for c in cands:
                final_cands.append(ComboCandidate(eng, c.numbers, c.score, c.meta))
            candidates_by_engine[eng] = final_cands

        # Run selection
        # NOTE: With pool=22 and max_overlap=2, creating 50 combos is mathematically impossible 
        # (Packing number D(2,22,6) << 50).
        # But for the sake of UNIT TEST of the *Code Logic* (not math feasibility),
        # we can check that it returns *some* portfolio and a report, 
        # or we relax the overlap for the test.
        
        qa_policy = {'max_overlap': 5, 'max_freq': 50} # Relaxed for feasibility test
        
        portfolio, report = select_portfolio(candidates_by_engine, QUOTA, qa_policy)
        
        self.assertEqual(len(portfolio), 50)
        self.assertEqual(report.portfolio_size, 50)
        
        # Check Quota
        counts = Counter([c.engine_id for c in portfolio])
        for eng, q in QUOTA.items():
            self.assertEqual(counts[eng], q, f"Quota mismatch for {eng}")
            
    def test_determinism(self):
        # Run selection twice, expect identical results
        candidates_by_engine = {}
        for eng in QUOTA:
            cands = propose_combo_candidates("TEST", self.mock_pool, {}, None, None, limit=200)
            candidates_by_engine[eng] = [ComboCandidate(eng, c.numbers, c.score, c.meta) for c in cands]
            
        qa_policy = {'max_overlap': 5} # Relaxed
        
        p1, _ = select_portfolio(candidates_by_engine, QUOTA, qa_policy)
        p2, _ = select_portfolio(candidates_by_engine, QUOTA, qa_policy)
        
        nums1 = [c.numbers for c in p1]
        nums2 = [c.numbers for c in p2]
        self.assertEqual(nums1, nums2)

if __name__ == '__main__':
    unittest.main()
