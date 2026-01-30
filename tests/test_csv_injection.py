import sys
import os
import csv
import unittest

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from data_handler import DataManager

class TestCSVInjection(unittest.TestCase):
    def setUp(self):
        self.dm = DataManager()
        self.payload = "=cmd|' /C calc'!A0"
        self.normal = "@mentioning someone"
        # We need to cleanup created drafts.
        self.created_drafts = []

    def tearDown(self):
        # Ideally we remove the rows we added.
        # But DataManager doesn't support delete.
        # We can rewrite the file excluding our IDs.
        if self.created_drafts:
            drafts_file = self.dm.get_path_to_drafts_file()
            rows = []
            with open(drafts_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)

            with open(drafts_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for row in rows:
                    if row[0] not in self.created_drafts:
                        writer.writerow(row)

        # Also remove the safe export file
        safe_path = os.path.join(os.path.dirname(self.dm.get_path_to_drafts_file()), "drafts_safe.csv")
        if os.path.exists(safe_path):
            os.remove(safe_path)

    def test_safe_export(self):
        # 1. Add draft with malicious payload and normal payload
        draft_id_malicious = self.dm.add_draft(text="Malicious", notes=self.payload)
        self.created_drafts.append(draft_id_malicious)

        draft_id_normal = self.dm.add_draft(text=self.normal, notes="Normal")
        self.created_drafts.append(draft_id_normal)

        # 2. Verify it is stored RAW in the main DB (drafts.csv)
        found_raw = False
        with open(self.dm.get_path_to_drafts_file(), 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0] == draft_id_malicious:
                    if row[7] == self.payload:
                        found_raw = True
        self.assertTrue(found_raw, "Malicious payload should be stored RAW in main DB.")

        # 3. Verify safe export
        safe_path = self.dm.export_safe_drafts()
        self.assertTrue(os.path.exists(safe_path))
        self.assertNotEqual(safe_path, self.dm.get_path_to_drafts_file())

        found_sanitized = False
        found_normal_sanitized = False # Should be sanitized too if it starts with @

        with open(safe_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # Malicious check
                if row[0] == draft_id_malicious:
                    # Check notes field (index 7)
                    if row[7] == "'" + self.payload:
                        found_sanitized = True
                    elif row[7] == self.payload:
                         self.fail("Malicious payload found RAW in safe export!")

                # Normal check (@mention)
                if row[0] == draft_id_normal:
                     # Check text field (index 1) which is "@mentioning someone"
                     # Since it starts with @, it SHOULD be sanitized in export
                     if row[1] == "'" + self.normal:
                         found_normal_sanitized = True
                     elif row[1] == self.normal:
                         self.fail("Normal payload starting with @ found RAW in safe export! (Should be sanitized for Excel safety)")

        self.assertTrue(found_sanitized, "Sanitized payload not found in safe export.")
        self.assertTrue(found_normal_sanitized, "Normal payload starting with @ not sanitized in safe export.")

if __name__ == '__main__':
    unittest.main()
