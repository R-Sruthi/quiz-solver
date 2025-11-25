import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
ENDPOINT_URL = os.getenv("ENDPOINT_URL", "http://localhost:8000/solve")
EMAIL = os.getenv("STUDENT_EMAIL")
SECRET = os.getenv("STUDENT_SECRET")

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(ENDPOINT_URL.replace("/solve", "/health"))
        print("✅ Health Check:", response.json())
        return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_invalid_secret():
    """Test with invalid secret (should return 403)"""
    payload = {
        "email": EMAIL,
        "secret": "wrong-secret",
        "url": "https://tds-llm-analysis.s-anand.net/demo"
    }
    
    try:
        response = requests.post(ENDPOINT_URL, json=payload)
        if response.status_code == 403:
            print("✅ Invalid Secret Test: Correctly rejected (403)")
            return True
        else:
            print(f"❌ Invalid Secret Test: Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Invalid Secret Test Failed: {e}")
        return False

def test_demo_quiz():
    """Test with demo quiz"""
    payload = {
        "email": EMAIL,
        "secret": SECRET,
        "url": "https://tds-llm-analysis.s-anand.net/demo"
    }
    
    print("\n🚀 Testing Demo Quiz...")
    print(f"Endpoint: {ENDPOINT_URL}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(ENDPOINT_URL, json=payload, timeout=180)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Demo Quiz Test Passed!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Demo Quiz Test Failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.Timeout:
        print("❌ Demo Quiz Test Failed: Timeout (>180s)")
        return False
    except Exception as e:
        print(f"❌ Demo Quiz Test Failed: {e}")
        return False

def test_invalid_json():
    """Test with invalid JSON (should return 400)"""
    try:
        response = requests.post(
            ENDPOINT_URL,
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 400:
            print("✅ Invalid JSON Test: Correctly rejected (400)")
            return True
        else:
            print(f"❌ Invalid JSON Test: Expected 400, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Invalid JSON Test Failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("QUIZ SOLVER ENDPOINT TESTS")
    print("=" * 60)
    
    if not EMAIL or not SECRET:
        print("❌ Please set STUDENT_EMAIL and STUDENT_SECRET in .env file")
        exit(1)
    
    results = []
    
    print("\n1. Testing Health Endpoint...")
    results.append(test_health())
    
    print("\n2. Testing Invalid Secret...")
    results.append(test_invalid_secret())
    
    print("\n3. Testing Invalid JSON...")
    results.append(test_invalid_json())
    
    print("\n4. Testing Demo Quiz...")
    results.append(test_demo_quiz())
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✅ All tests passed! Your endpoint is ready.")
    else:
        print("❌ Some tests failed. Please check the logs above.")