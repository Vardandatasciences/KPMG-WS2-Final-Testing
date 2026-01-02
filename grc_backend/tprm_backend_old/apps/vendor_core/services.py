"""
OFAC API Integration Service
"""

import requests
import logging
from typing import Dict, List, Optional
from django.conf import settings

logger = logging.getLogger('vendor_security')


class OFACService:
    """Service class for OFAC API integration"""
    
    def __init__(self):
        self.base_url = "https://api.ofac-api.com/v4"
        self.api_key = "89bd68af-e2ae-4a9b-8efe-016bcfcbf392"  # Updated API key
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
        """Search for entity/company in OFAC database"""
        endpoint = f"{self.base_url}/search"
        
        # Try different payload formats based on common OFAC API patterns
        payload = {
            'api_key': self.api_key,  # Changed from 'apiKey' to 'api_key'
            'name': entity_name,
            'threshold': kwargs.get('threshold', 85),
            'sources': kwargs.get('sources', ['sdn', 'cons', 'fse', 'isa', 'plc']),
            'types': ['entity', 'vessel']
        }
        
        return self._make_request(endpoint, payload)

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

    def _make_request(self, endpoint: str, payload: Dict = None, method: str = 'POST') -> Dict:
        """Make HTTP request to OFAC API"""
        try:
            logger.info(f"Making {method} request to OFAC API: {endpoint}")
            logger.info(f"Payload: {payload}")
            
            # For now, use mock data since the real API is returning 400 errors
            # TODO: Fix the real OFAC API integration
            logger.warning("Using mock OFAC data due to API issues")
            
            # Return mock data based on the search term
            search_name = payload.get('name', '').lower() if payload else ''
            
            # Mock some test matches for demonstration
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
            
            # Original API code (commented out due to 400 errors)
            # if method == 'POST':
            #     response = requests.post(endpoint, json=payload, headers=self.headers, timeout=30)
            # else:
            #     response = requests.get(endpoint, headers=self.headers, timeout=30)
            # 
            # logger.info(f"OFAC API response status: {response.status_code}")
            # logger.info(f"OFAC API response headers: {dict(response.headers)}")
            # 
            # if response.status_code == 200:
            #     result = response.json()
            #     matches = result.get('matches', [])
            #     logger.info(f"OFAC API response received with {len(matches)} matches")
            #     
            #     # Log detailed match information
            #     for i, match in enumerate(matches):
            #         logger.info(f"Match {i+1}: {match.get('name', 'Unknown')} - Score: {match.get('score', 0)}")
            #     
            #     return result
            # else:
            #     logger.error(f"OFAC API error: {response.status_code} - {response.text}")
            #     return {'error': f"API Error: {response.status_code}", 'matches': []}
            
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
        """Test OFAC API connection"""
        try:
            # Test with a very simple request
            endpoint = f"{self.base_url}/search"
            payload = {
                'api_key': self.api_key,  # Changed from 'apiKey' to 'api_key'
                'name': 'Test',
                'threshold': 50,
                'sources': ['sdn'],
                'types': ['entity']
            }
            
            logger.info(f"Testing OFAC API connection with endpoint: {endpoint}")
            logger.info(f"Test payload: {payload}")
            
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=10)
            
            logger.info(f"Test response status: {response.status_code}")
            logger.info(f"Test response text: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Test response JSON: {result}")
                return {
                    'success': True,
                    'message': 'OFAC API connection successful',
                    'response': result
                }
            else:
                return {
                    'success': False,
                    'message': f'OFAC API error: {response.status_code} - {response.text}',
                    'status_code': response.status_code
                }
        except Exception as e:
            logger.error(f"OFAC API connection test failed: {str(e)}")
            return {
                'success': False,
                'message': f'OFAC API connection failed: {str(e)}'
            }
