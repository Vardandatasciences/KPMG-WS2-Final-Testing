import requests
import os

# Test S3 microservice directly
BASE_URL = "http://15.207.1.40:3000"
API_KEY = "my-very-strong-secret"

print(f"Testing S3 microservice at {BASE_URL}")
print(f"Using API key: {API_KEY}")

# Test 1: Check root endpoint without key (should be unauthorized)
print("\n=== Test 1: Root endpoint without API key ===")
response = requests.get(f"{BASE_URL}/")
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Test 2: Check root endpoint with key
print("\n=== Test 2: Root endpoint with API key ===")
headers = {"x-api-key": API_KEY}
response = requests.get(f"{BASE_URL}/", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Test 3: Try upload endpoint structure
print("\n=== Test 3: Upload endpoint with API key (GET - just to test auth) ===")
headers = {"x-api-key": API_KEY}
response = requests.get(f"{BASE_URL}/api/upload/test-user/test.txt", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
