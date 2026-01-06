import requests
import json
import time
import logging
import os
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')
import asyncio
import aiohttp
 
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
# Environment-based configuration
def get_ollama_url():
    """Get Ollama URL based on environment - CONFIGURED TO USE EC2 ONLY"""
    # FORCE EC2 USAGE - Skip local Ollama
    ec2_url = "http://13.205.15.232:11434"
    
    # Check if we want to override with environment variable
    if os.getenv('ENVIRONMENT') == 'LOCAL':
        logger.info("[INFO] ENVIRONMENT=LOCAL set, using localhost Ollama")
        return "http://127.0.0.1:11434"
    
    # Always use EC2 by default
    try:
        # Test EC2 connection
        response = requests.get(f"{ec2_url}/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("[OK] Using EC2 Ollama (forced)")
            return ec2_url
    except Exception as e:
        logger.warning(f"[WARN] EC2 Ollama not available: {e}")
    
    # Fallback to localhost only if EC2 fails
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        if response.status_code == 200:
            logger.info("[OK] EC2 failed, falling back to localhost Ollama")
            return "http://127.0.0.1:11434"
    except:
        pass
    
    # Default to EC2 even if connection test failed
    logger.warning("[WARN] Could not verify Ollama connection, defaulting to EC2")
    return ec2_url
 
class OllamaSimpleIntegration:
    """
    Simple Ollama Integration for AI Enhancement
    Provides basic Ollama API integration for text processing and analysis
    """
   
    def __init__(self, base_url: str = None):
        """Initialize Ollama integration"""
        self.base_url = base_url or get_ollama_url()
        self.available_models = []
        self.is_available = False
        logger.info(f"[INFO] Ollama configured for: {self.base_url}")
        self._check_availability()
       
    def _check_availability(self):
        """Check if Ollama is available and running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.is_available = True
                models_data = response.json()
                self.available_models = [model['name'] for model in models_data.get('models', [])]
                logger.info(f"[OK] Ollama available at {self.base_url} with models: {self.available_models}")
            else:
                logger.warning(f"[WARN] Ollama not responding properly: {response.status_code}")
                self.is_available = False
        except Exception as e:
            logger.warning(f"[WARN] Ollama not available: {e}")
            self.is_available = False
    
    def get_best_model(self, preferred_model: str = "llama3.2:3b") -> str:
        """Get the best available model, fallback to available ones"""
        if not self.is_available:
            return preferred_model
        
        # Check if preferred model is available
        if preferred_model in self.available_models:
            return preferred_model
        
        # Fallback order: llama3.2 -> mistral -> first available (prioritize EC2 models)
        fallback_models = ["llama3.2:3b", "llama3.2", "llama3", "mistral:7b-instruct", "mistral"]
        
        for model in fallback_models:
            if model in self.available_models:
                logger.info(f"[INFO] Using fallback model: {model}")
                return model
        
        # Return first available model if none of the preferred ones are found
        if self.available_models:
            logger.info(f"[INFO] Using first available model: {self.available_models[0]}")
            return self.available_models[0]
        
        # Last resort: return preferred model and let it fail
        return preferred_model
   
    def simple_ollama(self, prompt: str, model: str = "llama3.2:3b", max_tokens: int = 100) -> Optional[str]:
        """
        Simple Ollama API call for text processing - OPTIMIZED FOR SPEED
       
        Args:
            prompt: Input prompt for the model
            model: Model name to use
            max_tokens: Maximum tokens to generate
           
        Returns:
            Generated text or None if failed
        """
        if not self.is_available:
            logger.warning("Ollama not available, skipping request")
            return None
        
        # Use the best available model
        actual_model = self.get_best_model(model)
        if actual_model != model:
            logger.info(f"[INFO] Requested model '{model}' not available, using '{actual_model}'")
           
        # Retry logic with exponential backoff - OPTIMIZED FOR SPEED
        max_retries = 2  # Reduced from 3 to 2 for speed
       
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": actual_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
               
                # OPTIMIZED timeout for vendor extraction and contract processing
                base_timeout = 80  # Increased to 80 seconds for complex contract extraction
                adaptive_timeout = min(150, base_timeout + (len(prompt) // 100))  # Max 150 seconds for complex operations like contract/SLA extraction
               
                logger.info(f"Attempt {attempt + 1}/{max_retries} with {adaptive_timeout}s timeout using {actual_model}")
               
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=adaptive_timeout
                )
               
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '').strip()
                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Reduced wait time from 2^attempt to 1 second
                        continue
                    return None
                   
            except requests.exceptions.Timeout:
                logger.error(f"Ollama API timeout (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Reduced wait time
                    continue
                return None
            except Exception as e:
                logger.error(f"Error calling Ollama (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Reduced wait time
                    continue
                return None
       
        logger.error("All retry attempts failed")
        return None
   
    def enhance_descriptions(self, descriptions: List[str], model: str = "llama3.2:3b") -> List[str]:
        """
        Enhance transaction descriptions using Ollama
       
        Args:
            descriptions: List of transaction descriptions
            model: Model to use for enhancement
           
        Returns:
            List of enhanced descriptions
        """
        if not self.is_available:
            logger.warning("Ollama not available, returning original descriptions")
            return descriptions
           
        enhanced_descriptions = []
       
        for desc in descriptions:
            try:
                # Create enhancement prompt
                prompt = f"""
                Enhance this transaction description to be more descriptive and clear:
                Original: {desc}
               
                Enhanced description:"""
               
                enhanced = self.simple_ollama(prompt, model, max_tokens=50)
                if enhanced:
                    enhanced_descriptions.append(enhanced)
                else:
                    enhanced_descriptions.append(desc)
                   
            except Exception as e:
                logger.error(f"Error enhancing description '{desc}': {e}")
                enhanced_descriptions.append(desc)
       
        return enhanced_descriptions
   
    def categorize_transactions(self, descriptions: List[str], model: str = "llama3.2:3b") -> List[str]:
        """
        Categorize transactions using Ollama
       
        Args:
            descriptions: List of transaction descriptions
            model: Model to use for categorization
           
        Returns:
            List of categories
        """
        if not self.is_available:
            logger.warning("Ollama not available, returning default categories")
            return ["Operating Activities"] * len(descriptions)
           
        categories = []
       
        for desc in descriptions:
            try:
                prompt = f"""
                Categorize this transaction into one of these cash flow categories:
                - Operating Activities (revenue, expenses, regular business operations)
                - Investing Activities (capital expenditure, asset purchases, investments)
                - Financing Activities (loans, interest, dividends, equity)
               
                Transaction: {desc}
                Category:"""
               
                category = self.simple_ollama(prompt, model, max_tokens=20)
                if category:
                    # Clean up the response
                    category = category.strip().split('\n')[0].strip()
                    if category not in ["Operating Activities", "Investing Activities", "Financing Activities"]:
                        category = "Operating Activities"
                else:
                    category = "Operating Activities"
                   
                categories.append(category)
               
            except Exception as e:
                logger.error(f"Error categorizing '{desc}': {e}")
                categories.append("Operating Activities")
       
        return categories
   
    def analyze_patterns(self, data: List[Dict[str, Any]], model: str = "llama3.2:3b") -> Dict[str, Any]:
        """
        Analyze patterns in transaction data using Ollama
       
        Args:
            data: List of transaction dictionaries
            model: Model to use for analysis
           
        Returns:
            Dictionary containing pattern analysis
        """
        if not self.is_available:
            logger.warning("Ollama not available, returning basic analysis")
            return {"patterns": "Basic analysis only", "confidence": 0.5}
           
        try:
            # Prepare data summary for analysis
            total_transactions = len(data)
            total_amount = sum(float(item.get('amount', 0)) for item in data)
            avg_amount = total_amount / total_transactions if total_transactions > 0 else 0
           
            prompt = f"""
            Analyze these transaction patterns:
            - Total transactions: {total_transactions}
            - Total amount: ${total_amount:,.2f}
            - Average amount: ${avg_amount:,.2f}
           
            Provide insights about:
            1. Revenue patterns
            2. Seasonal trends
            3. Risk factors
            4. Recommendations
           
            Analysis:"""
           
            analysis = self.simple_ollama(prompt, model, max_tokens=200)
           
            return {
                "patterns": analysis if analysis else "No patterns detected",
                "confidence": 0.8 if analysis else 0.3,
                "total_transactions": total_transactions,
                "total_amount": total_amount,
                "avg_amount": avg_amount
            }
           
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return {"patterns": "Analysis failed", "confidence": 0.1, "error": str(e)}
   
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of Ollama integration"""
        return {
            "available": self.is_available,
            "base_url": self.base_url,
            "available_models": self.available_models,
            "status": "healthy" if self.is_available else "unavailable"
        }
 
# Global instance for easy access
ollama_integration = OllamaSimpleIntegration()
 
class AsyncOllamaClient:
    """Async Ollama client for concurrent processing"""
   
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session = None
        self.semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
       
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
       
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
   
    async def async_generate(self, prompt: str, model: str = "llama3.2:3b", max_tokens: int = 200) -> Optional[str]:
        """Async version of Ollama generation"""
        async with self.semaphore:  # Limit concurrent requests
            try:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
               
                timeout = aiohttp.ClientTimeout(total=60)  # 1 minute timeout for faster processing
               
                async with self.session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '').strip()
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return None
                       
            except asyncio.TimeoutError:
                logger.error("Ollama API timeout")
                return None
            except Exception as e:
                logger.error(f"Error calling Ollama: {e}")
                return None
 
def simple_ollama(prompt: str, model: str = "llama3.2:3b", max_tokens: int = 100) -> Optional[str]:
    """
    Simple function to call Ollama
   
    Args:
        prompt: Input prompt
        model: Model name
        max_tokens: Maximum tokens to generate
       
    Returns:
        Generated text or None
    """
    return ollama_integration.simple_ollama(prompt, model, max_tokens)
 
def enhance_descriptions_with_ollama(descriptions: List[str]) -> List[str]:
    """
    Enhance descriptions using Ollama
   
    Args:
        descriptions: List of descriptions to enhance
       
    Returns:
        List of enhanced descriptions
    """
    return ollama_integration.enhance_descriptions(descriptions)
 
def categorize_with_ollama(descriptions: List[str]) -> List[str]:
    """
    Categorize transactions using Ollama
   
    Args:
        descriptions: List of descriptions to categorize
       
    Returns:
        List of categories
    """
    return ollama_integration.categorize_transactions(descriptions)
 
def analyze_patterns_with_ollama(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze patterns using Ollama
   
    Args:
        data: Transaction data to analyze
       
    Returns:
        Pattern analysis results
    """
    return ollama_integration.analyze_patterns(data)
 
def check_ollama_availability():
    """Check if Ollama is available and working"""
    try:
        import requests
        # Use the same auto-detection logic as the main class
        ollama_url = get_ollama_url()
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception:
        return False
 
# Test function
def test_ollama_integration():
    """Test the Ollama integration"""
    print("Testing Ollama integration...")
   
    # Test availability
    status = ollama_integration.get_health_status()
    print(f"Ollama status: {status}")
   
    # Test simple call
    if ollama_integration.is_available:
        result = simple_ollama("Hello, how are you?", max_tokens=20)
        print(f"Test response: {result}")
    else:
        print("Ollama not available for testing")
 
if __name__ == "__main__":
    test_ollama_integration()