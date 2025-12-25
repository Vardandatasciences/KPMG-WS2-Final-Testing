# AI Performance Comparison Report Guide

## Overview

This report compares **OpenAI** vs **Ollama (Phase 1, 2, 3 Optimized)** across three document types:
1. **Risk Document** (`risk_register3.pdf`)
2. **Incident Document** (`incident_report_1.pdf`)
3. **Policy Document** (`PCI_DSS_1.pdf`)

## Report Contents

### 1. Executive Summary
- Total processing time comparison
- Overall speed improvement percentage
- Key findings and recommendations

### 2. Performance Charts
- **Processing Time Comparison**: Bar chart showing time for each document type
- **Extraction Count Comparison**: Number of items extracted by each provider
- **Speed Improvement**: Percentage improvement with Ollama
- **Similarity Scores**: How similar are the results between providers

### 3. Detailed Analysis per Document Type

#### Risk Document Analysis
- Processing time (OpenAI vs Ollama)
- Number of risks extracted
- Similarity score between results
- Cache hit statistics
- Sample extracted risks

#### Incident Document Analysis
- Processing time comparison
- Number of incidents extracted
- Similarity analysis
- Performance metrics

#### Policy Document Analysis
- Processing time comparison
- Number of policies/subpolicies extracted
- Extraction success rate
- Performance metrics

### 4. Phase Optimizations Proof

#### Phase 1 (Quick Wins)
- ✅ Quantized Ollama models (1B, 3B, 8B)
- ✅ Dynamic context window sizing
- ✅ Model selection by complexity
- **Proof**: Model routing logs, context optimization metrics

#### Phase 2 (Medium-Term)
- ✅ Redis/fakeredis caching
- ✅ Document preprocessing
- ✅ Few-shot prompts
- ✅ Document hashing
- **Proof**: Cache hit statistics, preprocessing metadata

#### Phase 3 (Advanced)
- ✅ RAG (ChromaDB) for context retrieval
- ✅ Intelligent model routing
- ✅ Request queuing
- ✅ Rate limiting
- ✅ System load tracking
- **Proof**: RAG stats, routing decisions, queue status, load metrics

### 5. Metrics Included

For each test:
- **Processing Time**: Seconds to complete extraction
- **Accuracy**: Number of items correctly extracted
- **Similarity**: Jaccard similarity between OpenAI and Ollama results
- **Cache Performance**: Hit rate, cache size
- **RAG Performance**: Context retrieval stats
- **System Load**: Current system load during processing
- **Cost Comparison**: Estimated API costs (if applicable)

### 6. Conclusion
- Performance summary
- Cost-benefit analysis
- Recommendations for production use

## Running the Report Generator

```bash
cd grc_backend
python generate_performance_report.py
```

## Output Files

The script generates:
1. **`performance_report_output/AI_Performance_Comparison_Report.pdf`** - Main PDF report
2. **`performance_report_output/test_results.json`** - Raw test data
3. **`performance_report_output/*.png`** - Chart images (4 charts)

## Expected Results

Based on Phase 1, 2, 3 optimizations:

### Performance Improvements
- **30-50% faster** processing with Ollama (Phase 1: model selection)
- **50-70% cost reduction** (Phase 2: caching)
- **15-25% accuracy improvement** (Phase 3: RAG context)

### Similarity
- **85-95% similarity** between OpenAI and Ollama results
- Comparable extraction quality
- Better structured output with few-shot prompts

## Verification Steps

1. Check that all 3 documents are processed
2. Verify both OpenAI and Ollama results are generated
3. Confirm charts are created
4. Review PDF report for completeness
5. Validate metrics and percentages

## Troubleshooting

If the script fails:
1. Ensure all documents exist in `grc_backend/` directory
2. Check Django settings are correct
3. Verify OpenAI API key is set (for OpenAI tests)
4. Ensure Ollama is running (for Ollama tests)
5. Install required packages: `pip install reportlab matplotlib`

## Notes

- Tests are run sequentially to avoid rate limiting
- Cache is cleared between provider tests for fair comparison
- Each test includes full Phase 1, 2, 3 optimizations
- Results are stored in JSON for further analysis


