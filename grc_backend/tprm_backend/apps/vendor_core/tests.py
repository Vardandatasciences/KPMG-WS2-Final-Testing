"""
Tests for vendor_core app.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings

from .services import OFACService


@override_settings(OFAC_API_KEY='')
class OFACServiceMockTest(TestCase):
    """OFAC service tests with mocked HTTP (no real API key needed)."""

    def test_search_entity_without_key_returns_mock_or_empty(self):
        """Without OFAC_API_KEY, search_entity returns dict with 'matches' key."""
        service = OFACService()
        out = service.search_entity('Acme Corp')
        self.assertIn('matches', out)
        self.assertIsInstance(out['matches'], list)
        # No error when name has no mock trigger
        if not out.get('mock_data'):
            self.assertNotIn('error', out)

    def test_search_entity_mock_trigger_returns_matches(self):
        """With mock data, names containing 'test' or 'global' or 'med' can return matches."""
        service = OFACService()
        out = service.search_entity('test company')
        self.assertIn('matches', out)
        self.assertIsInstance(out['matches'], list)
        if out.get('mock_data') and out['matches']:
            self.assertEqual(out['matches'][0].get('source'), 'sdn')
            self.assertIn('score', out['matches'][0])

    @override_settings(OFAC_API_KEY='test-key')
    @patch('tprm_backend.apps.vendor_core.services.requests.post')
    def test_search_entity_with_key_calls_v4_api(self, mock_post):
        """With OFAC_API_KEY set, search_entity sends v4 payload (apiKey, cases)."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'error': False,
            'results': [{'id': '1', 'name': 'Acme', 'matchCount': 0, 'matches': []}]
        }
        service = OFACService()
        out = service.search_entity('Acme Corp', case_id=42)
        self.assertIn('matches', out)
        self.assertEqual(out['matches'], [])
        self.assertIsNone(out.get('error'))
        call_args = mock_post.call_args
        payload = call_args[1].get('json') or {}
        self.assertIn('apiKey', payload)
        self.assertIn('cases', payload)
        self.assertEqual(len(payload['cases']), 1)
        self.assertEqual(payload['cases'][0].get('name'), 'Acme Corp')
        self.assertEqual(payload['cases'][0].get('id'), '42')

    @override_settings(OFAC_API_KEY='test-key')
    @patch('tprm_backend.apps.vendor_core.services.requests.post')
    def test_search_entity_api_error_returns_error_key(self, mock_post):
        """When API returns error in body, response contains 'error' and empty matches."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'error': True,
            'errorMessage': 'Account over monthly limit'
        }
        service = OFACService()
        out = service.search_entity('Acme', case_id=1)
        self.assertIn('error', out)
        self.assertEqual(out['matches'], [])
        self.assertIn('limit', out['error'])

    def test_calculate_risk_score_and_determine_risk_level(self):
        """Risk score and level helpers behave as expected."""
        service = OFACService()
        score_high = service.calculate_risk_score({'score': 90, 'source': 'sdn'})
        self.assertGreaterEqual(score_high, 85)
        self.assertEqual(service.determine_risk_level(90), 'HIGH')
        self.assertEqual(service.determine_risk_level(70), 'MEDIUM')
        self.assertEqual(service.determine_risk_level(50), 'LOW')
