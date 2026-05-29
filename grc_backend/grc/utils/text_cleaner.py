"""
Text cleaning utilities for similarity detection pipeline (Step 1).

This module provides text preprocessing for Framework, Policy, SubPolicy, and Compliance
to prepare data for embedding generation and semantic similarity search.
"""

import re
import html
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class CleaningResult:
    """
    Result of text cleaning operation.
    
    Hybrid approach:
    - structured_json: Cleaned fields as JSON for storage/querying
    - embedding_text: Generated text blob for embedding similarity search
    """
    structured_json: Dict[str, Any]  # Structured data for DB storage
    embedding_text: str  # Generated text for embedding model
    original_values: Dict[str, Any]  # Original raw values
    changes_made: List[str]  # List of cleaning operations performed
    timestamp: str
    entity_type: str
    entity_id: Optional[int] = None
    
    # Backward compatibility - cleaned_text is now embedding_text
    @property
    def cleaned_text(self) -> str:
        return self.embedding_text


class TextCleaner:
    """
    Configurable text cleaner for GRC entity similarity detection.
    
    Supports cleaning for:
    - Framework (FrameworkName, FrameworkDescription, Category, Domain, InternalExternal, Identifier)
    - Policy (PolicyName, PolicyDescription, PolicyType, PolicyCategory, PolicySubCategory, Scope, Objective)
    - SubPolicy (SubPolicyName, Description, Control, Identifier)
    - Compliance (ComplianceTitle, ComplianceItemDescription, ComplianceType, Scope, Objective, Criticality, RiskCategory, Identifier)
    """
    
    # Configurable cleaning rules - NO hardcoded limits or spellings
    DEFAULT_CONFIG = {
        'remove_html': True,
        'normalize_whitespace': True,
        'fix_spelling': False,
        'spelling_corrections': {},  # Configurable: {'typo': 'correction', ...}
        'normalize_unicode': True,  # Convert Unicode to ASCII equivalents
        'remove_urls': False,
        'remove_email_addresses': False,
        'remove_bullet_points': True,
        'normalize_bullets_to_pipes': True,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize text cleaner with configuration."""
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
    
    def clean_framework(self, framework_data: Dict[str, Any]) -> CleaningResult:
        """
        Clean framework fields.
        
        Returns both structured JSON and embedding text.
        
        Args:
            framework_data: Dictionary with FrameworkName, FrameworkDescription, 
                           Category, Domain, InternalExternal, Identifier
        """
        changes = []
        # Ensure all values are plain strings (guard against encrypted list fields)
        framework_data = {
            k: (' '.join(str(i) for i in v) if isinstance(v, list) else v)
            for k, v in (framework_data or {}).items()
        }
        original = dict(framework_data)
        
        # Clean individual fields
        name = self._clean_name(framework_data.get('FrameworkName', ''))
        if name != framework_data.get('FrameworkName', ''):
            changes.append(f"Normalized FrameworkName: '{framework_data.get('FrameworkName')}' -> '{name}'")
        
        description = self._clean_description(framework_data.get('FrameworkDescription', ''))
        if description != framework_data.get('FrameworkDescription', ''):
            changes.append(f"Cleaned FrameworkDescription")
        
        category = self._clean_category(framework_data.get('Category', ''))
        if category != framework_data.get('Category', ''):
            changes.append(f"Normalized Category")
        
        # Handle Domain FK
        domain_name = ''
        domain_id = None
        domain_obj = framework_data.get('Domain') or framework_data.get('domain')
        if domain_obj:
            if hasattr(domain_obj, 'DomainName'):
                domain_name = self._clean_name(domain_obj.DomainName)
            elif hasattr(domain_obj, 'domain_name'):
                domain_name = self._clean_name(domain_obj.domain_name)
            elif isinstance(domain_obj, str):
                domain_name = self._clean_name(domain_obj)
            # Get domain ID if available
            if hasattr(domain_obj, 'DomainId') or hasattr(domain_obj, 'id'):
                domain_id = getattr(domain_obj, 'DomainId', None) or getattr(domain_obj, 'id', None)
        
        internal_external = self._clean_type_field(framework_data.get('InternalExternal', ''))
        if internal_external:
            internal_external = internal_external.capitalize()
        
        identifier = self._clean_identifier(framework_data.get('Identifier', ''))
        
        # Build structured JSON for storage
        structured_json = {
            'record_type': 'framework',
            'name': name,
            'description': description,
            'category': category,
            'domain': domain_name,
            'domain_id': domain_id,
            'type': internal_external,
            'identifier': identifier,
        }
        
        # Generate embedding text from structured JSON
        embedding_text = self._generate_embedding_text(structured_json)
        
        return CleaningResult(
            structured_json=structured_json,
            embedding_text=embedding_text,
            original_values=original,
            changes_made=changes,
            timestamp=self._get_timestamp(),
            entity_type='Framework'
        )
    
    def clean_policy(self, policy_data: Dict[str, Any]) -> CleaningResult:
        """Clean policy fields - returns structured JSON + embedding text."""
        changes = []
        policy_data = {k: (' '.join(str(i) for i in v) if isinstance(v, list) else v) for k, v in (policy_data or {}).items()}
        original = dict(policy_data)
        
        name = self._clean_name(policy_data.get('PolicyName', ''))
        if name != policy_data.get('PolicyName', ''):
            changes.append("Normalized PolicyName")
        
        description = self._clean_description(policy_data.get('PolicyDescription', ''))
        
        policy_type = self._clean_type_field(policy_data.get('PolicyType', ''))
        category = self._clean_category(policy_data.get('PolicyCategory', ''))
        sub_category = self._clean_category(policy_data.get('PolicySubCategory', ''))
        scope = self._clean_long_text(policy_data.get('Scope', ''))
        objective = self._clean_long_text(policy_data.get('Objective', ''))
        
        # Get parent framework info
        framework_id = None
        framework_obj = policy_data.get('FrameworkId')
        if framework_obj:
            framework_id = getattr(framework_obj, 'FrameworkId', None) or getattr(framework_obj, 'id', None) or framework_obj
        
        # Build structured JSON
        structured_json = {
            'record_type': 'policy',
            'name': name,
            'description': description,
            'policy_type': policy_type,
            'category': category,
            'sub_category': sub_category,
            'scope': scope,
            'objective': objective,
            'framework_id': framework_id,
        }
        
        # Generate embedding text
        embedding_text = self._generate_embedding_text(structured_json)
        
        return CleaningResult(
            structured_json=structured_json,
            embedding_text=embedding_text,
            original_values=original,
            changes_made=changes,
            timestamp=self._get_timestamp(),
            entity_type='Policy'
        )
    
    def clean_subpolicy(self, subpolicy_data: Dict[str, Any]) -> CleaningResult:
        """Clean sub-policy fields - returns structured JSON + embedding text."""
        changes = []
        subpolicy_data = {k: (' '.join(str(i) for i in v) if isinstance(v, list) else v) for k, v in (subpolicy_data or {}).items()}
        original = dict(subpolicy_data)
        
        name = self._clean_name(subpolicy_data.get('SubPolicyName', ''))
        description = self._clean_description(subpolicy_data.get('Description', ''))
        control = self._clean_long_text(subpolicy_data.get('Control', ''))
        identifier = self._clean_identifier(subpolicy_data.get('Identifier', ''))
        
        if name != subpolicy_data.get('SubPolicyName', ''):
            changes.append("Normalized SubPolicyName")
        
        # Get parent IDs
        framework_id = None
        policy_id = None
        
        framework_obj = subpolicy_data.get('FrameworkId')
        if framework_obj:
            framework_id = getattr(framework_obj, 'FrameworkId', None) or getattr(framework_obj, 'id', None) or framework_obj
        
        policy_obj = subpolicy_data.get('PolicyId')
        if policy_obj:
            policy_id = getattr(policy_obj, 'PolicyId', None) or getattr(policy_obj, 'id', None) or policy_obj
        
        # Build structured JSON
        structured_json = {
            'record_type': 'subpolicy',
            'name': name,
            'description': description,
            'control': control,
            'identifier': identifier,
            'framework_id': framework_id,
            'policy_id': policy_id,
        }
        
        # Generate embedding text
        embedding_text = self._generate_embedding_text(structured_json)
        
        return CleaningResult(
            structured_json=structured_json,
            embedding_text=embedding_text,
            original_values=original,
            changes_made=changes,
            timestamp=self._get_timestamp(),
            entity_type='SubPolicy'
        )
    
    def clean_compliance(self, compliance_data: Dict[str, Any]) -> CleaningResult:
        """Clean compliance fields - returns structured JSON + embedding text."""
        changes = []
        compliance_data = {k: (' '.join(str(i) for i in v) if isinstance(v, list) else v) for k, v in (compliance_data or {}).items()}
        original = dict(compliance_data)
        
        title = self._clean_name(compliance_data.get('ComplianceTitle', ''))
        description = self._clean_description(compliance_data.get('ComplianceItemDescription', ''))
        comp_type = self._clean_type_field(compliance_data.get('ComplianceType', ''))
        scope = self._clean_long_text(compliance_data.get('Scope', ''))
        objective = self._clean_long_text(compliance_data.get('Objective', ''))
        criticality = self._clean_type_field(compliance_data.get('Criticality', ''))
        risk_category = self._clean_category(compliance_data.get('RiskCategory', ''))
        identifier = self._clean_identifier(compliance_data.get('Identifier', ''))
        
        if title != compliance_data.get('ComplianceTitle', ''):
            changes.append("Normalized ComplianceTitle")
        
        # Get parent IDs
        framework_id = None
        policy_id = None
        subpolicy_id = None
        
        framework_obj = compliance_data.get('FrameworkId')
        if framework_obj:
            framework_id = getattr(framework_obj, 'FrameworkId', None) or getattr(framework_obj, 'id', None) or framework_obj
        
        policy_obj = compliance_data.get('PolicyId')
        if policy_obj:
            policy_id = getattr(policy_obj, 'PolicyId', None) or getattr(policy_obj, 'id', None) or policy_obj
        
        subpolicy_obj = compliance_data.get('SubPolicy') or compliance_data.get('Subpolicy') or compliance_data.get('subpolicy')
        if subpolicy_obj:
            subpolicy_id = getattr(subpolicy_obj, 'SubPolicyId', None) or getattr(subpolicy_obj, 'id', None) or subpolicy_obj
        
        # Build structured JSON
        structured_json = {
            'record_type': 'compliance',
            'title': title,
            'description': description,
            'compliance_type': comp_type,
            'scope': scope,
            'objective': objective,
            'criticality': criticality,
            'risk_category': risk_category,
            'identifier': identifier,
            'framework_id': framework_id,
            'policy_id': policy_id,
            'subpolicy_id': subpolicy_id,
        }
        
        # Generate embedding text
        embedding_text = self._generate_embedding_text(structured_json)
        
        return CleaningResult(
            structured_json=structured_json,
            embedding_text=embedding_text,
            original_values=original,
            changes_made=changes,
            timestamp=self._get_timestamp(),
            entity_type='Compliance'
        )
    
    # ============== Private Helper Methods ==============
    
    def _generate_embedding_text(self, structured_json: Dict[str, Any]) -> str:
        """
        Generate embedding text from structured JSON.
        
        Creates a clean, readable text blob for the embedding model.
        Format: "Field: Value | Field: Value | ..."
        """
        record_type = structured_json.get('record_type', 'unknown')
        
        parts = [f"Record Type: {record_type.title()}"]
        
        # Common fields across all types
        if 'name' in structured_json and structured_json['name']:
            parts.append(f"Name: {structured_json['name']}")
        
        if 'title' in structured_json and structured_json['title']:
            parts.append(f"Title: {structured_json['title']}")
        
        if 'description' in structured_json and structured_json['description']:
            parts.append(f"Description: {structured_json['description']}")
        
        # Type/category fields
        if 'type' in structured_json and structured_json['type']:
            parts.append(f"Type: {structured_json['type']}")
        
        if 'policy_type' in structured_json and structured_json['policy_type']:
            parts.append(f"Policy Type: {structured_json['policy_type']}")
        
        if 'compliance_type' in structured_json and structured_json['compliance_type']:
            parts.append(f"Compliance Type: {structured_json['compliance_type']}")
        
        if 'category' in structured_json and structured_json['category']:
            parts.append(f"Category: {structured_json['category']}")
        
        if 'sub_category' in structured_json and structured_json['sub_category']:
            parts.append(f"Sub Category: {structured_json['sub_category']}")
        
        if 'risk_category' in structured_json and structured_json['risk_category']:
            parts.append(f"Risk Category: {structured_json['risk_category']}")
        
        # Domain and scope
        if 'domain' in structured_json and structured_json['domain']:
            parts.append(f"Domain: {structured_json['domain']}")
        
        if 'scope' in structured_json and structured_json['scope']:
            parts.append(f"Scope: {structured_json['scope']}")
        
        if 'objective' in structured_json and structured_json['objective']:
            parts.append(f"Objective: {structured_json['objective']}")
        
        # Control and criticality
        if 'control' in structured_json and structured_json['control']:
            parts.append(f"Control: {structured_json['control']}")
        
        if 'criticality' in structured_json and structured_json['criticality']:
            parts.append(f"Criticality: {structured_json['criticality']}")
        
        # Identifier
        if 'identifier' in structured_json and structured_json['identifier']:
            parts.append(f"Identifier: {structured_json['identifier']}")
        
        # Parent IDs (for context, but may be less important for embedding)
        # These are included at the end with lower weight in semantic meaning
        
        return " | ".join(parts)
    
    def _clean_name(self, text: str) -> str:
        """Clean entity names: Title Case, trim, normalize spaces and punctuation."""
        if not text:
            return ''
        
        text = str(text).strip()
        
        # Normalize whitespace
        if self.config['normalize_whitespace']:
            text = ' '.join(text.split())
        
        # Remove special characters except alphanumeric, spaces, hyphens, periods
        text = re.sub(r'[^\w\s\-\.]', '', text)
        
        # Normalize consecutive periods to single period
        text = re.sub(r'\.{2,}', '.', text)
        
        # Normalize consecutive hyphens to single hyphen
        text = re.sub(r'-{2,}', '-', text)
        
        # Remove periods that are adjacent to hyphens (.- becomes -, -. becomes -)
        text = re.sub(r'\.-', '-', text)
        text = re.sub(r'-\.', '-', text)
        
        # Clean up spaces around periods and hyphens
        text = re.sub(r'\s*\.\s*', '.', text)
        text = re.sub(r'\s*-\s*', '-', text)
        
        # Final whitespace normalization
        text = ' '.join(text.split())
        
        # Title case
        text = text.title()
        
        return text
    
    def _clean_description(self, text: str) -> str:
        """Clean descriptions: trim, normalize line breaks, remove HTML, Unicode normalize."""
        if not text:
            return ''
        
        text = str(text).strip()
        
        # Normalize Unicode characters
        if self.config.get('normalize_unicode', True):
            text = self._normalize_unicode(text)
        
        # Remove HTML if configured
        if self.config['remove_html']:
            text = self._strip_html(text)
        
        # Remove URLs if configured
        if self.config.get('remove_urls', False):
            text = self._remove_urls(text)
        
        # Remove email addresses if configured
        if self.config.get('remove_email_addresses', False):
            text = self._remove_emails(text)
        
        # Normalize line breaks to pipes (preserves structure)
        if self.config.get('normalize_bullets_to_pipes', True):
            text = self._normalize_line_breaks_to_pipes(text)
        else:
            text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # Remove bullet points if configured
        if self.config.get('remove_bullet_points', True):
            text = self._remove_bullet_prefixes(text)
        
        # Normalize whitespace
        if self.config['normalize_whitespace']:
            text = ' '.join(text.split())
        
        # Apply spelling corrections if enabled (from configurable dict)
        if self.config.get('fix_spelling', False):
            text = self._fix_spelling(text)
        
        # NO LENGTH LIMIT - take full text as requested
        return text
    
    def _clean_category(self, text: str) -> str:
        """Clean category fields: lowercase, trim, normalize."""
        if not text:
            return ''
        
        text = str(text).strip().lower()
        text = ' '.join(text.split())
        text = re.sub(r'[^\w\s\-]', '', text)
        
        return text
    
    def _clean_type_field(self, text: str) -> str:
        """Clean type fields: standardize common values."""
        if not text:
            return ''
        
        text = str(text).strip()
        text = ' '.join(text.split())
        
        # Common standardizations
        standardizations = {
            'internal': 'Internal',
            'external': 'External',
            'standard': 'Standard',
            'procedure': 'Procedure',
            'guideline': 'Guideline',
            'policy': 'Policy',
            'control': 'Control',
            'critical': 'Critical',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low',
        }
        
        lower_text = text.lower()
        return standardizations.get(lower_text, text)
    
    def _clean_identifier(self, text: str) -> str:
        """Clean identifiers: uppercase, trim, normalize."""
        if not text:
            return ''
        
        text = str(text).strip().upper()
        text = ' '.join(text.split())
        
        return text
    
    def _clean_long_text(self, text: str) -> str:
        """Clean long text fields (Scope, Objective, Control): trim, full preservation."""
        if not text:
            return ''
        
        text = str(text).strip()
        
        # Normalize Unicode
        if self.config.get('normalize_unicode', True):
            text = self._normalize_unicode(text)
        
        # Remove HTML
        if self.config['remove_html']:
            text = self._strip_html(text)
        
        # Normalize bullets/line breaks to pipes
        if self.config.get('normalize_bullets_to_pipes', True):
            text = self._normalize_line_breaks_to_pipes(text)
        
        # Remove bullet prefixes
        if self.config.get('remove_bullet_points', True):
            text = self._remove_bullet_prefixes(text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Apply spelling corrections if configured
        if self.config.get('fix_spelling', False):
            text = self._fix_spelling(text)
        
        # NO LENGTH LIMIT - preserve full text
        return text
    
    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ''
        
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        
        return text
    
    def _normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode characters to ASCII equivalents.
        Handles smart quotes, em-dash, en-dash, non-breaking spaces, bullets.
        """
        if not text:
            return ''
        
        import unicodedata
        
        unicode_replacements = {
            '\u2018': "'",
            '\u2019': "'",
            '\u201c': '"',
            '\u201d': '"',
            '\u2013': '-',
            '\u2014': '-',
            '\u2026': '...',
            '\u00a0': ' ',
            '\u2002': ' ',
            '\u2003': ' ',
            '\u2009': ' ',
            '\u00b7': ' ',
            '\u2022': ' ',
            '\u25e6': ' ',
            '\u25aa': ' ',
            '\u25ab': ' ',
        }
        
        for unicode_char, ascii_char in unicode_replacements.items():
            text = text.replace(unicode_char, ascii_char)
        
        text = unicodedata.normalize('NFC', text)
        
        return text
    
    def _remove_urls(self, text: str) -> str:
        """Remove HTTP/HTTPS URLs from text."""
        if not text:
            return ''
        
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        text = re.sub(url_pattern, '', text)
        
        www_pattern = r'www\.(?:[-\w.])+\.\w+(?:/[^\s]*)?'
        text = re.sub(www_pattern, '', text)
        
        return text
    
    def _remove_emails(self, text: str) -> str:
        """Remove email addresses from text."""
        if not text:
            return ''
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.sub(email_pattern, '', text)
    
    def _normalize_line_breaks_to_pipes(self, text: str) -> str:
        """Convert line breaks to pipe separators to preserve structure."""
        if not text:
            return ''
        
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        return ' | '.join(lines)
    
    def _remove_bullet_prefixes(self, text: str) -> str:
        """
        Remove common bullet point prefixes.
        Handles: •, *, -, 1. 2. 3., [ ] [x]
        """
        if not text:
            return ''
        
        bullet_pattern = r'^[\s]*[•\*\-\+\◦\▪\▫\□\■]\s+'
        numbered_pattern = r'^[\s]*\d+[\.\)]\s+'
        checkbox_pattern = r'^[\s]*\[[\sx\]]\s+'
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = re.sub(bullet_pattern, '', line)
            line = re.sub(numbered_pattern, '', line)
            line = re.sub(checkbox_pattern, '', line)
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _fix_spelling(self, text: str) -> str:
        """Fix spelling mistakes using configurable corrections dictionary."""
        corrections = self.config.get('spelling_corrections', {})
        if not corrections:
            return text
        
        words = text.split()
        corrected = []
        
        for word in words:
            lower_word = word.lower()
            if lower_word in corrections:
                corrected.append(self._match_case(word, corrections[lower_word]))
            else:
                # Check for partial word matches
                for typo, fix in corrections.items():
                    if typo in lower_word:
                        new_word = self._match_case(word, lower_word.replace(typo, fix))
                        corrected.append(new_word)
                        break
                else:
                    corrected.append(word)
        
        return ' '.join(corrected)
    
    def _match_case(self, original: str, correction: str) -> str:
        """Match case pattern of original word to correction."""
        if original.isupper():
            return correction.upper()
        elif original.islower():
            return correction.lower()
        elif original[0].isupper():
            return correction.capitalize()
        return correction
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


# ============== Convenience Functions ==============

def clean_framework_text(framework_data: Dict[str, Any], config: Optional[Dict] = None) -> CleaningResult:
    """Convenience function to clean framework data."""
    cleaner = TextCleaner(config)
    return cleaner.clean_framework(framework_data)


def clean_policy_text(policy_data: Dict[str, Any], config: Optional[Dict] = None) -> CleaningResult:
    """Convenience function to clean policy data."""
    cleaner = TextCleaner(config)
    return cleaner.clean_policy(policy_data)


def clean_subpolicy_text(subpolicy_data: Dict[str, Any], config: Optional[Dict] = None) -> CleaningResult:
    """Convenience function to clean sub-policy data."""
    cleaner = TextCleaner(config)
    return cleaner.clean_subpolicy(subpolicy_data)


def clean_compliance_text(compliance_data: Dict[str, Any], config: Optional[Dict] = None) -> CleaningResult:
    """Convenience function to clean compliance data."""
    cleaner = TextCleaner(config)
    return cleaner.clean_compliance(compliance_data)
