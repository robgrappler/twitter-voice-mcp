import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath("src"))

from twitter_handler import TwitterHandler

class TestMediaSupport(unittest.TestCase):
    @patch('requests.get')
    def test_url_detection(self, mock_get):
        # Mock successful download
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'fake_data']
        mock_get.return_value = mock_response

        handler = TwitterHandler()
        handler.session = MagicMock()
        # Mock _chunked_upload to avoid actual API call
        handler._chunked_upload = MagicMock(return_value="media_id_123")
        
        # Test with URL
        media_id = handler.upload_media("https://picsum.photos/200/300")
        
        self.assertEqual(media_id, "media_id_123")
        mock_get.assert_called_once()
        handler._chunked_upload.assert_called_once()

    def test_chunked_upload_logic(self):
        handler = TwitterHandler()
        handler.session = MagicMock()
        
        # Mock INIT
        mock_init = MagicMock()
        mock_init.status_code = 202
        mock_init.json.return_value = {'media_id_string': '987'}
        
        # Mock APPEND
        mock_append = MagicMock()
        mock_append.status_code = 204
        
        # Mock FINALIZE
        mock_finalize = MagicMock()
        mock_finalize.status_code = 200
        
        handler.session.post.side_effects = [mock_init, mock_append, mock_finalize]
        
        # We need a real file for os.path.getsize
        with open('test_tmp.jpg', 'wb') as f:
            f.write(b'fake')
        
        try:
            handler.session.post.side_effect = [mock_init, mock_append, mock_finalize]
            res = handler._chunked_upload('test_tmp.jpg')
            self.assertEqual(res, '987')
        finally:
            if os.path.exists('test_tmp.jpg'):
                os.remove('test_tmp.jpg')

if __name__ == "__main__":
    unittest.main()
