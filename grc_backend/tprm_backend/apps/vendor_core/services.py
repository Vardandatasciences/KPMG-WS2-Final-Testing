"""
OFAC API Integration Service.

When OFAC_API_KEY is set in settings, the service can call the real OFAC API.
When unset or when the real API returns errors, mock data is used (see _make_request).
"""

import requests
import logging
from typing import Dict, List, Optional
from django.conf import settings

logger = logging.getLogger('vendor_security')


class OFACService:
    """Service class for OFAC API integration"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'OFAC_API_BASE_URL', 'https://api.ofac-api.com/v4')
        self.api_key = getattr(settings, 'OFAC_API_KEY', '') or ''
        self.headers = {
            'Content-Type': 'application/json'
        }

    def search_individual(self, first_name: str, last_name: str, **kwargs) -> Dict:
        """Search for individual in OFAC database"""
        endpoint = f"{self.base_url}/search"
        
        payload = {
            'api_key': self.api_key,  # Changed from 'apiKey' to 'api_key'
            'name': f"{first_name} {last_name}",  # Single name, not array
            'threshold': kwargs.get('threshold', 95),
            'sources': kwargs.get('sources', ['sdn', 'cons', 'fse', 'isa', 'plc']),
            'types': ['individual']
        }
        
        return self._make_request(endpoint, payload)

    def search_entity(self, entity_name: str, **kwargs) -> Dict:
        """Search for entity/company in OFAC database.
        Uses OFAC API v4 format when api_key is set: apiKey, cases=[{id, name}], sources, types.
        See https://docs.ofac-api.com/search-api/request
        """
        endpoint = f"{self.base_url}/search"
        case_id = kwargs.get('case_id', '0')

        if self.api_key:
            # v4 API format: apiKey, cases array, sources (SDN, EU, UN, etc.),
            # types. Sources default to settings.OFAC_SOURCES (default: ['SDN']).
            default_sources = getattr(settings, 'OFAC_SOURCES', ['SDN'])
            payload = {
                'apiKey': self.api_key,
                'sources': kwargs.get('sources', default_sources),
                'types': ['person', 'organization', 'vessel', 'aircraft'],
                'cases': [{'id': str(case_id), 'name': (entity_name or '').strip() or 'Unknown'}]
            }
        else:
            payload = {
                'api_key': '',
                'name': entity_name,
                'sources': ['sdn', 'cons', 'fse', 'isa', 'plc'],
                'types': ['entity', 'vessel']
            }

        return self._make_request(endpoint, payload, case_id=case_id)

    def get_details(self, entry_id: str) -> Dict:
        """Get detailed information about a specific OFAC entry"""
        endpoint = f"{self.base_url}/details/{entry_id}?apiKey={self.api_key}"
        return self._make_request(endpoint, method='GET')

    def bulk_search(self, names: List[str], **kwargs) -> Dict:
        """Perform bulk search for multiple names"""
        endpoint = f"{self.base_url}/bulk-search"
        
        payload = {
            'apiKey': self.api_key,
            'names': names,  # This endpoint does accept arrays
            'threshold': kwargs.get('threshold', 85),
            'sources': kwargs.get('sources', ['sdn', 'cons', 'fse', 'isa', 'plc'])
        }
        
        return self._make_request(endpoint, payload)

    def _normalize_v4_match(self, m: Dict) -> Dict:
        """Convert OFAC API v4 sanction object to internal match shape (id, name, source, score, etc.)."""
        aliases = []
        if m.get('alias'):
            aliases = [a.get('name') or a.get('firstName', '') + ' ' + a.get('lastName', '') for a in m['alias'] if isinstance(a, dict)]
        addresses = m.get('addresses') or []
        if addresses and isinstance(addresses[0], dict):
            addresses = [f"{a.get('address1', '')} {a.get('city', '')} {a.get('country', '')}".strip() for a in addresses]
        return {
            'id': m.get('id'),
            'name': m.get('name') or m.get('nameFormatted', ''),
            'source': (m.get('source') or 'SDN').upper(),
            'score': 85,
            'aliases': aliases,
            'addresses': addresses,
            'programs': m.get('programs', []),
            'remarks': m.get('remarks', '') or '',
        }

    def _make_request(self, endpoint: str, payload: Dict = None, method: str = 'POST', case_id: str = '0') -> Dict:
        """Make HTTP request to OFAC API. Supports v4 format (apiKey, cases[]) and response (results[].matches)."""
        try:
            logger.info(f"Making {method} request to OFAC API: {endpoint}")
            if payload and 'apiKey' in payload:
                log_payload = {**payload, 'apiKey': '***' if payload.get('apiKey') else ''}
            else:
                log_payload = payload
            logger.info(f"Payload (key redacted): {log_payload}")

            search_name = (payload.get('name', '') or (payload.get('cases', [{}])[0].get('name', '') if payload.get('cases') else '')).lower()

            if self.api_key and payload and payload.get('apiKey'):
                try:
                    if method == 'POST':
                        response = requests.post(endpoint, json=payload, headers=self.headers, timeout=30)
                    else:
                        response = requests.get(endpoint, headers=self.headers, timeout=30)
                    logger.info(f"OFAC API response status: {response.status_code}")
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('error') or result.get('errorMessage'):
                            err = result.get('errorMessage') or 'OFAC API returned an error'
                            logger.warning(f"OFAC API error in body: {err}")
                            return {'error': err, 'matches': []}
                        # v4: results[].matches
                        raw_matches = []
                        for r in result.get('results', []):
                            raw_matches.extend(r.get('matches', []))
                        matches = [self._normalize_v4_match(m) for m in raw_matches]
                        logger.info(f"OFAC API response received with {len(matches)} matches")
                        return {'matches': matches, 'results': result.get('results'), 'error': None}
                    err_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(f"OFAC API error: {err_msg}; falling back to mock")
                    return {'error': err_msg, 'matches': []}
                except Exception as api_err:
                    logger.warning(f"OFAC API request failed: {api_err}; falling back to mock data")
            else:
                if not self.api_key:
                    logger.warning("OFAC_API_KEY not set - using mock OFAC data. Set OFAC_API_KEY in env/settings for live API.")

            # Mock data (when no key, or API error)
            mock_matches = []
            if 'test' in search_name or 'global' in search_name or 'med' in search_name:
                mock_matches = [
                    {
                        'id': 'mock_001',
                        'name': f'Mock Match for {search_name}',
                        'source': 'sdn',
                        'score': 75,
                        'aliases': [f'{search_name} Ltd', f'{search_name} Inc'],
                        'addresses': ['123 Mock Street, Test City'],
                        'programs': ['Test Sanctions Program'],
                        'remarks': 'Mock test data for demonstration',
                        'risk_level': 'MEDIUM'
                    }
                ]
            result = {
                'matches': mock_matches,
                'total_matches': len(mock_matches),
                'search_term': search_name,
                'mock_data': True
            }
            logger.info(f"Mock OFAC response with {len(mock_matches)} matches")
            return result

        except Exception as e:
            logger.error(f"Unexpected error in OFAC API call: {str(e)}")
            return {'error': str(e), 'matches': []}

    def calculate_risk_score(self, match_data: Dict) -> int:
        """Calculate risk score based on match data"""
        base_score = match_data.get('score', 0)
        
        # Adjust score based on list type
        list_type = match_data.get('source', '').lower()
        if list_type == 'sdn':  # Specially Designated Nationals
            base_score += 10
        elif list_type == 'cons':  # Consolidated Sanctions
            base_score += 8
        elif list_type == 'fse':  # Foreign Sanctions Evaders
            base_score += 6
        
        # Adjust for exact name matches
        if match_data.get('name_match_score', 0) > 95:
            base_score += 5
            
        return min(base_score, 100)  # Cap at 100

    def determine_risk_level(self, match_score: float) -> str:
        """Determine risk level based on match score"""
        if match_score >= 85:
            return 'HIGH'
        elif match_score >= 70:
            return 'MEDIUM'
        else:
            return 'LOW'

    def extract_match_details(self, match: Dict) -> Dict:
        """Extract and format match details for storage"""
        return {
            'ofac_id': match.get('id'),
            'name': match.get('name'),
            'source': match.get('source'),
            'aliases': match.get('aliases', []),
            'addresses': match.get('addresses', []),
            'programs': match.get('programs', []),
            'remarks': match.get('remarks', ''),
            'date_of_birth': match.get('date_of_birth'),
            'place_of_birth': match.get('place_of_birth'),
            'nationality': match.get('nationality'),
            'id_number': match.get('id_number'),
            'original_score': match.get('score', 0)
        }

    def test_connection(self) -> Dict:
        """Test OFAC API connection using v4 format (apiKey, cases[])."""
        if not self.api_key:
            return {
                'success': False,
                'message': 'OFAC_API_KEY is not set. Add it to .env to use the live API.'
            }
        try:
            endpoint = f"{self.base_url}/search"
            payload = {
                'apiKey': self.api_key,
                'sources': ['SDN'],
                'types': ['person', 'organization'],
                'cases': [{'id': 'connection-test', 'name': 'Test'}]
            }
            logger.info(f"Testing OFAC API connection: {endpoint}")
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=15)
            logger.info(f"OFAC test response status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                if result.get('error') or result.get('errorMessage'):
                    return {
                        'success': False,
                        'message': result.get('errorMessage') or 'OFAC API returned an error',
                        'response': result
                    }
                return {
                    'success': True,
                    'message': 'OFAC API connection successful',
                    'response': result
                }
            return {
                'success': False,
                'message': f'OFAC API error: {response.status_code} - {response.text[:300]}',
                'status_code': response.status_code
            }
        except Exception as e:
            logger.error(f"OFAC API connection test failed: {str(e)}")
            return {
                'success': False,
                'message': f'OFAC API connection failed: {str(e)}'
            }


class SanctionsNetworkService:
    """
    Service class for sanctions.network integration.
    This is used to back the internal SANCTIONS screening type with a real,
    free, public sanctions API (US OFAC, UN, EU, etc.).
    """

    def __init__(self):
        # Base URL can be overridden via SANCTIONS_API_BASE_URL in settings / .env
        self.base_url = getattr(settings, 'SANCTIONS_API_BASE_URL', 'https://sanctions.network').rstrip('/')
        self.session = requests.Session()

    def _normalize_match(self, item: Dict) -> Dict:
        """
        Convert sanctions.network row into internal match shape that is
        compatible with how OFACService results are stored.
        """
        names = item.get('names') or []
        primary_name = names[0] if names else ''
        aliases = names[1:] if len(names) > 1 else []
        source = (item.get('source') or '').upper() or 'UNKNOWN'

        addresses = item.get('addresses') or []
        programs = item.get('programs') or []

        return {
            'id': item.get('source_id') or item.get('id'),
            'name': primary_name,
            'source': source,
            # Treat any sanctions hit as high-risk by default; you can refine later.
            'score': 90,
            'aliases': aliases,
            'addresses': addresses,
            'programs': programs,
            'remarks': item.get('remarks', '') or '',
            'risk_level': 'HIGH',
        }

    def search_entity(self, entity_name: str, limit: int = 50) -> Dict:
        """
        Search sanctions.network for an entity by name using the fuzzy
        /rpc/search_sanctions endpoint.
        Docs: https://sanctions.network/
        """
        entity_name = (entity_name or '').strip()
        if not entity_name:
            return {'matches': [], 'error': None}

        try:
            url = f"{self.base_url}/rpc/search_sanctions"
            params = {
                'name': entity_name,
                'limit': limit,
            }
            logger.info(f"Calling sanctions.network for SANCTIONS screening: {url} params={params}")
            response = self.session.get(url, params=params, timeout=25)
            logger.info(f"sanctions.network response status: {response.status_code}")

            if response.status_code != 200:
                err = f"sanctions.network HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(err)
                return {'matches': [], 'error': err}

            data = response.json() or []
            matches = [self._normalize_match(item) for item in data]
            logger.info(f"sanctions.network returned {len(matches)} matches for name={entity_name}")
            return {'matches': matches, 'error': None, 'raw': data}

        except Exception as e:
            err = f"sanctions.network request failed: {str(e)}"
            logger.warning(err, exc_info=True)
            return {'matches': [], 'error': err}

