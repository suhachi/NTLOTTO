import unittest
from nt_lotto.nt_core.scoring import score_combo

class TestScoring(unittest.TestCase):
    def test_score_ranks(self):
        win = {1, 2, 3, 4, 5, 6}
        bonus = 7
        
        # 1st: 6 hits
        s = score_combo([1, 2, 3, 4, 5, 6], win, bonus)
        self.assertEqual(s['rank'], 1)
        
        # 2nd: 5 hits + bonus
        s = score_combo([1, 2, 3, 4, 5, 7], win, bonus)
        self.assertEqual(s['rank'], 2)
        
        # 3rd: 5 hits
        s = score_combo([1, 2, 3, 4, 5, 8], win, bonus)
        self.assertEqual(s['rank'], 3)
        
        # 4th: 4 hits
        s = score_combo([1, 2, 3, 4, 8, 9], win, bonus)
        self.assertEqual(s['rank'], 4)
        
        # 5th: 3 hits
        s = score_combo([1, 2, 3, 8, 9, 10], win, bonus)
        self.assertEqual(s['rank'], 5)
        
        # Fail
        s = score_combo([1, 2, 8, 9, 10, 11], win, bonus)
        self.assertEqual(s['rank'], 0)

if __name__ == "__main__":
    unittest.main()
