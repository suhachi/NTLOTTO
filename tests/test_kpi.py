import unittest
import pandas as pd
from nt_lotto.nt_core.kpi import compute_recall_at_k, update_engine_kpi

class TestKPI(unittest.TestCase):
    def test_recall(self):
        topk = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        win = {1, 2, 3, 4, 5, 20}
        # Intersect: 1,2,3,4,5 = 5 matches
        # Recall@K = 5/6 = 0.8333
        self.assertAlmostEqual(compute_recall_at_k(topk, win), 5/6)
        
    def test_update_kpi(self):
        # Mock engine history
        history = {
            "E1": {100: [1,2,3,4,5,6], 101: [10,11,12,13,14,15]},
            "E2": {100: [10,11,12,13,14,15], 101: [1,2,3,4,5,6]}
        }
        # Mock SSOT
        ssot_data = [
            {'round': 100, 'n1':1,'n2':2,'n3':3,'n4':4,'n5':5,'n6':6},
            {'round': 101, 'n1':1,'n2':2,'n3':3,'n4':4,'n5':5,'n6':6}
        ]
        ssot_df = pd.DataFrame(ssot_data)
        
        exclusions = {999}
        
        df = update_engine_kpi("dummy.csv", history, ssot_df, exclusions)
        
        e1 = df[df['engine_id']=='E1'].iloc[0]
        # E1: R100=6/6=1.0, R101=0/6=0.0. Mean=0.5
        self.assertAlmostEqual(e1['overall'], 0.5)
        
        e2 = df[df['engine_id']=='E2'].iloc[0]
        # E2: R100=0.0, R101=1.0. Mean=0.5
        self.assertAlmostEqual(e2['overall'], 0.5)

if __name__ == '__main__':
    unittest.main()
