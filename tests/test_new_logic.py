import sys
import os
from datetime import datetime, timezone, timedelta
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath("src"))

from scheduler import TweetScheduler
from data_handler import DataManager

class TestScheduleLogic(unittest.TestCase):
    def setUp(self):
        self.scheduler = TweetScheduler()

    def test_vampire_mode_slots(self):
        # Vampire Mode (CST): Mon, Tue, Fri at 00:00, 01:00, 02:00
        # Mon, Feb 2, 2026 is a Monday.
        # 00:00 CST is 06:00 UTC.
        
        # Test Monday 00:00 CST (06:00 UTC)
        vamp_mon = datetime(2026, 2, 2, 6, 0, tzinfo=timezone.utc)
        self.assertTrue(self.scheduler.is_strategy_slot(vamp_mon))
        
        # Test Monday 01:00 CST (07:00 UTC)
        vamp_mon_1 = datetime(2026, 2, 2, 7, 0, tzinfo=timezone.utc)
        self.assertTrue(self.scheduler.is_strategy_slot(vamp_mon_1))
        
        # Test Wednesday 00:00 CST (06:00 UTC) - Should be False
        wed = datetime(2026, 2, 4, 6, 0, tzinfo=timezone.utc)
        self.assertFalse(self.scheduler.is_strategy_slot(wed))

    def test_growth_mode_slots(self):
        # Growth Mode (CST): Everyday at 08:00, 14:00
        # 08:00 CST is 14:00 UTC.
        
        # Everyday 08:00 CST (14:00 UTC)
        growth_anyday = datetime(2026, 2, 4, 14, 0, tzinfo=timezone.utc)
        self.assertTrue(self.scheduler.is_strategy_slot(growth_anyday))
        
        # Everyday 14:00 CST (20:00 UTC)
        growth_anyday_2 = datetime(2026, 2, 4, 20, 0, tzinfo=timezone.utc)
        self.assertTrue(self.scheduler.is_strategy_slot(growth_anyday_2))

    def test_drift_protection(self):
        # Top of hour check (first 5 mins)
        slot_ok = datetime(2026, 2, 4, 14, 2, tzinfo=timezone.utc)
        self.assertTrue(self.scheduler.is_strategy_slot(slot_ok))
        
        slot_late = datetime(2026, 2, 4, 14, 6, tzinfo=timezone.utc)
        self.assertFalse(self.scheduler.is_strategy_slot(slot_late))

    def test_log_attempt(self):
        data_manager = DataManager()
        log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "post_log.csv")
        
        # Log a dummy attempt
        test_msg = "Verification test message"
        data_manager.log_attempt("success", draft_id="test_id", text=test_msg)
        
        # Verify it exists
        self.assertTrue(os.path.exists(log_path))
        
        # Read and check content
        import pandas as pd
        df = pd.read_csv(log_path)
        last_row = df.iloc[-1]
        self.assertEqual(last_row["status"], "success")
        self.assertEqual(last_row["draft_id"], "test_id")
        self.assertIn(test_msg, last_row["text"])

if __name__ == "__main__":
    unittest.main()
