def calculate_optimal_context_size(text_length: int, task_complexity: str = "medium") -> int:
    base_sizes = {
        "simple": 1000,
        "medium": 2000,
        "complex": 4000,
        "full_document": 16000,  # For ingest tasks - need full doc to extract all incidents
    }
    base = base_sizes.get(task_complexity, 2000)
    if task_complexity == "full_document":
        size = min(text_length, base)  # Use full document up to base limit
    elif text_length < 1000:
        size = min(1000, base)
    elif text_length < 5000:
        size = min(2000, base)
    elif text_length < 10000:
        size = min(3000, base)
    else:
        size = min(4000, base)
    print(f"[AI-CONTEXT] calculate_optimal_context_size: text_len={text_length}, complexity={task_complexity} -> max_context={size}")
    return size


def truncate_for_context_budget(text: str, max_context: int) -> str:
    if len(text) <= max_context:
        return text
    side = max_context // 2
    truncated = f"{text[:side]}\n\n[... content truncated for context budget ...]\n\n{text[-side:]}"
    print(f"[AI-CONTEXT] truncate_for_context_budget: {len(text)} -> {len(truncated)} chars (head+tail, max_context={max_context})")
    return truncated


def build_context_window(text: str, strategy: str = "balanced", task_complexity: str = "medium") -> dict:
    max_context = calculate_optimal_context_size(len(text), task_complexity=task_complexity)
    if strategy == "head":
        content = text[:max_context]
        print(f"[AI-CONTEXT] build_context_window: strategy=head, kept first {len(content)} chars")
    elif strategy == "tail":
        content = text[-max_context:]
        print(f"[AI-CONTEXT] build_context_window: strategy=tail, kept last {len(content)} chars")
    else:
        content = truncate_for_context_budget(text, max_context)
        print(f"[AI-CONTEXT] build_context_window: strategy=balanced, result={len(content)} chars, truncated={len(text) > max_context}")
    return {
        "content": content,
        "max_context": max_context,
        "strategy": strategy,
        "original_length": len(text),
        "truncated": len(text) > max_context,
    }
