import unittest
import sys
import os
import numpy as np

# Adjust path to import nt_lotto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nt_lotto.nt_core.metrics import recall_at_k, summarize_recalls

class TestMetrics(unittest.TestCase):
    def test_recall_at_k(self):
        win_set = {1, 2, 3, 4, 5, 6}
        
        # Perfect match
        self.assertAlmostEqual(recall_at_k({1, 2, 3, 4, 5, 6}, win_set), 1.0)
        
        # Partial match (3 out of 6)
        # 3/6 = 0.5
        self.assertAlmostEqual(recall_at_k({1, 2, 3, 10, 11, 12}, win_set), 0.5)
        
        # No match
        self.assertAlmostEqual(recall_at_k({10, 11, 12, 13, 14, 15}, win_set), 0.0)
        
        # Empty inputs
        self.assertAlmostEqual(recall_at_k(set(), win_set), 0.0)
        
    def test_summarize_recalls(self):
        recalls = [0.1] * 100
        summary = summarize_recalls(recalls)
        self.assertAlmostEqual(summary['overall'], 0.1)
        self.assertAlmostEqual(summary['recent10'], 0.1)
        
        # 50 zeros, 50 ones
        # mean=0.5
        recalls_varying = [0.0] * 50 + [1.0] * 50
        summary_v = summarize_recalls(recalls_varying)
        self.assertAlmostEqual(summary_v['overall'], 0.5)
        self.assertAlmostEqual(summary_v['recent10'], 1.0)
        # recent 20 -> 20 of 1.0 -> 1.0
        self.assertAlmostEqual(summary_v['recent20'], 1.0)
        # recent 30 -> 30 of 1.0 -> 1.0
        self.assertAlmostEqual(summary_v['recent30'], 1.0)
        
        # Empty
        summary_e = summarize_recalls([])
        self.assertEqual(summary_e['overall'], 0.0)

if __name__ == '__main__':
    unittest.main()
