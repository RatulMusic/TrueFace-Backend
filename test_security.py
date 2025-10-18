"""
Security Test Suite for TrueFACE Backend
Tests various security vulnerabilities and protections
"""

import requests
import json
import time
import base64
import asyncio
import websockets
from concurrent.futures import ThreadPoolExecutor
import threading

API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

def test_cors_security():
    """Test CORS configuration"""
    print("🔒 Testing CORS Security...")
    
    # Test with malicious origin
    headers = {
        'Origin': 'https://malicious-site.com',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
    }
    
    try:
        response = requests.options(f"{API_BASE_URL}/analyze", headers=headers)
        cors_header = response.headers.get('Access-Control-Allow-Origin', '')
        
        if cors_header == '*':
            print("   ❌ CRITICAL: CORS allows all origins (*)")
            return False
        else:
            print("   ✅ CORS properly configured")
            return True
    except Exception as e:
        print(f"   ❌ CORS test failed: {e}")
        return False

def test_authentication():
    """Test API authentication"""
    print("🔑 Testing Authentication...")
    
    # Test without API key
    try:
        response = requests.post(f"{API_BASE_URL}/analyze", json={
            "session_id": "test",
            "frame_data": "test"
        })
        
        if response.status_code == 401:
            print("   ✅ Authentication required")
            return True
        else:
            print("   ❌ CRITICAL: No authentication required")
            return False
    except Exception as e:
        print(f"   ❌ Auth test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting protection"""
    print("⏱️ Testing Rate Limiting...")
    
    def make_request():
        try:
            return requests.get(f"{API_BASE_URL}/", timeout=5)
        except:
            return None
    
    # Make rapid requests
    start_time = time.time()
    responses = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        responses = [f.result() for f in futures if f.result()]
    
    # Check for rate limiting
    rate_limited = any(r.status_code == 429 for r in responses if r)
    
    if rate_limited:
        print("   ✅ Rate limiting active")
        return True
    else:
        print("   ❌ WARNING: No rate limiting detected")
        return False

def test_input_validation():
    """Test input validation"""
    print("🛡️ Testing Input Validation...")
    
    test_cases = [
        # Oversized data
        {
            "session_id": "test",
            "frame_data": "A" * 20000000,  # 20MB of data
            "expected": 422  # Validation error
        },
        # Invalid session ID
        {
            "session_id": "../../../etc/passwd",
            "frame_data": "test",
            "expected": 422
        },
        # Invalid base64
        {
            "session_id": "test",
            "frame_data": "invalid_base64_data!!!",
            "expected": 422
        },
        # SQL injection attempt
        {
            "session_id": "'; DROP TABLE users; --",
            "frame_data": "test",
            "expected": 422
        }
    ]
    
    passed = 0
    for i, test_case in enumerate(test_cases):
        try:
            response = requests.post(f"{API_BASE_URL}/analyze", json={
                "session_id": test_case["session_id"],
                "frame_data": test_case.get("frame_data"),
                "audio_data": test_case.get("audio_data")
            }, timeout=10)
            
            if response.status_code == test_case["expected"]:
                print(f"   ✅ Test case {i+1}: Input validation working")
                passed += 1
            else:
                print(f"   ❌ Test case {i+1}: Expected {test_case['expected']}, got {response.status_code}")
        except Exception as e:
            print(f"   ❌ Test case {i+1}: Request failed - {e}")
    
    return passed == len(test_cases)

def test_file_upload_security():
    """Test file upload security"""
    print("📁 Testing File Upload Security...")
    
    # Test oversized file
    large_data = b"A" * (10 * 1024 * 1024)  # 10MB
    
    try:
        files = {'file': ('large.jpg', large_data, 'image/jpeg')}
        response = requests.post(f"{API_BASE_URL}/upload/frame", files=files, timeout=30)
        
        if response.status_code in [413, 422]:  # Payload too large or validation error
            print("   ✅ File size limits enforced")
            size_check = True
        else:
            print("   ❌ WARNING: No file size limits")
            size_check = False
    except Exception as e:
        print(f"   ❌ File upload test failed: {e}")
        size_check = False
    
    # Test malicious file type
    try:
        malicious_data = b"<?php system($_GET['cmd']); ?>"
        files = {'file': ('script.php', malicious_data, 'image/jpeg')}  # Fake content type
        response = requests.post(f"{API_BASE_URL}/upload/frame", files=files, timeout=10)
        
        if response.status_code in [400, 422]:
            print("   ✅ File type validation working")
            type_check = True
        else:
            print("   ❌ WARNING: Insufficient file type validation")
            type_check = False
    except Exception as e:
        print(f"   ❌ Malicious file test failed: {e}")
        type_check = False
    
    return size_check and type_check

async def test_websocket_security():
    """Test WebSocket security"""
    print("🔌 Testing WebSocket Security...")
    
    try:
        # Test connection limits
        connections = []
        max_connections = 10
        
        for i in range(max_connections):
            try:
                ws = await websockets.connect(WS_URL, timeout=5)
                connections.append(ws)
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"   Connection {i+1} failed: {e}")
                break
        
        if len(connections) < max_connections:
            print(f"   ✅ Connection limits enforced (max: {len(connections)})")
            connection_limit = True
        else:
            print("   ❌ WARNING: No connection limits detected")
            connection_limit = False
        
        # Test message size limits
        if connections:
            try:
                large_message = json.dumps({
                    "type": "frame_data",
                    "session_id": "test",
                    "data": "A" * (25 * 1024 * 1024)  # 25MB message
                })
                
                await connections[0].send(large_message)
                response = await asyncio.wait_for(connections[0].recv(), timeout=5)
                
                response_data = json.loads(response)
                if response_data.get("type") == "error":
                    print("   ✅ Message size limits enforced")
                    message_limit = True
                else:
                    print("   ❌ WARNING: No message size limits")
                    message_limit = False
            except Exception as e:
                print("   ✅ Message size limits enforced (connection closed)")
                message_limit = True
        else:
            message_limit = False
        
        # Close all connections
        for ws in connections:
            try:
                await ws.close()
            except:
                pass
        
        return connection_limit and message_limit
        
    except Exception as e:
        print(f"   ❌ WebSocket security test failed: {e}")
        return False

def test_error_handling():
    """Test error message security"""
    print("🚨 Testing Error Handling...")
    
    # Test that internal errors don't leak information
    try:
        # Trigger an internal error
        response = requests.post(f"{API_BASE_URL}/analyze", json={
            "session_id": "test",
            "frame_data": None,
            "audio_data": None
        })
        
        if response.status_code >= 500:
            error_detail = response.json().get("detail", "")
            
            # Check if error message is generic
            sensitive_keywords = ["traceback", "exception", "file", "line", "function", "module"]
            has_sensitive_info = any(keyword.lower() in error_detail.lower() for keyword in sensitive_keywords)
            
            if not has_sensitive_info:
                print("   ✅ Error messages are generic")
                return True
            else:
                print("   ❌ WARNING: Error messages may leak internal information")
                return False
        else:
            print("   ✅ Request handled properly")
            return True
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        return False

def test_security_headers():
    """Test security headers"""
    print("🛡️ Testing Security Headers...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/")
        headers = response.headers
        
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Content-Security-Policy': lambda x: x is not None
        }
        
        passed = 0
        for header, expected in security_headers.items():
            if callable(expected):
                if expected(headers.get(header)):
                    print(f"   ✅ {header} header present")
                    passed += 1
                else:
                    print(f"   ❌ {header} header missing")
            else:
                if headers.get(header) == expected:
                    print(f"   ✅ {header} header correct")
                    passed += 1
                else:
                    print(f"   ❌ {header} header incorrect or missing")
        
        return passed == len(security_headers)
    except Exception as e:
        print(f"   ❌ Security headers test failed: {e}")
        return False

async def run_security_tests():
    """Run comprehensive security test suite"""
    print("🔒 TrueFACE Backend Security Test Suite")
    print("=" * 50)
    
    tests = [
        ("CORS Security", test_cors_security),
        ("Authentication", test_authentication),
        ("Rate Limiting", test_rate_limiting),
        ("Input Validation", test_input_validation),
        ("File Upload Security", test_file_upload_security),
        ("Error Handling", test_error_handling),
        ("Security Headers", test_security_headers),
    ]
    
    results = {}
    
    # Run synchronous tests
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   ❌ Test crashed: {e}")
            results[test_name] = False
    
    # Run WebSocket test
    print(f"\nWebSocket Security:")
    try:
        results["WebSocket Security"] = await test_websocket_security()
    except Exception as e:
        print(f"   ❌ WebSocket test crashed: {e}")
        results["WebSocket Security"] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("🔒 SECURITY TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    critical_failures = []
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name:20} : {status}")
        
        if passed_test:
            passed += 1
        else:
            if test_name in ["CORS Security", "Authentication", "Rate Limiting"]:
                critical_failures.append(test_name)
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if critical_failures:
        print(f"\n🚨 CRITICAL SECURITY FAILURES:")
        for failure in critical_failures:
            print(f"   - {failure}")
        print("\n⚠️  DO NOT DEPLOY TO PRODUCTION WITH THESE FAILURES!")
    elif passed == total:
        print("\n🎉 All security tests passed!")
        print("✅ System appears secure for production deployment")
    else:
        print("\n⚠️  Some non-critical security tests failed")
        print("🔧 Review and fix issues before production deployment")
    
    return passed == total and not critical_failures

if __name__ == "__main__":
    print("Make sure the TrueFACE Backend server is running...")
    print("For secure testing, start with: python main_secure.py\n")
    
    success = asyncio.run(run_security_tests())
    
    if success:
        print("\n🛡️ Security validation complete - System ready for production!")
    else:
        print("\n🔧 Security issues detected - Fix before deployment!")
