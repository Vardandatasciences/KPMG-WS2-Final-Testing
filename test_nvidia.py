"""
NVIDIA API Model Tester
Test NVIDIA NIM models with simple Q&A
"""

from openai import OpenAI

# ── Configuration ──────────────────────────────────────────────────────────────
NVIDIA_API_KEY = "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"   # <-- Replace with your key
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "nvidia/nemotron-3-nano-30b-a3b"



# Popular NVIDIA NIM models to choose from:
AVAILABLE_MODELS = {
    "1": ("meta/llama-3.3-70b-instruct",   "Llama 3.3 70B Instruct"),
    "2": ("meta/llama-3.1-8b-instruct",    "Llama 3.1 8B Instruct (faster)"),
    "3": ("mistralai/mistral-7b-instruct", "Mistral 7B Instruct"),
    "4": ("google/gemma-7b",               "Google Gemma 7B"),
    "5": ("nvidia/llama3-chatqa-1.5-70b",  "NVIDIA ChatQA 1.5 70B"),
}

# ── Client Setup ───────────────────────────────────────────────────────────────
client = OpenAI(
    base_url=NVIDIA_BASE_URL,
    api_key=NVIDIA_API_KEY,
)


def list_models():
    """Print available models."""
    print("\n📦 Available Models:")
    for key, (model_id, label) in AVAILABLE_MODELS.items():
        print(f"  [{key}] {label}")
        print(f"       {model_id}")


def ask_question(question: str, model_id: str, system_prompt: str = None) -> str:
    """Send a question to the NVIDIA API and return the answer."""
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )

    return response.choices[0].message.content


def interactive_mode(model_id: str):
    """Run an interactive Q&A session."""
    print(f"\n💬 Interactive Q&A — Model: {model_id}")
    print("   Type 'quit' or 'exit' to stop.\n")

    system_prompt = "You are a helpful, concise assistant."

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Exiting.")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            print("👋 Goodbye!")
            break

        print("AI : ", end="", flush=True)
        try:
            answer = ask_question(question, model_id, system_prompt)
            print(answer)
        except Exception as e:
            print(f"[Error] {e}")
        print()


def batch_test(model_id: str):
    """Run a quick batch of preset questions."""
    questions = [
        "What is the capital of France?",
        "Explain quantum computing in one sentence.",
        "Write a haiku about artificial intelligence.",
        "What is 17 multiplied by 23?",
        "Name three programming languages created after 2010.",
    ]

    print(f"\n🧪 Batch Test — Model: {model_id}\n")
    for i, q in enumerate(questions, 1):
        print(f"Q{i}: {q}")
        try:
            answer = ask_question(q, model_id)
            print(f"A{i}: {answer}\n")
        except Exception as e:
            print(f"A{i}: [Error] {e}\n")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("   🚀  NVIDIA API Model Tester")
    print("=" * 55)

    # Pick a model
    list_models()
    choice = input("\nSelect model [1-5] (default 1): ").strip() or "1"
    model_id, label = AVAILABLE_MODELS.get(choice, AVAILABLE_MODELS["1"])
    print(f"\n✅ Using: {label}")

    # Pick mode
    print("\n🔧 Test Mode:")
    print("  [1] Interactive Q&A")
    print("  [2] Batch test (preset questions)")
    mode = input("Choose [1/2] (default 1): ").strip() or "1"

    if mode == "2":
        batch_test(model_id)
    else:
        interactive_mode(model_id)


if __name__ == "__main__":
    main()