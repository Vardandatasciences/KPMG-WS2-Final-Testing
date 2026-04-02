"""
Centralized caps for potentially large in-memory collections.
"""

from __future__ import annotations

from typing import Any

# Prevent excessive module-name checks when mapping integration events.
MAX_INTEGRATION_MODULE_NAMES_CHECK = 200

# Limit fallback temp section copies in upload framework flow.
MAX_DEFAULT_TEMP_SECTIONS = 200

# Cap extracted framework policy/subpolicy payload sizes.
MAX_FRAMEWORK_POLICIES = 2000
MAX_FRAMEWORK_SUBPOLICIES_PER_POLICY = 500


def cap_extracted_framework_policies(extracted_data: Any) -> None:
    """
    Mutate extracted framework payload in-place and cap policy list sizes.

    The codebase passes dict payloads with keys like `Policies` / `SubPolicies`.
    This helper safely handles mixed shapes and leaves unknown shapes untouched.
    """
    if not isinstance(extracted_data, dict):
        return

    policies_key = None
    for key in ("Policies", "policies", "Policy", "policy"):
        if key in extracted_data and isinstance(extracted_data[key], list):
            policies_key = key
            break

    if not policies_key:
        return

    policies = extracted_data[policies_key]
    if len(policies) > MAX_FRAMEWORK_POLICIES:
        extracted_data[policies_key] = policies[:MAX_FRAMEWORK_POLICIES]
        policies = extracted_data[policies_key]

    for item in policies:
        if not isinstance(item, dict):
            continue
        for sub_key in ("SubPolicies", "subPolicies", "subpolicies", "SubPolicy"):
            if sub_key in item and isinstance(item[sub_key], list):
                if len(item[sub_key]) > MAX_FRAMEWORK_SUBPOLICIES_PER_POLICY:
                    item[sub_key] = item[sub_key][:MAX_FRAMEWORK_SUBPOLICIES_PER_POLICY]

