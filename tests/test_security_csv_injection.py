
import sys
import os
import csv
import unittest
import tempfile
import shutil
# from unittest.mock import patch # Removed patch

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), 'src'))

import data_handler

class TestSecurityCSVInjection(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.drafts_file = os.path.join(self.test_dir, "drafts.csv")
        self.safe_file = os.path.join(self.test_dir, "drafts_safe_export.csv")

        # Initialize an empty drafts file
        headers = [
            "id", "text", "media_path", "model_used", "status",
            "created_at", "scheduled_time", "notes", "is_retweet", "original_tweet_id"
        ]
        with open(self.drafts_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

        # Direct assignment instead of patch, matching test_data_handler.py pattern
        self.original_drafts_file = data_handler.DRAFTS_FILE
        self.original_data_dir = data_handler.DATA_DIR

        data_handler.DRAFTS_FILE = self.drafts_file
        data_handler.DATA_DIR = self.test_dir

        self.dm = data_handler.DataManager()

    def tearDown(self):
        # Restore globals
        data_handler.DRAFTS_FILE = self.original_drafts_file
        data_handler.DATA_DIR = self.original_data_dir

        shutil.rmtree(self.test_dir)

    def test_safe_export_sanitization(self):
        malicious_text = "=1+1"
        malicious_note = "@cmd"

        # Add a draft with malicious content
        self.dm.add_draft(text=malicious_text, notes=malicious_note)

        # Verify raw storage (should be unsanitized)
        with open(self.drafts_file, 'r', newline='', encoding='utf-8') as f:
            content = f.read()
            # We look for the raw string. In CSV it might be ,=1+1,
            self.assertIn(f"{malicious_text}", content)
            # Ensure it is NOT quoted with a single quote (sanity check)
            self.assertNotIn(f"'{malicious_text}", content)

        # Call safe export
        safe_path = self.dm.export_safe_drafts()

        # Verify path correctness
        self.assertEqual(safe_path, self.safe_file)
        self.assertTrue(os.path.exists(safe_path))

        # Verify sanitized content
        with open(safe_path, 'r', newline='', encoding='utf-8') as f:
            safe_content = f.read()

        # Should contain sanitized text (starts with ')
        self.assertIn(f"'{malicious_text}", safe_content)
        self.assertIn(f"'{malicious_note}", safe_content)

if __name__ == '__main__':
    unittest.main()
