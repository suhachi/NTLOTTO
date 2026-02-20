import unittest
import sys
import os
import numpy as np
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nt_lotto.nt_core.omega import (
    softmax_weights, build_candidate_pool, EngineKPI
)
from nt_lotto.nt_core.schemas import OmegaWeight

class TestOmega(unittest.TestCase):
    def test_softmax_weights_sum_to_one(self):
        kpis = [
            EngineKPI("A", "OK", 0.5, 0.5, 0.5, 0.5, 100),
            EngineKPI("B", "OK", 0.6, 0.6, 0.6, 0.6, 100)
        ]
        weights = softmax_weights(kpis, tau=1.0)
        total_w = sum(w.weight for w in weights)
        self.assertAlmostEqual(total_w, 1.0)
        
    def test_stub_weight_zero(self):
        kpis = [
            EngineKPI("A", "OK", 0.5, 0.5, 0.5, 0.5, 100),
            EngineKPI("B", "STUB", 0.0, 0.0, 0.0, 0.0, 0)
        ]
        weights = softmax_weights(kpis)
        w_dict = {w.engine_id: w.weight for w in weights}
        self.assertEqual(w_dict["B"], 0.0)
        self.assertAlmostEqual(w_dict["A"], 1.0) # Only 1 valid engine triggers renormalization
        
    def test_candidate_pool_size(self):
        # 3 Engines, weights 0.5, 0.3, 0.2
        weights = [
            OmegaWeight("A", 0.0, 0.5),
            OmegaWeight("B", 0.0, 0.3),
            OmegaWeight("C", 0.0, 0.2)
        ]
        
        # Engine A: [1..20]
        # Engine B: [21..40]
        # Engine C: [1..20] reinforcing A
        engine_topk = {
            "A": list(range(1, 21)),
            "B": list(range(21, 41)),
            "C": list(range(1, 21)) 
        }
        
        pool_nums, df = build_candidate_pool(engine_topk, weights, k_eval=20, k_pool=10)
        
        self.assertEqual(len(pool_nums), 10)
        # 1 should be top score because A(0.5) and C(0.2) have it at rank 1
        # Score_1 = 0.5 * 1.0 + 0.2 * 1.0 = 0.7
        # Score_21 = 0.3 * 1.0 = 0.3
        self.assertEqual(pool_nums[0], 1)

if __name__ == '__main__':
    unittest.main()
