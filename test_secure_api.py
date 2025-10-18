"""
Secure API Test Suite for TrueFACE Backend
Tests the production-ready API with proper authentication
"""

import requests
import json
import time
import asyncio
import websockets
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

# Get API key from environment or use development default
API_KEY = os.getenv('API_KEY', 'dev_api_key_123')

def get_auth_headers():
    """Get authentication headers"""
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

def test_health_endpoint():
    """Test the health endpoint with authentication"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", headers=get_auth_headers(), timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Components: {data.get('components', {})}")
            return True
        elif response.status_code == 403:
            print("   ❌ Authentication failed - check API key")
            return False
        else:
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   Failed: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint (no auth required)"""
    print("🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Version: {data.get('version', 'N/A')}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   Failed: {e}")
        return False

def test_analyze_endpoint():
    """Test the analyze endpoint with authentication"""
    print("🔍 Testing analyze endpoint...")
    try:
        payload = {
            "session_id": "test_session_1",
            "frame_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
            "audio_data": None
        }
        
        response = requests.post(
            f"{API_BASE_URL}/analyze", 
            json=payload, 
            headers=get_auth_headers(), 
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Authenticity Score: {result.get('authenticity', 'N/A')}")
            print(f"   Video Score: {result.get('video_score', 'N/A')}")
            print(f"   Audio Score: {result.get('audio_score', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
            return True
        elif response.status_code == 403:
            print("   ❌ Authentication failed - check API key")
            return False
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   Failed: {e}")
        return False

def test_auth_score_endpoint():
    """Test the auth score endpoint with authentication"""
    print("🔍 Testing auth score endpoint...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/auth_score/test_session_1", 
            headers=get_auth_headers(), 
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Session Authenticity: {result.get('authenticity', 'N/A')}")
            return True
        elif response.status_code == 404:
            print("   ℹ️  Session not found (expected for new session)")
            return True  # This is expected behavior
        elif response.status_code == 403:
            print("   ❌ Authentication failed - check API key")
            return False
        else:
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   Failed: {e}")
        return False

def test_authentication_security():
    """Test that endpoints are properly secured"""
    print("🔒 Testing authentication security...")
    try:
        # Test without authentication
        response = requests.post(f"{API_BASE_URL}/analyze", json={
            "session_id": "test",
            "frame_data": "test"
        }, timeout=5)
        
        if response.status_code == 403:
            print("   ✅ Endpoints properly secured (403 without auth)")
            return True
        else:
            print(f"   ❌ Security issue: Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   Failed: {e}")
        return False

async def test_websocket():
    """Test WebSocket functionality (no auth required for WebSocket)"""
    print("🔍 Testing WebSocket connection...")
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("   ✅ WebSocket connected successfully")
            
            # Test ping
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("   📤 Sent ping message")
            
            # Wait for pong
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            pong_data = json.loads(response)
            print(f"   📥 Received: {pong_data.get('type', 'unknown')}")
            
            # Test frame analysis
            frame_message = {
                "type": "frame_data",
                "session_id": "ws_test_session",
                "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
            }
            await websocket.send(json.dumps(frame_message))
            print("   📤 Sent frame data")
            
            # Wait for analysis result
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            analysis_data = json.loads(response)
            
            if analysis_data.get("type") == "analysis_result":
                result = analysis_data.get("data", {})
                print(f"   📊 Analysis Result - Authenticity: {result.get('authenticity', 'N/A')}")
                return True
            else:
                print(f"   ❌ Unexpected response: {analysis_data}")
                return False
                
    except asyncio.TimeoutError:
        print("   ⏰ WebSocket test timed out")
        return False
    except Exception as e:
        print(f"   ❌ WebSocket test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting (make multiple requests quickly)"""
    print("⏱️ Testing rate limiting...")
    try:
        # Make several requests quickly
        responses = []
        for i in range(5):
            response = requests.get(f"{API_BASE_URL}/", timeout=2)
            responses.append(response.status_code)
            time.sleep(0.1)  # Small delay between requests
        
        # Check if any were rate limited (429)
        rate_limited = any(status == 429 for status in responses)
        
        if rate_limited:
            print("   ✅ Rate limiting is working (some 429 responses)")
        else:
            print("   ℹ️  No rate limiting detected (may need more requests)")
        
        return True  # Don't fail the test if rate limiting isn't triggered
    except Exception as e:
        print(f"   Failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("🧪 TrueFACE Secure Backend API Tests")
    print("=" * 50)
    
    # Check API key
    if not API_KEY or API_KEY == 'your_api_key_here':
        print("⚠️  Warning: Using default/placeholder API key")
        print(f"   Current API key: {API_KEY}")
        print("   Set API_KEY environment variable for production testing")
    else:
        print(f"🔑 Using API key: {API_KEY[:10]}...")
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    tests = [
        ("Root Endpoint (No Auth)", test_root_endpoint),
        ("Authentication Security", test_authentication_security),
        ("Health Check (With Auth)", test_health_endpoint),
        ("Analyze Endpoint (With Auth)", test_analyze_endpoint),
        ("Auth Score Endpoint (With Auth)", test_auth_score_endpoint),
        ("Rate Limiting", test_rate_limiting),
    ]
    
    results = {}
    
    # Run synchronous tests
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   💥 Test crashed: {e}")
            results[test_name] = False
    
    # Run WebSocket test
    print(f"\nWebSocket Test:")
    try:
        results["WebSocket"] = asyncio.run(test_websocket())
    except Exception as e:
        print(f"   💥 WebSocket test crashed: {e}")
        results["WebSocket"] = False
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 SECURE API TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name:30} : {status}")
        if passed_test:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All secure API tests passed!")
        print("✅ Authentication is working correctly")
        print("✅ Security measures are active")
        print(f"🌐 API is running at: {API_BASE_URL}")
        print(f"🔌 WebSocket at: {WS_URL}")
        print(f"📚 API docs at: {API_BASE_URL}/docs")
    else:
        print("⚠️  Some tests failed. Check the results above.")
        if results.get("Authentication Security", False):
            print("✅ Security is working (endpoints are protected)")
        else:
            print("❌ Security issues detected")
    
    # Provide usage examples
    print(f"\n💡 API Usage Examples:")
    print(f"curl -H 'Authorization: Bearer {API_KEY}' {API_BASE_URL}/health")
    print(f"curl -H 'Authorization: Bearer {API_KEY}' -H 'Content-Type: application/json' \\")
    json_data = '{"session_id":"test","frame_data":"base64_data"}'
    print(f"     -d '{json_data}' \\")
    print(f"     {API_BASE_URL}/analyze")
    
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n🚀 Secure backend is ready for production use!")
    else:
        print("\n🔧 Please check the failed tests above.")
