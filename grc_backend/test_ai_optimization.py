"""
AI Model Optimization Test Script - Phase 1
============================================

This script tests Phase 1 optimizations step by step:
1. Baseline Test (Current Setup)
2. Quantized Models Test
3. Dynamic Context Window Test
4. Streaming Response Test
5. Performance Comparison

Run each step individually and confirm results before proceeding.
"""

import requests
import json
import time
import os
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# Ollama Configuration (from your settings)
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://13.205.15.232:11434').rstrip('/')
OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', '600'))

# Current model (non-quantized)
CURRENT_MODEL = 'llama3.2:3b'

# Quantized models to test (updated to match your available models)
QUANTIZED_MODELS = {
    'llama3.2:1b-instruct-q4_K_M': {
        'name': 'Llama 3.2 1B Instruct (q4_K_M)',
        'description': 'Ultra-fast, smallest model with instruction tuning',
        'use_case': 'Simple queries, basic extraction'
    },
    'llama3.2:3b-instruct-q4_K_M': {
        'name': 'Llama 3.2 3B Instruct (q4_K_M)',
        'description': 'Best balance of speed and quality with instruction tuning',
        'use_case': 'General document processing (RECOMMENDED)'
    },
    'llama3:8b-instruct-q4_K_M': {
        'name': 'Llama 3 8B Instruct (q4_K_M)',
        'description': 'Larger model for complex reasoning tasks',
        'use_case': 'Complex reasoning tasks'
    }
}

# Test prompts (simulating real use cases)
TEST_PROMPTS = {
    'simple': {
        'prompt': 'What is the compliance status of this document? Answer in one sentence.',
        'expected_context': 2048,
        'description': 'Simple query - should use 1B model'
    },
    'medium': {
        'prompt': '''Analyze this audit document and identify compliance issues:

Document: Annual Security Audit Report 2024
- Last audit date: 2023-06-15
- Findings: 3 high-risk issues, 5 medium-risk issues
- Remediation status: 2 high-risk issues pending
- Next audit due: 2024-12-31

Provide a summary of compliance status and key recommendations.''',
        'expected_context': 4096,
        'description': 'Medium document - should use 3B model'
    },
    'complex': {
        'prompt': '''Perform comprehensive risk analysis on this vendor assessment:

Vendor: Cloud Services Provider Inc.
Contract Duration: 3 years
Service Type: Infrastructure as a Service
Data Classification: PII, Financial Data
Compliance Requirements: SOC 2, ISO 27001, GDPR
Security Controls: Multi-factor authentication, encryption at rest
Incident History: 1 minor incident in past year
Third-party Dependencies: 2 sub-processors

Analyze:
1. Risk level assessment
2. Compliance gaps
3. Security posture
4. Recommendations for risk mitigation
5. Contract terms review

Provide detailed analysis with specific risk scores and mitigation strategies.''',
        'expected_context': 8192,
        'description': 'Complex analysis - should use 8B model'
    }
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_header(title: str, step: int = None):
    """Print formatted header"""
    print("\n" + "="*80)
    if step:
        print(f"STEP {step}: {title}")
    else:
        print(title)
    print("="*80 + "\n")

def print_result(title: str, data: Dict):
    """Print formatted result"""
    print(f"\n📊 {title}")
    print("-" * 60)
    for key, value in data.items():
        print(f"  {key}: {value}")
    print()

def wait_for_confirmation(message: str = "Press Enter to continue to next step..."):
    """Wait for user confirmation"""
    input(f"\n⏸️  {message}")

def calculate_word_count(text: str) -> int:
    """Calculate word count in text"""
    return len(text.split())

def estimate_tokens(text: str) -> int:
    """Estimate token count (rough: 1 token ≈ 0.75 words)"""
    return int(len(text.split()) * 1.33)

def determine_context_size(text: str) -> int:
    """Determine appropriate context size based on text length"""
    word_count = calculate_word_count(text)
    tokens = estimate_tokens(text)
    
    if tokens < 1500:  # Small document
        return 2048
    elif tokens < 3500:  # Medium document
        return 4096
    else:  # Large document
        return 8192

# ============================================================================
# OLLAMA API FUNCTIONS
# ============================================================================

def check_ollama_connection() -> bool:
    """Check if Ollama is accessible"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            print(f"✅ Ollama connection successful!")
            print(f"   Available models: {', '.join(model_names)}")
            return True, model_names
        else:
            print(f"❌ Ollama returned status code: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {str(e)}")
        print(f"   URL: {OLLAMA_BASE_URL}")
        return False, []

def check_model_available(model_name: str, available_models: List[str]) -> bool:
    """Check if a model is available"""
    # Check exact match or partial match
    for available in available_models:
        if model_name in available or available in model_name:
            return True
    return False

def call_ollama_api(
    prompt: str,
    model: str,
    context_size: int = 4096,
    temperature: float = 0.1,
    stream: bool = False,
    timeout: int = 600
) -> Tuple[Optional[str], float, Dict]:
    """
    Call Ollama API and return response, time taken, and metadata
    
    Returns:
        (response_text, time_taken, metadata)
    """
    start_time = time.time()
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "temperature": temperature,
            "num_ctx": context_size,  # Context window size
            "num_predict": 2000,  # Max tokens to generate
        }
    }
    
    try:
        if stream:
            # Handle streaming response
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                stream=True,
                timeout=timeout
            )
            
            if response.status_code != 200:
                return None, 0, {'error': f'Status code: {response.status_code}'}
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if 'response' in chunk:
                            full_response += chunk['response']
                    except json.JSONDecodeError:
                        continue
            
            elapsed_time = time.time() - start_time
            return full_response, elapsed_time, {'streaming': True}
        else:
            # Handle non-streaming response
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=timeout
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                return None, elapsed_time, {'error': error_data}
            
            result = response.json()
            response_text = result.get('response', '')
            
            metadata = {
                'total_duration': result.get('total_duration', 0),
                'load_duration': result.get('load_duration', 0),
                'prompt_eval_count': result.get('prompt_eval_count', 0),
                'eval_count': result.get('eval_count', 0),
            }
            
            return response_text, elapsed_time, metadata
            
    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        return None, elapsed_time, {'error': 'Request timeout'}
    except Exception as e:
        elapsed_time = time.time() - start_time
        return None, elapsed_time, {'error': str(e)}

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_step_1_baseline():
    """STEP 1: Test current baseline setup"""
    print_header("BASELINE TEST - Current Setup", 1)
    
    print("Testing current model and configuration...")
    print(f"Model: {CURRENT_MODEL}")
    print(f"Ollama URL: {OLLAMA_BASE_URL}\n")
    
    # Check connection
    connected, available_models = check_ollama_connection()
    if not connected:
        print("❌ Cannot proceed - Ollama connection failed")
        return None
    
    # Check if current model is available
    if not check_model_available(CURRENT_MODEL, available_models):
        print(f"⚠️  Warning: Model '{CURRENT_MODEL}' not found in available models")
        print("   Available models:", ', '.join(available_models))
    
    # Test with medium prompt
    test_prompt = TEST_PROMPTS['medium']['prompt']
    print(f"\n🧪 Testing with medium complexity prompt...")
    print(f"   Prompt length: {len(test_prompt)} characters")
    print(f"   Word count: {calculate_word_count(test_prompt)} words")
    print(f"   Estimated tokens: {estimate_tokens(test_prompt)} tokens")
    
    print("\n⏳ Calling Ollama API (this may take 30-60 seconds)...")
    
    response, elapsed_time, metadata = call_ollama_api(
        prompt=test_prompt,
        model=CURRENT_MODEL,
        context_size=4096,  # Default context
        temperature=0.1,
        stream=False
    )
    
    if response:
        print(f"\n✅ Baseline test completed!")
        print(f"   Response time: {elapsed_time:.2f} seconds")
        print(f"   Response length: {len(response)} characters")
        print(f"   Response preview: {response[:200]}...")
        
        if 'total_duration' in metadata:
            print(f"   Model processing time: {metadata.get('total_duration', 0) / 1e9:.2f} seconds")
        
        baseline_result = {
            'model': CURRENT_MODEL,
            'response_time': elapsed_time,
            'response_length': len(response),
            'response_preview': response[:200],
            'metadata': metadata
        }
        
        return baseline_result
    else:
        print(f"\n❌ Baseline test failed!")
        print(f"   Error: {metadata.get('error', 'Unknown error')}")
        return None

def test_step_2_quantized_models():
    """STEP 2: Test quantized models"""
    print_header("QUANTIZED MODELS TEST", 2)
    
    # Check connection
    connected, available_models = check_ollama_connection()
    if not connected:
        print("❌ Cannot proceed - Ollama connection failed")
        return None
    
    print("Testing quantized models for speed and quality comparison...\n")
    
    results = {}
    test_prompt = TEST_PROMPTS['medium']['prompt']
    
    for model_name, model_info in QUANTIZED_MODELS.items():
        print(f"\n🧪 Testing: {model_info['name']}")
        print(f"   Description: {model_info['description']}")
        print(f"   Use case: {model_info['use_case']}")
        
        # Check if model is available
        if not check_model_available(model_name, available_models):
            print(f"   ⚠️  Model not available - you may need to download it:")
            print(f"      Run: ollama pull {model_name}")
            results[model_name] = {'status': 'not_available'}
            continue
        
        print("   ⏳ Calling API...")
        
        response, elapsed_time, metadata = call_ollama_api(
            prompt=test_prompt,
            model=model_name,
            context_size=4096,
            temperature=0.1,
            stream=False
        )
        
        if response:
            print(f"   ✅ Completed in {elapsed_time:.2f} seconds")
            print(f"   Response length: {len(response)} characters")
            
            results[model_name] = {
                'status': 'success',
                'response_time': elapsed_time,
                'response_length': len(response),
                'response_preview': response[:200],
                'metadata': metadata
            }
        else:
            print(f"   ❌ Failed: {metadata.get('error', 'Unknown error')}")
            results[model_name] = {'status': 'failed', 'error': metadata.get('error')}
    
    # Print comparison
    print("\n" + "="*80)
    print("📊 QUANTIZED MODELS COMPARISON")
    print("="*80)
    print(f"{'Model':<30} {'Status':<15} {'Time (s)':<12} {'Response Length':<15}")
    print("-"*80)
    
    for model_name, result in results.items():
        if result.get('status') == 'success':
            print(f"{model_name:<30} {'✅ Success':<15} {result['response_time']:<12.2f} {result['response_length']:<15}")
        elif result.get('status') == 'not_available':
            print(f"{model_name:<30} {'⚠️  Not Available':<15} {'-':<12} {'-':<15}")
        else:
            print(f"{model_name:<30} {'❌ Failed':<15} {'-':<12} {'-':<15}")
    
    return results

def test_step_3_dynamic_context():
    """STEP 3: Test dynamic context window sizing"""
    print_header("DYNAMIC CONTEXT WINDOW TEST", 3)
    
    print("Testing dynamic context sizing based on document size...\n")
    
    # Check connection
    connected, available_models = check_ollama_connection()
    if not connected:
        print("❌ Cannot proceed - Ollama connection failed")
        return None
    
    # Use recommended quantized model
    test_model = 'llama3.2:3b-instruct-q4_K_M'
    if not check_model_available(test_model, available_models):
        test_model = CURRENT_MODEL  # Fallback to current model
    
    results = {}
    
    for test_type, test_data in TEST_PROMPTS.items():
        print(f"\n🧪 Testing: {test_data['description']}")
        prompt = test_data['prompt']
        
        # Calculate appropriate context size
        calculated_context = determine_context_size(prompt)
        expected_context = test_data['expected_context']
        
        print(f"   Prompt tokens: ~{estimate_tokens(prompt)}")
        print(f"   Calculated context: {calculated_context}")
        print(f"   Expected context: {expected_context}")
        
        # Test with calculated context
        print("   ⏳ Calling API with dynamic context...")
        
        response, elapsed_time, metadata = call_ollama_api(
            prompt=prompt,
            model=test_model,
            context_size=calculated_context,
            temperature=0.1,
            stream=False
        )
        
        if response:
            print(f"   ✅ Completed in {elapsed_time:.2f} seconds")
            
            results[test_type] = {
                'context_size': calculated_context,
                'response_time': elapsed_time,
                'response_length': len(response),
                'tokens_estimated': estimate_tokens(prompt)
            }
        else:
            print(f"   ❌ Failed: {metadata.get('error', 'Unknown error')}")
            results[test_type] = {'status': 'failed'}
    
    # Print summary
    print("\n" + "="*80)
    print("📊 DYNAMIC CONTEXT WINDOW RESULTS")
    print("="*80)
    print(f"{'Test Type':<15} {'Context Size':<15} {'Time (s)':<12} {'Tokens':<10}")
    print("-"*80)
    
    for test_type, result in results.items():
        if 'response_time' in result:
            print(f"{test_type:<15} {result['context_size']:<15} {result['response_time']:<12.2f} {result['tokens_estimated']:<10}")
        else:
            print(f"{test_type:<15} {'Failed':<15} {'-':<12} {'-':<10}")
    
    return results

def test_step_4_streaming():
    """STEP 4: Test streaming responses"""
    print_header("STREAMING RESPONSE TEST", 4)
    
    print("Testing streaming vs non-streaming responses...\n")
    
    # Check connection
    connected, available_models = check_ollama_connection()
    if not connected:
        print("❌ Cannot proceed - Ollama connection failed")
        return None
    
    # Use recommended quantized model
    test_model = 'llama3.2:3b-instruct-q4_K_M'
    if not check_model_available(test_model, available_models):
        test_model = CURRENT_MODEL  # Fallback to current model
    
    test_prompt = TEST_PROMPTS['medium']['prompt']
    context_size = determine_context_size(test_prompt)
    
    results = {}
    
    # Test non-streaming
    print("🧪 Testing NON-STREAMING response...")
    print("   ⏳ Calling API...")
    
    response_non_stream, time_non_stream, metadata_non_stream = call_ollama_api(
        prompt=test_prompt,
        model=test_model,
        context_size=context_size,
        temperature=0.1,
        stream=False
    )
    
    if response_non_stream:
        print(f"   ✅ Completed in {time_non_stream:.2f} seconds")
        results['non_streaming'] = {
            'response_time': time_non_stream,
            'response_length': len(response_non_stream),
            'first_token_time': time_non_stream  # In non-streaming, first token = last token
        }
    else:
        print(f"   ❌ Failed: {metadata_non_stream.get('error', 'Unknown error')}")
        results['non_streaming'] = {'status': 'failed'}
    
    # Test streaming
    print("\n🧪 Testing STREAMING response...")
    print("   ⏳ Calling API (you'll see tokens appear as they're generated)...")
    
    start_time = time.time()
    first_token_time = None
    
    response_stream, time_stream, metadata_stream = call_ollama_api(
        prompt=test_prompt,
        model=test_model,
        context_size=context_size,
        temperature=0.1,
        stream=True
    )
    
    if response_stream:
        print(f"   ✅ Completed in {time_stream:.2f} seconds")
        print(f"   Response length: {len(response_stream)} characters")
        results['streaming'] = {
            'response_time': time_stream,
            'response_length': len(response_stream),
            'first_token_time': None  # Would need to track this in streaming
        }
    else:
        print(f"   ❌ Failed: {metadata_stream.get('error', 'Unknown error')}")
        results['streaming'] = {'status': 'failed'}
    
    # Print comparison
    print("\n" + "="*80)
    print("📊 STREAMING vs NON-STREAMING COMPARISON")
    print("="*80)
    
    if 'response_time' in results.get('non_streaming', {}) and 'response_time' in results.get('streaming', {}):
        non_stream_time = results['non_streaming']['response_time']
        stream_time = results['streaming']['response_time']
        
        print(f"Non-streaming time: {non_stream_time:.2f} seconds")
        print(f"Streaming time: {stream_time:.2f} seconds")
        print(f"Difference: {abs(non_stream_time - stream_time):.2f} seconds")
        print(f"\n💡 Note: Streaming provides better UX (perceived 3x faster)")
        print(f"   Actual processing time is similar, but users see results immediately")
    
    return results

def test_step_5_performance_comparison():
    """STEP 5: Comprehensive performance comparison"""
    print_header("PERFORMANCE COMPARISON - All Optimizations", 5)
    
    print("Running comprehensive comparison of all optimizations...\n")
    
    # Check connection
    connected, available_models = check_ollama_connection()
    if not connected:
        print("❌ Cannot proceed - Ollama connection failed")
        return None
    
    test_prompt = TEST_PROMPTS['medium']['prompt']
    context_size = determine_context_size(test_prompt)
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Baseline (Current)',
            'model': CURRENT_MODEL,
            'context': 4096,  # Fixed large context
            'stream': False
        },
        {
            'name': 'Optimized (3B Quantized + Dynamic Context)',
            'model': 'llama3.2:3b-instruct-q4_K_M',
            'context': context_size,  # Dynamic context
            'stream': False
        },
        {
            'name': 'Optimized + Streaming',
            'model': 'llama3.2:3b-instruct-q4_K_M',
            'context': context_size,  # Dynamic context
            'stream': True
        }
    ]
    
    results = {}
    
    for scenario in scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        print(f"   Model: {scenario['model']}")
        print(f"   Context: {scenario['context']}")
        print(f"   Streaming: {scenario['stream']}")
        
        # Check if model is available
        if not check_model_available(scenario['model'], available_models):
            print(f"   ⚠️  Model not available, skipping...")
            results[scenario['name']] = {'status': 'model_not_available'}
            continue
        
        print("   ⏳ Running test...")
        
        response, elapsed_time, metadata = call_ollama_api(
            prompt=test_prompt,
            model=scenario['model'],
            context_size=scenario['context'],
            temperature=0.1,
            stream=scenario['stream']
        )
        
        if response:
            print(f"   ✅ Completed in {elapsed_time:.2f} seconds")
            results[scenario['name']] = {
                'response_time': elapsed_time,
                'response_length': len(response),
                'model': scenario['model'],
                'context': scenario['context'],
                'streaming': scenario['stream']
            }
        else:
            print(f"   ❌ Failed: {metadata.get('error', 'Unknown error')}")
            results[scenario['name']] = {'status': 'failed'}
    
    # Print comprehensive comparison
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE PERFORMANCE COMPARISON")
    print("="*80)
    print(f"{'Scenario':<40} {'Time (s)':<12} {'Improvement':<15}")
    print("-"*80)
    
    baseline_time = None
    for scenario_name, result in results.items():
        if 'response_time' in result:
            time_taken = result['response_time']
            if baseline_time is None:
                baseline_time = time_taken
                improvement = "Baseline"
            else:
                improvement_pct = ((baseline_time - time_taken) / baseline_time) * 100
                improvement = f"{improvement_pct:+.1f}%"
            
            print(f"{scenario_name:<40} {time_taken:<12.2f} {improvement:<15}")
    
    if baseline_time:
        print(f"\n💡 Expected Phase 1 improvement: 40-60% faster")
        print(f"   Your baseline: {baseline_time:.2f} seconds")
        print(f"   Target time: {baseline_time * 0.5:.2f} - {baseline_time * 0.6:.2f} seconds")
    
    return results

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function - runs tests step by step"""
    
    print("="*80)
    print("AI MODEL OPTIMIZATION TEST - PHASE 1")
    print("="*80)
    print("\nThis script will test Phase 1 optimizations step by step.")
    print("After each step, review the results and confirm before proceeding.\n")
    
    # Check Ollama connection first
    print("🔍 Checking Ollama connection...")
    connected, available_models = check_ollama_connection()
    if not connected:
        print("\n❌ Cannot proceed - Ollama is not accessible")
        print(f"   Please verify Ollama is running at: {OLLAMA_BASE_URL}")
        return
    
    print(f"\n✅ Ready to proceed with {len(available_models)} available models")
    
    # Store all results
    all_results = {}
    
    # STEP 1: Baseline
    print("\n" + "="*80)
    print("Starting STEP 1: Baseline Test")
    print("="*80)
    baseline_result = test_step_1_baseline()
    all_results['baseline'] = baseline_result
    
    if baseline_result:
        wait_for_confirmation("Review baseline results above, then continue to Step 2...")
    else:
        print("\n⚠️  Baseline test failed. Continuing anyway...")
        wait_for_confirmation()
    
    # STEP 2: Quantized Models
    print("\n" + "="*80)
    print("Starting STEP 2: Quantized Models Test")
    print("="*80)
    quantized_results = test_step_2_quantized_models()
    all_results['quantized'] = quantized_results
    
    wait_for_confirmation("Review quantized models results, then continue to Step 3...")
    
    # STEP 3: Dynamic Context
    print("\n" + "="*80)
    print("Starting STEP 3: Dynamic Context Window Test")
    print("="*80)
    context_results = test_step_3_dynamic_context()
    all_results['dynamic_context'] = context_results
    
    wait_for_confirmation("Review dynamic context results, then continue to Step 4...")
    
    # STEP 4: Streaming
    print("\n" + "="*80)
    print("Starting STEP 4: Streaming Response Test")
    print("="*80)
    streaming_results = test_step_4_streaming()
    all_results['streaming'] = streaming_results
    
    wait_for_confirmation("Review streaming results, then continue to Step 5...")
    
    # STEP 5: Performance Comparison
    print("\n" + "="*80)
    print("Starting STEP 5: Performance Comparison")
    print("="*80)
    comparison_results = test_step_5_performance_comparison()
    all_results['comparison'] = comparison_results
    
    # Final Summary
    print("\n" + "="*80)
    print("📋 FINAL SUMMARY - Phase 1 Test Results")
    print("="*80)
    print("\nAll test results have been collected.")
    print("\nNext steps:")
    print("1. Review all results above")
    print("2. Identify which optimizations provided the best improvements")
    print("3. Confirm which models are available and working")
    print("4. Proceed with implementation in codebase")
    print("\n" + "="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

