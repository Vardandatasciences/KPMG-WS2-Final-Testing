import json
import time
from functools import lru_cache
from typing import Any

from .config import (
    AI_PROVIDER,
    OLLAMA_TIMEOUT,
    OLLAMA_TEMPERATURE,
    build_generation_options,
    get_quantized_model,
)
from .processing.context import build_context_window
from .prompts import (
    attach_few_shot_examples,
    get_system_prompt,
    optimize_prompt_for_speed,
)
from .providers.ollama_provider import OllamaProvider
from .providers.openai_provider import OpenAIProvider
from .retrieval.rag import RAGService
from .routing.model_router import ModelRoutingService
from .runtime.cache import AIResponseCache
from .runtime.health import get_ai_runtime_health
from .runtime.jobs import AIJobService
from .runtime.metrics import (
    record_ai_call,
    record_cache_hit,
    record_fallback,
    record_rag_usage,
)
from .runtime.queue import AIRequestQueue
from .tasks.policy import POLICY_TASKS
from .tasks.risk import RISK_TASKS
from .tasks.incident import INCIDENT_TASKS
from .tasks.similarity import SIMILARITY_TASKS
from .tasks.gap_analysis import GAP_ANALYSIS_TASKS
from .types import AIRequestOptions, EvidenceSource, InferenceTrace


class AIService:
    def __init__(self):
        self.cache = AIResponseCache()
        self.router = ModelRoutingService()
        self.queue = AIRequestQueue()
        self.jobs = AIJobService("shared")
        self.rag = RAGService()
        self._providers = {
            "ollama": OllamaProvider(),
        }
        try:
            self._providers["openai"] = OpenAIProvider()
        except Exception:
            pass

    def _prepare_prompt(self, task_name: str, prompt: str) -> dict[str, Any]:
        print(f"[AI-SERVICE] _prepare_prompt: task={task_name}, raw_prompt_len={len(prompt)}")
        task_complexity = "full_document" if "ingest_document" in task_name else ("complex" if "gap" in task_name else "medium")
        context = build_context_window(prompt, strategy="balanced", task_complexity=task_complexity)
        optimized = optimize_prompt_for_speed(task_name, context["content"])
        enriched = attach_few_shot_examples(optimized, task_name)
        system_prompt = get_system_prompt(task_name)
        final_prompt = f"System instructions: {system_prompt}\n\n{enriched}"
        print(f"[AI-SERVICE] _prepare_prompt: task={task_name}, final_prompt_len={len(final_prompt)}, truncated={context.get('truncated', False)}")
        return {
            "prompt": final_prompt,
            "context": context,
            "system_prompt": system_prompt,
        }

    def build_inference_trace(
        self,
        *,
        task_name: str,
        provider: str,
        model: str,
        route_reason: str,
        logic: str,
        evidence_sources: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> InferenceTrace:
        sources = [
            EvidenceSource(
                source_type=item.get("source_type", "code"),
                source_id=item.get("source_id", ""),
                label=item.get("label", ""),
                excerpt=item.get("excerpt"),
                metadata=item.get("metadata", {}),
            )
            for item in (evidence_sources or [])
        ]
        return InferenceTrace(
            task_name=task_name,
            provider=provider,
            model=model,
            route_reason=route_reason,
            logic=logic,
            evidence_sources=sources,
            metadata=metadata or {},
        )

    def attach_inference_logic(self, output: Any, trace: InferenceTrace) -> Any:
        trace_payload = {
            "task_name": trace.task_name,
            "provider": trace.provider,
            "model": trace.model,
            "route_reason": trace.route_reason,
            "logic": trace.logic,
            "evidence_sources": [
                {
                    "source_type": item.source_type,
                    "source_id": item.source_id,
                    "label": item.label,
                    "excerpt": item.excerpt,
                    "metadata": item.metadata,
                }
                for item in trace.evidence_sources
            ],
            "metadata": trace.metadata,
        }
        if isinstance(output, dict):
            output.setdefault("_trace", trace_payload)
            return output
        return {
            "result": output,
            "_trace": trace_payload,
        }

    def _normalize_options(self, task_name: str, options: AIRequestOptions | None, **kwargs) -> AIRequestOptions:
        if options is None:
            options = AIRequestOptions(task_name=task_name)
        options.task_name = task_name
        for key, value in kwargs.items():
            if value is not None and hasattr(options, key):
                setattr(options, key, value)
        if options.temperature is None:
            options.temperature = OLLAMA_TEMPERATURE
        if options.timeout is None:
            options.timeout = OLLAMA_TIMEOUT
        return options

    def _get_provider(self, provider_name: str):
        provider = self._providers.get(provider_name)
        if provider is not None:
            return provider
        fallback = self._providers.get(AI_PROVIDER) or next(iter(self._providers.values()))
        return fallback

    def _default_preferred_model(self, task_name: str, preferred_provider: str | None) -> str | None:
        # Only auto-pick quantized models for Ollama.
        # For OpenAI-compatible providers (including NVIDIA), let router/config pick OPENAI_MODEL/NVIDIA model.
        provider = (preferred_provider or AI_PROVIDER or "").lower()
        if provider == "ollama":
            return get_quantized_model(task_name)
        return None

    def generate_text(
        self,
        *,
        task_name: str,
        prompt: str,
        options: AIRequestOptions | None = None,
        preferred_provider: str | None = None,
        preferred_model: str | None = None,
        timeout: int | None = None,
        retries: int | None = None,
    ) -> str:
        resolved = self._normalize_options(
            task_name,
            options,
            preferred_provider=preferred_provider,
            preferred_model=preferred_model or self._default_preferred_model(task_name, preferred_provider),
            timeout=timeout,
            retries=retries,
        )
        prepared_prompt = self._prepare_prompt(task_name, prompt)
        generation_options = build_generation_options(task_name, resolved.temperature)
        resolved.temperature = generation_options["temperature"]
        decision = self.router.select_model(resolved, prepared_prompt["prompt"])
        provider = self._get_provider(decision.provider)
        started = time.perf_counter()
        try:
            result = provider.generate_text(
                prepared_prompt["prompt"],
                model=decision.model,
                temperature=resolved.temperature or 0.1,
                timeout=resolved.timeout or OLLAMA_TIMEOUT,
                retries=resolved.retries,
            )
            record_ai_call(task_name, decision.provider, decision.model, (time.perf_counter() - started) * 1000, True)
            return result
        except Exception:
            record_ai_call(task_name, decision.provider, decision.model, (time.perf_counter() - started) * 1000, False)
            raise

    def generate_json(
        self,
        *,
        task_name: str,
        prompt: str,
        options: AIRequestOptions | None = None,
        preferred_provider: str | None = None,
        preferred_model: str | None = None,
        timeout: int | None = None,
        retries: int | None = None,
    ) -> Any:
        resolved = self._normalize_options(
            task_name,
            options,
            preferred_provider=preferred_provider,
            preferred_model=preferred_model or self._default_preferred_model(task_name, preferred_provider),
            timeout=timeout,
            retries=retries,
        )
        if task_name.startswith("risk."):
            print(f"[AI-RISK] generate_json start: task={task_name}")
        if task_name.startswith("incident."):
            print(f"[AI-INCIDENT] generate_json start: task={task_name}")
        if task_name.startswith("policy."):
            print(f"[AI-POLICY] 🤖 Centralized AI call: task={task_name}")
        if task_name.startswith("compliance."):
            print(f"[AI-COMPLIANCE] Centralized AI call: task={task_name}")
        if task_name.startswith("similarity."):
            print(f"[AI-SIMILARITY] 🔍 Centralized similarity analysis: task={task_name}")
        if task_name.startswith("gap_analysis."):
            print(f"[AI-GAP-ANALYSIS] 📊 Centralized gap analysis: task={task_name}")
        prepared_prompt = self._prepare_prompt(task_name, prompt)
        generation_options = build_generation_options(task_name, resolved.temperature)
        resolved.temperature = generation_options["temperature"]
        decision = self.router.select_model(resolved, prepared_prompt["prompt"])
        provider = self._get_provider(decision.provider)
        if task_name.startswith("risk."):
            print(
                f"[AI-RISK] model decision: task={task_name}, "
                f"provider={decision.provider}, model={decision.model}, reason={decision.reason}"
            )
        if task_name.startswith("incident."):
            print(
                f"[AI-INCIDENT] model decision: task={task_name}, "
                f"provider={decision.provider}, model={decision.model}, reason={decision.reason}"
            )
        if task_name.startswith("policy."):
            print(
                f"[AI-POLICY] 🤖 Model: provider={decision.provider}, model={decision.model}, reason={decision.reason}"
            )
        if task_name.startswith("compliance."):
            print(
                f"[AI-COMPLIANCE] Model: provider={decision.provider}, model={decision.model}, reason={decision.reason}"
            )
        if task_name.startswith("similarity."):
            print(
                f"[AI-SIMILARITY] 🔍 Model: provider={decision.provider}, model={decision.model}, reason={decision.reason}"
            )
        if task_name.startswith("gap_analysis."):
            print(
                f"[AI-GAP-ANALYSIS] 📊 Model: provider={decision.provider}, model={decision.model}, reason={decision.reason}"
            )
        ttl = 86400 if len(prepared_prompt["prompt"]) > 2000 else 3600

        def _callback():
            started = time.perf_counter()
            result = provider.generate_json(
                prepared_prompt["prompt"],
                model=decision.model,
                temperature=resolved.temperature or 0.1,
                timeout=resolved.timeout or OLLAMA_TIMEOUT,
                retries=resolved.retries,
            )
            record_ai_call(task_name, decision.provider, decision.model, (time.perf_counter() - started) * 1000, True)
            return result

        result = self.cache.get_or_set(
            task_name=task_name,
            provider=decision.provider,
            model=decision.model,
            prompt=prepared_prompt["prompt"],
            callback=_callback,
            document_hash=resolved.document_hash,
            schema_version=resolved.schema_version,
            ttl=ttl,
            use_cache=resolved.use_cache,
        )
        if task_name.startswith("risk."):
            cache_flag = "enabled" if resolved.use_cache else "disabled"
            print(f"[AI-RISK] cache {cache_flag} for task={task_name}, provider={decision.provider}, model={decision.model}")
        if task_name.startswith("incident."):
            cache_flag = "enabled" if resolved.use_cache else "disabled"
            print(f"[AI-INCIDENT] cache {cache_flag} for task={task_name}, provider={decision.provider}, model={decision.model}")
        if task_name.startswith("policy."):
            cache_flag = "enabled" if resolved.use_cache else "disabled"
            print(f"[AI-POLICY] 🤖 Cache {cache_flag} | task={task_name}")
        if task_name.startswith("compliance."):
            cache_flag = "enabled" if resolved.use_cache else "disabled"
            print(f"[AI-COMPLIANCE] Cache {cache_flag} | task={task_name}")
        if resolved.use_cache:
            record_cache_hit(task_name, decision.model)

        if self.rag.available() and resolved.metadata.get("rag_chunks_used"):
            record_rag_usage(task_name, resolved.metadata["rag_chunks_used"])

        if resolved.include_trace:
            trace = self.build_inference_trace(
                task_name=task_name,
                provider=decision.provider,
                model=decision.model,
                route_reason=decision.reason,
                logic=f"Prompt was optimized for speed and context budget before execution. System prompt category: {prepared_prompt['system_prompt']}",
                evidence_sources=resolved.metadata.get("evidence_sources", []),
                metadata={
                    "context_strategy": prepared_prompt["context"]["strategy"],
                    "context_truncated": prepared_prompt["context"]["truncated"],
                    "sampling": generation_options,
                },
            )
            result = self.attach_inference_logic(result, trace)

        # Print full AI output to terminal for all centralized AI calls
        def _print_ai_output(prefix: str, task_name: str, result: Any):
            try:
                if isinstance(result, dict):
                    keys = list(result.keys())
                    print(f"{prefix} generate_json result dict for task={task_name}, keys={keys}")
                    out_str = json.dumps(result, default=str, ensure_ascii=False)
                    max_len = 2000  # Truncate very long outputs
                    if len(out_str) > max_len:
                        print(f"{prefix} AI OUTPUT (truncated to {max_len} chars):\n{out_str[:max_len]}...")
                    else:
                        print(f"{prefix} AI OUTPUT:\n{out_str}")
                elif isinstance(result, list):
                    print(f"{prefix} generate_json result list for task={task_name}, len={len(result)}")
                    out_str = json.dumps(result, default=str, ensure_ascii=False)
                    max_len = 2000
                    if len(out_str) > max_len:
                        print(f"{prefix} AI OUTPUT (truncated to {max_len} chars):\n{out_str[:max_len]}...")
                    else:
                        print(f"{prefix} AI OUTPUT:\n{out_str}")
                else:
                    print(f"{prefix} generate_json result type for task={task_name}: {type(result).__name__} = {result}")
            except Exception as e:
                print(f"{prefix} AI OUTPUT print failed: {e}")

        prefix = "[AI-RISK]" if task_name.startswith("risk.") else "[AI-INCIDENT]" if task_name.startswith("incident.") else "[AI-POLICY]" if task_name.startswith("policy.") else "[AI]"
        _print_ai_output(prefix, task_name, result)

        return result

    def embed(self, text: str, metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None) -> list[float]:
        resolved = self._normalize_options("embedding", options)
        decision = self.router.select_model(resolved, text)
        provider = self._get_provider(decision.provider)
        return provider.embed(text, model=decision.model, timeout=resolved.timeout or 60)

    def ingest_knowledge(self, document_text: str, document_id: str, metadata: dict[str, Any] | None = None):
        return self.rag.ingest_document(document_text, document_id, metadata=metadata)

    def retrieve_knowledge(self, query: str, filters: dict[str, Any] | None = None, limit: int = 5):
        return self.rag.retrieve_context(query, limit=limit)

    def get_job_status(self, job_id: str):
        return self.jobs.get_job_status(job_id)

    def generate_policy_bundle_from_text(
        self,
        document_text: str,
        extra_payload: dict[str, Any] | None = None,
        extra_metadata: dict[str, Any] | None = None,
        options: AIRequestOptions | None = None,
    ) -> Any:
        """
        Centralized helper for policy/subpolicy/compliance generation.

        Pipeline:
        - Preprocess the raw document text via DocumentPreparationService (control chars, whitespace, lemmatization, truncation).
        - Attach preprocessing metadata + document_hash for caching.
        - Call the high-level task `policy.generate_policy_with_compliances`.
        """
        from .processing.preprocessor import DocumentPreparationService

        prep_service = DocumentPreparationService()
        prepared = prep_service.prepare_text(document_text)
        processed_text: str = prepared.get("text", "")
        prep_metadata: dict[str, Any] = prepared.get("metadata", {})

        payload: dict[str, Any] = {"document_text": processed_text}
        if extra_payload:
            payload.update(extra_payload)

        merged_metadata: dict[str, Any] = {"preprocessing": prep_metadata}
        if extra_metadata:
            merged_metadata.update(extra_metadata)

        resolved_options = options or AIRequestOptions(task_name="policy.generate_policy_with_compliances")
        resolved_options.task_name = "policy.generate_policy_with_compliances"
        if not resolved_options.document_hash:
            resolved_options.document_hash = prep_metadata.get("document_hash")
        # Preserve any existing metadata but ensure preprocessing info is attached
        resolved_options.metadata = {
            **resolved_options.metadata,
            "preprocessing": prep_metadata,
        }

        return self.run_task(
            "policy.generate_policy_with_compliances",
            payload,
            metadata=merged_metadata,
            options=resolved_options,
        )

    def health(self) -> dict[str, Any]:
        return get_ai_runtime_health(list(self._providers.keys()), self.rag.available())

    def run_task(
        self,
        task_name: str,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        options: AIRequestOptions | None = None,
    ) -> Any:
        if task_name.startswith("risk."):
            print(
                f"[AI-RISK] run_task start: task={task_name}, "
                f"payload_keys={list(payload.keys())}, metadata_keys={list((metadata or {}).keys())}"
            )
        if task_name.startswith("incident."):
            print(
                f"[AI-INCIDENT] run_task start: task={task_name}, "
                f"payload_keys={list(payload.keys())}, metadata_keys={list((metadata or {}).keys())}"
            )
        if task_name.startswith("similarity."):
            print(
                f"[AI-SIMILARITY] 🔍 run_task start: task={task_name}, "
                f"payload_keys={list(payload.keys())}, metadata_keys={list((metadata or {}).keys())}"
            )
        if task_name.startswith("gap_analysis."):
            print(
                f"[AI-GAP-ANALYSIS] 📊 run_task start: task={task_name}, "
                f"payload_keys={list(payload.keys())}, metadata_keys={list((metadata or {}).keys())}"
            )
        task = {
            **POLICY_TASKS,
            **RISK_TASKS,
            **INCIDENT_TASKS,
            **SIMILARITY_TASKS,
            **GAP_ANALYSIS_TASKS,
        }.get(task_name)
        if task is None:
            raise RuntimeError(f"Unknown AI task: {task_name}")
        result = task(self, payload, metadata=metadata or {}, options=options)
        if task_name.startswith("risk."):
            if isinstance(result, dict):
                r_keys = list(result.keys())
                print(f"[AI-RISK] run_task done: task={task_name}, result_keys={r_keys}")
            else:
                print(f"[AI-RISK] run_task done: task={task_name}, result_type={type(result).__name__}")
        if task_name.startswith("incident."):
            if isinstance(result, dict):
                r_keys = list(result.keys())
                print(f"[AI-INCIDENT] run_task done: task={task_name}, result_keys={r_keys}")
            else:
                print(f"[AI-INCIDENT] run_task done: task={task_name}, result_type={type(result).__name__}")
        if task_name.startswith("similarity."):
            if isinstance(result, dict):
                r_keys = list(result.keys())
                print(f"[AI-SIMILARITY] 🔍 run_task done: task={task_name}, result_keys={r_keys}")
            else:
                print(f"[AI-SIMILARITY] 🔍 run_task done: task={task_name}, result_type={type(result).__name__}")
        if task_name.startswith("gap_analysis."):
            if isinstance(result, dict):
                r_keys = list(result.keys())
                print(f"[AI-GAP-ANALYSIS] 📊 run_task done: task={task_name}, result_keys={r_keys}")
            else:
                print(f"[AI-GAP-ANALYSIS] 📊 run_task done: task={task_name}, result_type={type(result).__name__}")
        return result


@lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    return AIService()


def legacy_call_openai_json(prompt: str, retries: int = 3, timeout: int = 120, document_hash: str | None = None, use_cache: bool = True):
    service = get_ai_service()
    options = AIRequestOptions(
        task_name="legacy.openai_json",
        preferred_provider="openai",
        retries=retries,
        timeout=timeout,
        document_hash=document_hash,
        use_cache=use_cache,
    )
    try:
        return service.generate_json(task_name="legacy.openai_json", prompt=prompt, options=options)
    except Exception:
        record_fallback("openai", AI_PROVIDER)
        raise


def legacy_call_ollama_json(
    prompt: str,
    model: str | None = None,
    retries: int = 2,
    timeout: int | None = None,
    document_hash: str | None = None,
    use_cache: bool = True,
):
    service = get_ai_service()
    options = AIRequestOptions(
        task_name="legacy.ollama_json",
        preferred_provider="ollama",
        preferred_model=model,
        retries=retries,
        timeout=timeout or OLLAMA_TIMEOUT,
        document_hash=document_hash,
        use_cache=use_cache,
    )
    try:
        return service.generate_json(task_name="legacy.ollama_json", prompt=prompt, options=options)
    except Exception:
        record_fallback("ollama", AI_PROVIDER)
        raise
