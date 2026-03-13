from ...utils.model_router import get_current_system_load, route_model
from ..config import AI_PROVIDER, OLLAMA_MODEL_COMPLEX, OLLAMA_MODEL_DEFAULT, OLLAMA_MODEL_FAST, OPENAI_MODEL
from ..types import AIRequestOptions, ModelDecision


class ModelRoutingService:
    def select_model(self, options: AIRequestOptions, prompt: str = "") -> ModelDecision:
        provider = options.preferred_provider or AI_PROVIDER
        document_size = len(prompt or "")

        if provider == "openai":
            return ModelDecision(
                provider="openai",
                model=options.preferred_model or OPENAI_MODEL,
                reason="OpenAI provider selected",
            )

        try:
            model = route_model(
                task_type=options.task_name or "analysis",
                document_size=document_size,
                accuracy_required="high" if "gap" in (options.task_name or "") else "medium",
                system_load=get_current_system_load(),
            )
            return ModelDecision(provider="ollama", model=model, reason="Heuristic model router selected model")
        except Exception:
            if options.preferred_model:
                return ModelDecision(provider="ollama", model=options.preferred_model, reason="Preferred Ollama model selected")
            if document_size < 2500:
                return ModelDecision(provider="ollama", model=OLLAMA_MODEL_FAST, reason="Short prompt fast-path")
            if document_size > 10000:
                return ModelDecision(provider="ollama", model=OLLAMA_MODEL_COMPLEX, reason="Large prompt complex-path")
            return ModelDecision(provider="ollama", model=OLLAMA_MODEL_DEFAULT, reason="Default Ollama model selected")
