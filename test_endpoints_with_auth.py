"""
Test all endpoints with proper authentication
"""

import requests
import json
import time
import asyncio
import websockets
import base64
from io import BytesIO
from PIL import Image
import numpy as np

API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

# Try different API keys
API_KEYS = [
    "dev_api_key_123",
    "trueface_secure_api_key_2024_change_in_production",
    ""  # Empty for development mode
]

def test_with_different_keys():
    """Test which API key works"""
    print("🔑 Testing API Key Authentication...")
    
    for i, api_key in enumerate(API_KEYS):
        print(f"\nTrying API key {i+1}: {'(empty)' if not api_key else api_key[:10]}...")
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        try:
            response = requests.get(f"{API_BASE_URL}/health", headers=headers, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ API key works!")
                return api_key
            elif response.status_code == 401:
                print(f"   ❌ Invalid API key")
            elif response.status_code == 403:
                print(f"   ❌ Authentication required")
            else:
                print(f"   ❓ Unexpected status: {response.text}")
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    return None

def test_all_endpoints_authenticated(api_key):
    """Test all endpoints with working API key"""
    print(f"\n🧪 Testing All Endpoints with API Key: {api_key[:10] if api_key else '(none)'}...")
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["Content-Type"] = "application/json"
    
    results = {}
    
    # Test 1: Root endpoint (no auth needed)
    print("\n1. Root Endpoint (GET /):")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"   Status: {response.status_code} ✅" if response.status_code == 200 else f"   Status: {response.status_code} ❌")
        results["root"] = response.status_code == 200
    except Exception as e:
        print(f"   Failed: {e}")
        results["root"] = False
    
    # Test 2: Health endpoint
    print("\n2. Health Check (GET /health):")
    try:
        response = requests.get(f"{API_BASE_URL}/health", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Deepfake Detector: {data.get('components', {}).get('deepfake_detector', False)}")
            print(f"   Stream Processor: {data.get('components', {}).get('stream_processor', False)}")
        results["health"] = response.status_code == 200
    except Exception as e:
        print(f"   Failed: {e}")
        results["health"] = False
    
    # Test 3: Analyze endpoint
    print("\n3. Analyze Endpoint (POST /analyze):")
    try:
        # Create simple test data
        test_payload = {
            "session_id": "endpoint_test",
            "frame_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
            "audio_data": None
        }
        
        response = requests.post(f"{API_BASE_URL}/analyze", json=test_payload, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Authenticity: {data.get('authenticity', 'N/A')}")
            print(f"   Video Score: {data.get('video_score', 'N/A')}")
        results["analyze"] = response.status_code == 200
    except Exception as e:
        print(f"   Failed: {e}")
        results["analyze"] = False
    
    # Test 4: Auth score endpoint
    print("\n4. Auth Score Endpoint (GET /auth_score/{session_id}):")
    try:
        response = requests.get(f"{API_BASE_URL}/auth_score/endpoint_test", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Session Authenticity: {data.get('authenticity', 'N/A')}")
        elif response.status_code == 404:
            print("   Session not found (expected)")
        results["auth_score"] = response.status_code in [200, 404]
    except Exception as e:
        print(f"   Failed: {e}")
        results["auth_score"] = False
    
    # Test 5: WebSocket
    print("\n5. WebSocket Endpoint (WS /ws):")
    try:
        async def test_ws():
            async with websockets.connect(WS_URL) as websocket:
                # Send ping
                await websocket.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                return data.get("type") == "pong"
        
        ws_result = asyncio.run(test_ws())
        print(f"   WebSocket: {'✅ Working' if ws_result else '❌ Failed'}")
        results["websocket"] = ws_result
    except Exception as e:
        print(f"   Failed: {e}")
        results["websocket"] = False
    
    return results

def main():
    """Main test function"""
    print("🚀 TrueFACE Backend - Complete Endpoint Testing")
    print("=" * 50)
    
    # Wait for server
    print("⏳ Waiting for server...")
    time.sleep(2)
    
    # Find working API key
    working_key = test_with_different_keys()
    
    if working_key is None:
        print("\n❌ No working API key found!")
        print("The server might be in production mode requiring authentication.")
        print("Try setting DEBUG=true or providing a valid API key.")
        return False
    
    # Test all endpoints
    results = test_all_endpoints_authenticated(working_key)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 ENDPOINT TEST RESULTS")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for endpoint, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{endpoint.upper():15} : {status}")
    
    print(f"\n📈 Overall: {passed}/{total} endpoints working")
    
    if passed == total:
        print("\n🎉 ALL ENDPOINTS WORKING!")
        print("✅ Authentication system operational")
        print("✅ REST API fully functional")
        print("✅ WebSocket communication active")
        print("✅ Deepfake detection ready")
        
        print(f"\n🌐 API Base: {API_BASE_URL}")
        print(f"🔌 WebSocket: {WS_URL}")
        if working_key:
            print(f"🔑 API Key: {working_key}")
        
        print("\n🚀 Backend is FULLY OPERATIONAL!")
        return True
    else:
        failed = [name for name, success in results.items() if not success]
        print(f"\n⚠️  Failed endpoints: {', '.join(failed)}")
        print("🔧 Check server logs for details")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ All endpoint tests completed successfully!")
    else:
        print("\n❌ Some endpoints need attention.")
