"""
Advanced Model Routing System for Phase 3
- Intelligently selects the best AI model based on multiple factors
- Considers document size, task complexity, accuracy requirements, system load
"""

import time
import logging
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

# Model performance profiles
MODEL_PROFILES = {
    "llama3.2:1b-instruct-q4_K_M": {
        "speed": "very_fast",
        "accuracy": "good",
        "cost": "very_low",
        "max_context": 2000,
        "best_for": ["simple_queries", "field_extraction", "low_accuracy_required"]
    },
    "llama3.2:3b-instruct-q4_K_M": {
        "speed": "fast",
        "accuracy": "very_good",
        "cost": "low",
        "max_context": 4000,
        "best_for": ["general_tasks", "medium_complexity", "balanced"]
    },
    "llama3:8b-instruct-q4_K_M": {
        "speed": "medium",
        "accuracy": "excellent",
        "cost": "medium",
        "max_context": 8000,
        "best_for": ["complex_analysis", "high_accuracy_required", "large_documents"]
    },
    "gpt-4o-mini": {
        "speed": "fast",
        "accuracy": "excellent",
        "cost": "medium",
        "max_context": 128000,
        "best_for": ["general_tasks", "high_accuracy", "openai_preferred"]
    }
}

# System load tracking (simple in-memory tracker)
_system_load_history = []
_max_load_history = 100

def track_system_load(processing_time: float, document_size: int):
    """Track system load for routing decisions."""
    global _system_load_history
    
    load_metric = {
        "timestamp": time.time(),
        "processing_time": processing_time,
        "document_size": document_size,
        "load_score": (processing_time / 10.0) * (document_size / 10000.0)  # Simple load score
    }
    
    _system_load_history.append(load_metric)
    
    # Keep only recent history
    if len(_system_load_history) > _max_load_history:
        _system_load_history = _system_load_history[-_max_load_history:]
    
    return load_metric

def get_current_system_load() -> float:
    """Calculate current system load (0.0 to 1.0)."""
    if not _system_load_history:
        return 0.0
    
    # Get recent load (last 5 minutes)
    current_time = time.time()
    recent_loads = [
        l for l in _system_load_history
        if current_time - l["timestamp"] < 300  # 5 minutes
    ]
    
    if not recent_loads:
        return 0.0
    
    # Average load score, normalized
    avg_load = sum(l["load_score"] for l in recent_loads) / len(recent_loads)
    return min(1.0, avg_load / 10.0)  # Normalize to 0-1

def route_model(
    task_type: str = "general",
    document_size: int = 0,
    text_length: int = 0,
    num_risks: int = 1,
    accuracy_required: str = "medium",
    system_load: Optional[float] = None,
    provider: str = "ollama"
) -> str:
    """
    Intelligently route to the best model for the task.
    
    Args:
        task_type: Type of task (simple_query, field_extraction, complex_analysis, etc.)
        document_size: Size of document in bytes
        text_length: Length of text in characters
        num_risks: Number of risks to extract
        accuracy_required: "low", "medium", "high", "critical"
        system_load: Current system load (0.0-1.0), auto-calculated if None
        provider: "ollama" or "openai"
    
    Returns:
        Model name to use
    """
    # Get system load if not provided
    if system_load is None:
        system_load = get_current_system_load()
    
    # Use text_length if document_size not provided
    if document_size == 0 and text_length > 0:
        document_size = text_length
    
    # Determine task complexity
    if task_type in ["simple_query", "field_extraction"]:
        complexity = "simple"
    elif task_type in ["complex_analysis", "multi_risk_extraction"]:
        complexity = "complex"
    else:
        complexity = "medium"
    
    # Adjust complexity based on document size and number of risks
    if document_size > 50000 or num_risks > 5:
        complexity = "complex"
    elif document_size < 2000 and num_risks == 1:
        complexity = "simple"
    
    # Route based on provider
    if provider == "openai":
        # For OpenAI, use configured model (usually gpt-4o-mini)
        from django.conf import settings
        return getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
    
    # Ollama routing logic
    ollama_models = {
        "fast": "llama3.2:1b-instruct-q4_K_M",
        "default": "llama3.2:3b-instruct-q4_K_M",
        "complex": "llama3:8b-instruct-q4_K_M"
    }
    
    # High system load -> use faster model
    if system_load > 0.8:
        logger.info(f"🔄 High system load ({system_load:.2f}), routing to fast model")
        return ollama_models["fast"]
    
    # Critical accuracy required -> use complex model
    if accuracy_required == "critical":
        logger.info(f"🎯 Critical accuracy required, routing to complex model")
        return ollama_models["complex"]
    
    # High accuracy required -> use complex model (unless system overloaded)
    if accuracy_required == "high" and system_load < 0.7:
        logger.info(f"🎯 High accuracy required, routing to complex model")
        return ollama_models["complex"]
    
    # Simple task -> use fast model
    if complexity == "simple" and document_size < 2000:
        logger.info(f"⚡ Simple task, routing to fast model")
        return ollama_models["fast"]
    
    # Complex task -> use complex model (if not overloaded)
    if complexity == "complex" and system_load < 0.7:
        logger.info(f"🧠 Complex task, routing to complex model")
        return ollama_models["complex"]
    
    # Default -> balanced model
    logger.info(f"⚖️  Balanced routing, using default model")
    return ollama_models["default"]

def get_model_recommendation(
    task_description: str,
    document_size: int = 0,
    accuracy_required: str = "medium"
) -> Dict[str, Any]:
    """
    Get model recommendation with reasoning.
    
    Returns:
        Dict with recommended model and reasoning
    """
    system_load = get_current_system_load()
    recommended_model = route_model(
        task_type="general",
        document_size=document_size,
        accuracy_required=accuracy_required,
        system_load=system_load
    )
    
    profile = MODEL_PROFILES.get(recommended_model, {})
    
    return {
        "recommended_model": recommended_model,
        "reasoning": {
            "system_load": system_load,
            "document_size": document_size,
            "accuracy_required": accuracy_required,
            "model_profile": profile
        },
        "alternatives": {
            "faster": "llama3.2:1b-instruct-q4_K_M" if recommended_model != "llama3.2:1b-instruct-q4_K_M" else None,
            "more_accurate": "llama3:8b-instruct-q4_K_M" if recommended_model != "llama3:8b-instruct-q4_K_M" else None
        }
    }












