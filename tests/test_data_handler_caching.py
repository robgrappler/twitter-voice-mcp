import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
import sys

# Add src to path
sys.path.append(os.path.abspath("src"))

from data_handler import DataManager, DRAFTS_FILE

class TestDataHandlerCaching(unittest.TestCase):
    def setUp(self):
        # Patch os.path.exists to avoid actual file checks
        self.exists_patcher = patch('os.path.exists')
        self.mock_exists = self.exists_patcher.start()
        self.mock_exists.return_value = True

        # Patch pandas.read_csv
        self.read_csv_patcher = patch('pandas.read_csv')
        self.mock_read_csv = self.read_csv_patcher.start()

        # Setup mock DataFrame
        self.mock_df = pd.DataFrame({
            "id": ["1", "2"],
            "status": ["pending", "posted"],
            "text": ["t1", "t2"],
            "media_path": ["", ""],
            "model_used": ["m1", "m2"],
            "created_at": ["", ""],
            "scheduled_time": ["", ""],
            "notes": ["", ""],
            "is_retweet": [False, False],
            "original_tweet_id": ["", ""]
        })
        self.mock_read_csv.return_value = self.mock_df

        # Patch os.path.getmtime
        self.getmtime_patcher = patch('os.path.getmtime')
        self.mock_getmtime = self.getmtime_patcher.start()
        self.mock_getmtime.return_value = 100.0

        self.dm = DataManager()
        # Reset mock calls from init
        self.mock_read_csv.reset_mock()

    def tearDown(self):
        self.exists_patcher.stop()
        self.read_csv_patcher.stop()
        self.getmtime_patcher.stop()

    def test_caching_behavior(self):
        # 1. First call should read CSV
        self.dm.list_pending_drafts()
        self.mock_read_csv.assert_called_once()

        # Reset mock
        self.mock_read_csv.reset_mock()

        # 2. Second call with same mtime should NOT read CSV
        self.dm.list_pending_drafts()
        self.mock_read_csv.assert_not_called()

        # 3. Change mtime
        self.mock_getmtime.return_value = 200.0

        # 4. Third call should read CSV again
        self.dm.list_pending_drafts()
        self.mock_read_csv.assert_called_once()

    def test_write_invalidates_or_updates_cache(self):
        # 1. Read to load cache
        self.dm.list_pending_drafts()
        self.mock_read_csv.reset_mock()

        # 2. Write (update_draft_status)
        with patch.object(pd.DataFrame, 'to_csv') as mock_to_csv:
            # We want getmtime to return 100 (initial) then 300 (after write)
            # update_draft_status calls:
            # 1. _get_df -> getmtime (should be 100)
            # 2. ... write ...
            # 3. getmtime (should be 300)
            # list_pending_drafts calls:
            # 4. _get_df -> getmtime (should be 300)

            self.mock_getmtime.side_effect = [100.0, 300.0, 300.0]

            # Call update
            self.dm.update_draft_status("1", "posted")

            # Verify to_csv called
            mock_to_csv.assert_called()

            # Check read_csv was NOT called during update (cached used)
            self.mock_read_csv.assert_not_called()

            # 3. Read again.
            self.dm.list_pending_drafts()
            # Should NOT call read_csv because last_mtime was updated to 300
            self.mock_read_csv.assert_not_called()

if __name__ == "__main__":
    unittest.main()
