"""
Centralized AI Tasks Registry
Imports and registers all AI tasks for the centralized AI service.
"""

from .policy import POLICY_TASKS
from .risk import RISK_TASKS  
from .incident import INCIDENT_TASKS
from .similarity import SIMILARITY_TASKS
from .gap_analysis import GAP_ANALYSIS_TASKS

# Combined registry of all AI tasks
ALL_AI_TASKS = {
    **POLICY_TASKS,
    **RISK_TASKS,
    **INCIDENT_TASKS, 
    **SIMILARITY_TASKS,
    **GAP_ANALYSIS_TASKS,
}

# Export individual task registries for targeted imports
__all__ = [
    'ALL_AI_TASKS',
    'POLICY_TASKS', 
    'RISK_TASKS',
    'INCIDENT_TASKS',
    'SIMILARITY_TASKS', 
    'GAP_ANALYSIS_TASKS',
]