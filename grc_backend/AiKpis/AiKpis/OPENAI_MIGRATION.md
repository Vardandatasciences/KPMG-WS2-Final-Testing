# OpenAI Migration Guide

## Overview
The AiKpis module has been migrated from Ollama to OpenAI for both KPI generation and semantic embeddings.

## What Changed

### 1. **Configuration (`config.py`)**
- **Removed**: Ollama configuration (OLLAMA_BASE_URL, OLLAMA_MODEL)
- **Added**: OpenAI configuration (OPENAI_API_KEY, OPENAI_MODEL)
- **Removed**: KeyBERT and sentence-transformers dependencies
- **Added**: OpenAI SDK and embedding model configuration
- **Changed**: Global model instances now use OpenAI client instead of sentence transformers

### 2. **KPI Generation (`ollama_client.py`)**
- **Renamed**: File still named `ollama_client.py` but now uses OpenAI
- **Changed**: All API calls now use OpenAI's Chat Completions API
- **Changed**: Uses `response_format={"type": "json_object"}` for structured JSON output
- **Improved**: Better JSON parsing with OpenAI's native JSON mode
- **Removed**: Ollama-specific request handling

### 3. **Evidence Processing (`evidence.py`)**
- **Removed**: KeyBERT keyword extraction
- **Removed**: sentence-transformers for embeddings
- **Added**: OpenAI embeddings API (`text-embedding-3-small`)
- **Added**: Embedding caching to reduce API calls
- **Added**: Custom cosine similarity calculation using numpy
- **Changed**: Semantic matching now uses OpenAI embeddings
- **Simplified**: Chunk scoring uses simple keyword matching instead of KeyBERT

### 4. **Dependencies (`requirements.txt`)**
- **Removed**: keybert, sentence-transformers, json-repair
- **Added**: openai>=1.0.0, numpy
- **Kept**: langchain, langchain-text-splitters (for text chunking)

## Configuration Required

### 1. **Django Settings**
Ensure these are set in `backend/backend/settings.py`:

```python
OPENAI_API_KEY = "sk-proj-..."  # Your OpenAI API key
OPENAI_MODEL = "gpt-3.5-turbo"  # or "gpt-4" for better quality
```

### 2. **Environment Variables (Alternative)**
You can also set these as environment variables:

```bash
export OPENAI_API_KEY="sk-proj-..."
export OPENAI_MODEL="gpt-4"
```

## Installation

### 1. **Install New Dependencies**
```bash
cd backend/grc/AiKpis
pip install -r requirements.txt
```

### 2. **Uninstall Old Dependencies (Optional)**
```bash
pip uninstall keybert sentence-transformers json-repair -y
```

## Usage

No changes to the command-line interface:

```bash
# Same as before
python -m backend.grc.AiKpis.generateFrameworkKpi --framework-id 336
```

## Key Improvements

### 1. **Better JSON Generation**
- OpenAI's native JSON mode ensures valid JSON output
- No more truncated responses or malformed JSON
- Cleaner parsing with less error handling needed

### 2. **Higher Quality Embeddings**
- OpenAI's `text-embedding-3-small` is more accurate than sentence-transformers
- Faster API calls compared to local model inference
- Consistent results across different environments

### 3. **Simpler Dependencies**
- No need to download large ML models (sentence-transformers ~400MB)
- Faster installation and deployment
- Works on any machine with internet access

### 4. **Cost Considerations**
- **KPI Generation**: ~$0.002 per KPI (using gpt-3.5-turbo)
- **Embeddings**: ~$0.0001 per 1K tokens
- **Caching**: Embeddings are cached to minimize API calls

## API Costs Estimate

For a typical framework with 5 modules:
- **KPI Generation**: 5 modules × 12 KPIs × $0.002 = ~$0.12
- **Embeddings**: ~50 documents × $0.0001 = ~$0.005
- **Total per run**: ~$0.13

## Troubleshooting

### Error: "OPENAI_API_KEY not configured"
**Solution**: Set the API key in `backend/backend/settings.py` or as an environment variable.

### Error: "OpenAI SDK not available"
**Solution**: Install the OpenAI SDK:
```bash
pip install openai>=1.0.0
```

### Error: "Rate limit exceeded"
**Solution**: 
- Wait a few seconds and retry
- Upgrade your OpenAI plan for higher rate limits
- Add retry logic with exponential backoff

### Slow Performance
**Solution**:
- Embeddings are cached automatically
- Use `gpt-3.5-turbo` instead of `gpt-4` for faster responses
- Reduce `--max-s3-docs` to process fewer documents

## Rollback (If Needed)

If you need to rollback to Ollama:

1. Restore the old files from git:
```bash
git checkout HEAD~1 backend/grc/AiKpis/config.py
git checkout HEAD~1 backend/grc/AiKpis/ollama_client.py
git checkout HEAD~1 backend/grc/AiKpis/evidence.py
git checkout HEAD~1 backend/grc/AiKpis/requirements.txt
```

2. Reinstall old dependencies:
```bash
pip install keybert sentence-transformers
```

## Testing

Test the migration with a small framework:

```bash
# Test with default framework
python -m backend.grc.AiKpis.generateFrameworkKpi --framework-id 336 --max-s3-docs 2

# Check the logs for:
# [INFO] [API_CALL] Calling OpenAI API
# [INFO] [S3_EVIDENCE] OpenAI client initialized for embeddings
```

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify your OpenAI API key is valid
3. Ensure you have sufficient OpenAI credits
4. Review the `OPENAI_MIGRATION.md` file

## Future Enhancements

Potential improvements:
- Add support for Azure OpenAI endpoints
- Implement streaming responses for real-time feedback
- Add fine-tuned models for domain-specific KPIs
- Batch embedding requests for better performance

