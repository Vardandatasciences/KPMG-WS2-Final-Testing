def calculate_optimal_context_size(text_length: int, task_complexity: str = "medium") -> int:
    base_sizes = {
        "simple": 1000,
        "medium": 2000,
        "complex": 4000,
    }
    base = base_sizes.get(task_complexity, 2000)
    if text_length < 1000:
        return min(1000, base)
    if text_length < 5000:
        return min(2000, base)
    if text_length < 10000:
        return min(3000, base)
    return min(4000, base)


def truncate_for_context_budget(text: str, max_context: int) -> str:
    if len(text) <= max_context:
        return text
    side = max_context // 2
    return f"{text[:side]}\n\n[... content truncated for context budget ...]\n\n{text[-side:]}"


def build_context_window(text: str, strategy: str = "balanced", task_complexity: str = "medium") -> dict:
    max_context = calculate_optimal_context_size(len(text), task_complexity=task_complexity)
    if strategy == "head":
        content = text[:max_context]
    elif strategy == "tail":
        content = text[-max_context:]
    else:
        content = truncate_for_context_budget(text, max_context)
    return {
        "content": content,
        "max_context": max_context,
        "strategy": strategy,
        "original_length": len(text),
        "truncated": len(text) > max_context,
    }
