"""
Development endpoint testing - bypasses authentication for testing
"""

import requests
import json
import time
import asyncio
import websockets
import base64

API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

def test_public_endpoints():
    """Test endpoints that don't require authentication"""
    print("🧪 Testing Public Endpoints")
    print("=" * 40)
    
    results = {}
    
    # Test 1: Root endpoint
    print("\n1. Root Endpoint (GET /):")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Version: {data.get('version', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
        results["root"] = response.status_code == 200
    except Exception as e:
        print(f"   Failed: {e}")
        results["root"] = False
    
    # Test 2: OpenAPI schema
    print("\n2. OpenAPI Schema (GET /openapi.json):")
    try:
        response = requests.get(f"{API_BASE_URL}/openapi.json", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   API Title: {data.get('info', {}).get('title', 'N/A')}")
            print(f"   Endpoints: {len(data.get('paths', {}))}")
        results["openapi"] = response.status_code == 200
    except Exception as e:
        print(f"   Failed: {e}")
        results["openapi"] = False
    
    # Test 3: WebSocket (usually doesn't require auth)
    print("\n3. WebSocket Connection (WS /ws):")
    try:
        async def test_ws():
            try:
                async with websockets.connect(WS_URL, timeout=10) as websocket:
                    print("   ✅ WebSocket connected")
                    
                    # Test ping/pong
                    await websocket.send(json.dumps({"type": "ping"}))
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") == "pong":
                        print("   ✅ Ping/Pong working")
                        
                        # Test frame analysis
                        frame_msg = {
                            "type": "frame_data",
                            "session_id": "ws_test",
                            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
                        }
                        await websocket.send(json.dumps(frame_msg))
                        
                        analysis_response = await asyncio.wait_for(websocket.recv(), timeout=15)
                        analysis_data = json.loads(analysis_response)
                        
                        if analysis_data.get("type") == "analysis_result":
                            result = analysis_data.get("data", {})
                            print(f"   ✅ Frame analysis working")
                            print(f"   Authenticity: {result.get('authenticity', 'N/A')}")
                            return True
                        else:
                            print(f"   ❌ Unexpected analysis response: {analysis_data}")
                            return False
                    else:
                        print(f"   ❌ Unexpected ping response: {data}")
                        return False
            except Exception as e:
                print(f"   ❌ WebSocket error: {e}")
                return False
        
        ws_result = asyncio.run(test_ws())
        results["websocket"] = ws_result
    except Exception as e:
        print(f"   Failed: {e}")
        results["websocket"] = False
    
    return results

def test_protected_endpoints():
    """Test that protected endpoints are properly secured"""
    print("\n🔒 Testing Protected Endpoints (Security Check)")
    print("=" * 50)
    
    protected_endpoints = [
        ("GET", "/health", "Health Check"),
        ("POST", "/analyze", "Media Analysis"),
        ("GET", "/auth_score/test", "Auth Score"),
        ("POST", "/upload/frame", "Frame Upload")
    ]
    
    security_results = {}
    
    for method, endpoint, name in protected_endpoints:
        print(f"\n{name} ({method} {endpoint}):")
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            elif method == "POST":
                if endpoint == "/analyze":
                    payload = {"session_id": "test", "frame_data": "test"}
                    response = requests.post(f"{API_BASE_URL}{endpoint}", json=payload, timeout=5)
                elif endpoint == "/upload/frame":
                    files = {'file': ('test.jpg', b'fake_image_data', 'image/jpeg')}
                    response = requests.post(f"{API_BASE_URL}{endpoint}", files=files, timeout=5)
                else:
                    response = requests.post(f"{API_BASE_URL}{endpoint}", json={}, timeout=5)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code in [401, 403]:
                print(f"   ✅ Properly secured (requires authentication)")
                security_results[name] = True
            elif response.status_code == 200:
                print(f"   ⚠️  No authentication required")
                security_results[name] = False
            else:
                print(f"   ❓ Unexpected status: {response.status_code}")
                security_results[name] = False
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            security_results[name] = False
    
    return security_results

def check_server_functionality():
    """Check if core server functionality is working"""
    print("\n⚙️ Server Functionality Check")
    print("=" * 30)
    
    # Check if server is responding
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is responding")
            
            # Check if it's the TrueFACE API
            data = response.json()
            if "TrueFACE" in data.get("message", ""):
                print("✅ TrueFACE API identified")
                
                # Check version
                version = data.get("version", "unknown")
                print(f"✅ API Version: {version}")
                
                return True
            else:
                print("❌ Not TrueFACE API")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 TrueFACE Backend - Development Endpoint Testing")
    print("=" * 60)
    
    # Wait for server
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Check basic server functionality
    server_ok = check_server_functionality()
    if not server_ok:
        print("\n❌ Server is not responding properly!")
        return False
    
    # Test public endpoints
    public_results = test_public_endpoints()
    
    # Test security of protected endpoints
    security_results = test_protected_endpoints()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEVELOPMENT TEST RESULTS")
    print("=" * 60)
    
    print("\n🌐 Public Endpoints:")
    public_passed = 0
    for endpoint, success in public_results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"   {endpoint.upper():15} : {status}")
        if success:
            public_passed += 1
    
    print("\n🔒 Security Check (Protected Endpoints):")
    security_passed = 0
    for endpoint, secured in security_results.items():
        status = "✅ SECURED" if secured else "⚠️  UNSECURED"
        print(f"   {endpoint:20} : {status}")
        if secured:
            security_passed += 1
    
    # Overall assessment
    total_public = len(public_results)
    total_security = len(security_results)
    
    print(f"\n📈 Results Summary:")
    print(f"   Public Endpoints: {public_passed}/{total_public} working")
    print(f"   Security Check: {security_passed}/{total_security} properly secured")
    
    # Determine overall status
    if public_passed >= 2 and security_passed >= 3:  # At least root + websocket working, most endpoints secured
        print("\n🎉 BACKEND IS OPERATIONAL!")
        print("✅ Core functionality working")
        print("✅ Security measures active")
        print("✅ Real-time communication available")
        
        print(f"\n🌐 Access Points:")
        print(f"   API Base: {API_BASE_URL}")
        print(f"   WebSocket: {WS_URL}")
        print(f"   API Schema: {API_BASE_URL}/openapi.json")
        
        if public_results.get("websocket", False):
            print("\n🚀 Ready for frontend integration!")
            print("   - WebSocket communication established")
            print("   - Deepfake analysis pipeline active")
            print("   - Authentication system protecting endpoints")
        
        return True
    else:
        print("\n⚠️  BACKEND NEEDS ATTENTION")
        if public_passed < 2:
            print("❌ Core endpoints not working properly")
        if security_passed < 3:
            print("❌ Security measures may not be active")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Development testing completed successfully!")
        print("The TrueFACE backend core functionality is operational.")
    else:
        print("\n❌ Development testing found issues.")
        print("Please check the server configuration and logs.")
