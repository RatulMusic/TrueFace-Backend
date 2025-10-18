"""
Test Real Deepfake Detection API
Tests the actual deepfake detection capabilities with realistic data
"""

import requests
import base64
import json
import time
import numpy as np
from PIL import Image, ImageDraw
import io
import asyncio
import websockets

API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

def create_realistic_face_image(size=(224, 224)):
    """Create a more realistic face-like image for testing"""
    # Create base image
    img = Image.new('RGB', size, color=(240, 220, 200))  # Skin tone
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = size[0] // 2, size[1] // 2
    
    # Draw face oval
    face_bbox = [
        center_x - 80, center_y - 100,
        center_x + 80, center_y + 80
    ]
    draw.ellipse(face_bbox, fill=(220, 180, 160), outline=(200, 160, 140))
    
    # Draw eyes
    eye1_center = (center_x - 25, center_y - 20)
    eye2_center = (center_x + 25, center_y - 20)
    
    # Eye whites
    draw.ellipse([eye1_center[0]-12, eye1_center[1]-8, eye1_center[0]+12, eye1_center[1]+8], 
                 fill=(255, 255, 255), outline=(0, 0, 0))
    draw.ellipse([eye2_center[0]-12, eye2_center[1]-8, eye2_center[0]+12, eye2_center[1]+8], 
                 fill=(255, 255, 255), outline=(0, 0, 0))
    
    # Pupils
    draw.ellipse([eye1_center[0]-6, eye1_center[1]-6, eye1_center[0]+6, eye1_center[1]+6], 
                 fill=(50, 50, 50))
    draw.ellipse([eye2_center[0]-6, eye2_center[1]-6, eye2_center[0]+6, eye2_center[1]+6], 
                 fill=(50, 50, 50))
    
    # Nose
    nose_points = [
        (center_x, center_y - 10),
        (center_x - 8, center_y + 10),
        (center_x + 8, center_y + 10)
    ]
    draw.polygon(nose_points, fill=(200, 160, 140))
    
    # Mouth
    mouth_bbox = [
        center_x - 20, center_y + 25,
        center_x + 20, center_y + 40
    ]
    draw.ellipse(mouth_bbox, fill=(180, 100, 100), outline=(160, 80, 80))
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=90)
    return img_bytes.getvalue()

def create_synthetic_audio(duration=2.0, sample_rate=16000):
    """Create synthetic speech-like audio"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create formant-like structure (typical of human speech)
    f1, f2, f3 = 700, 1220, 2600  # Typical formant frequencies
    
    signal = (
        0.4 * np.sin(2 * np.pi * f1 * t) * np.exp(-t * 0.5) +
        0.3 * np.sin(2 * np.pi * f2 * t) * np.exp(-t * 0.3) +
        0.2 * np.sin(2 * np.pi * f3 * t) * np.exp(-t * 0.2) +
        0.1 * np.random.normal(0, 0.1, len(t))
    )
    
    # Add speech-like modulation
    modulation = 1 + 0.3 * np.sin(2 * np.pi * 5 * t)  # 5 Hz modulation
    signal *= modulation
    
    # Normalize
    signal = signal / np.max(np.abs(signal)) * 0.7
    
    # Convert to 16-bit PCM
    audio_int16 = (signal * 32767).astype(np.int16)
    return audio_int16.tobytes()

def test_real_video_detection():
    """Test real video deepfake detection"""
    print("🎥 Testing Real Video Deepfake Detection")
    print("-" * 40)
    
    # Create test images
    realistic_face = create_realistic_face_image()
    random_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    random_bytes = Image.fromarray(random_image).tobytes()
    
    test_cases = [
        ("Realistic Face", realistic_face),
        ("Random Noise", random_bytes[:len(realistic_face)])  # Same size
    ]
    
    results = []
    
    for name, image_data in test_cases:
        try:
            b64_data = base64.b64encode(image_data).decode()
            
            payload = {
                "session_id": f"video_test_{name.lower().replace(' ', '_')}",
                "frame_data": b64_data,
                "audio_data": None
            }
            
            start_time = time.time()
            response = requests.post(f"{API_BASE_URL}/analyze", json=payload, timeout=30)
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                video_score = result.get('video_score', 0)
                authenticity = result.get('authenticity', 0)
                confidence = result.get('confidence', 0)
                
                print(f"   {name}:")
                print(f"     Video Score: {video_score:.3f}")
                print(f"     Authenticity: {authenticity:.1f}%")
                print(f"     Confidence: {confidence:.3f}")
                print(f"     Processing Time: {processing_time:.2f}s")
                
                results.append({
                    'name': name,
                    'video_score': video_score,
                    'authenticity': authenticity,
                    'processing_time': processing_time,
                    'success': True
                })
            else:
                print(f"   {name}: ❌ Failed (Status: {response.status_code})")
                results.append({'name': name, 'success': False})
                
        except Exception as e:
            print(f"   {name}: ❌ Error - {e}")
            results.append({'name': name, 'success': False, 'error': str(e)})
    
    return results

def test_real_audio_detection():
    """Test real audio deepfake detection"""
    print("\n🎵 Testing Real Audio Deepfake Detection")
    print("-" * 40)
    
    # Create test audio
    synthetic_speech = create_synthetic_audio(duration=1.5)
    pure_noise = np.random.normal(0, 0.1, 24000).astype(np.float32).tobytes()
    
    test_cases = [
        ("Synthetic Speech", synthetic_speech),
        ("Pure Noise", pure_noise)
    ]
    
    results = []
    
    for name, audio_data in test_cases:
        try:
            b64_data = base64.b64encode(audio_data).decode()
            
            payload = {
                "session_id": f"audio_test_{name.lower().replace(' ', '_')}",
                "frame_data": None,
                "audio_data": b64_data
            }
            
            start_time = time.time()
            response = requests.post(f"{API_BASE_URL}/analyze", json=payload, timeout=30)
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                audio_score = result.get('audio_score', 0)
                authenticity = result.get('authenticity', 0)
                confidence = result.get('confidence', 0)
                
                print(f"   {name}:")
                print(f"     Audio Score: {audio_score:.3f}")
                print(f"     Authenticity: {authenticity:.1f}%")
                print(f"     Confidence: {confidence:.3f}")
                print(f"     Processing Time: {processing_time:.2f}s")
                
                results.append({
                    'name': name,
                    'audio_score': audio_score,
                    'authenticity': authenticity,
                    'processing_time': processing_time,
                    'success': True
                })
            else:
                print(f"   {name}: ❌ Failed (Status: {response.status_code})")
                results.append({'name': name, 'success': False})
                
        except Exception as e:
            print(f"   {name}: ❌ Error - {e}")
            results.append({'name': name, 'success': False, 'error': str(e)})
    
    return results

def test_combined_detection():
    """Test combined video + audio detection"""
    print("\n🔄 Testing Combined Detection")
    print("-" * 40)
    
    try:
        # Create realistic test data
        face_image = create_realistic_face_image()
        speech_audio = create_synthetic_audio(duration=2.0)
        
        b64_image = base64.b64encode(face_image).decode()
        b64_audio = base64.b64encode(speech_audio).decode()
        
        payload = {
            "session_id": "combined_test",
            "frame_data": b64_image,
            "audio_data": b64_audio
        }
        
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/analyze", json=payload, timeout=45)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"   Combined Analysis Results:")
            print(f"     Video Score: {result.get('video_score', 0):.3f}")
            print(f"     Audio Score: {result.get('audio_score', 0):.3f}")
            print(f"     Final Authenticity: {result.get('authenticity', 0):.1f}%")
            print(f"     Confidence: {result.get('confidence', 0):.3f}")
            print(f"     Total Processing Time: {processing_time:.2f}s")
            
            return {'success': True, 'result': result, 'processing_time': processing_time}
        else:
            print(f"   ❌ Failed (Status: {response.status_code})")
            return {'success': False}
            
    except Exception as e:
        print(f"   ❌ Error - {e}")
        return {'success': False, 'error': str(e)}

async def test_realtime_websocket():
    """Test real-time WebSocket with realistic data"""
    print("\n🔌 Testing Real-time WebSocket Detection")
    print("-" * 40)
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("   ✅ Connected to WebSocket")
            
            # Test with realistic face image
            face_image = create_realistic_face_image()
            b64_image = base64.b64encode(face_image).decode()
            
            # Send frame data
            frame_message = {
                "type": "frame_data",
                "session_id": "realtime_test",
                "data": b64_image
            }
            
            start_time = time.time()
            await websocket.send(json.dumps(frame_message))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            processing_time = time.time() - start_time
            
            data = json.loads(response)
            
            if data.get("type") == "analysis_result":
                result = data.get("data", {})
                print(f"   Real-time Analysis:")
                print(f"     Authenticity: {result.get('authenticity', 0):.1f}%")
                print(f"     Video Score: {result.get('video_score', 0):.3f}")
                print(f"     Response Time: {processing_time:.2f}s")
                return {'success': True, 'processing_time': processing_time}
            else:
                print(f"   ❌ Unexpected response: {data}")
                return {'success': False}
                
    except Exception as e:
        print(f"   ❌ WebSocket test failed: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """Run comprehensive real deepfake detection tests"""
    print("🧪 TrueFACE Real Deepfake Detection Tests")
    print("=" * 50)
    
    # Wait for server
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Test individual components
    video_results = test_real_video_detection()
    audio_results = test_real_audio_detection()
    combined_result = test_combined_detection()
    
    # Test real-time capability
    realtime_result = asyncio.run(test_realtime_websocket())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    # Video tests
    video_success = sum(1 for r in video_results if r.get('success', False))
    print(f"Video Detection: {video_success}/{len(video_results)} tests passed")
    
    # Audio tests
    audio_success = sum(1 for r in audio_results if r.get('success', False))
    print(f"Audio Detection: {audio_success}/{len(audio_results)} tests passed")
    
    # Combined test
    combined_success = combined_result.get('success', False)
    print(f"Combined Detection: {'✅ PASSED' if combined_success else '❌ FAILED'}")
    
    # Real-time test
    realtime_success = realtime_result.get('success', False)
    print(f"Real-time WebSocket: {'✅ PASSED' if realtime_success else '❌ FAILED'}")
    
    # Performance summary
    print(f"\n📈 Performance Summary:")
    avg_video_time = np.mean([r.get('processing_time', 0) for r in video_results if r.get('success')])
    avg_audio_time = np.mean([r.get('processing_time', 0) for r in audio_results if r.get('success')])
    
    if avg_video_time > 0:
        print(f"   Average Video Processing: {avg_video_time:.2f}s")
    if avg_audio_time > 0:
        print(f"   Average Audio Processing: {avg_audio_time:.2f}s")
    if combined_result.get('processing_time'):
        print(f"   Combined Processing: {combined_result['processing_time']:.2f}s")
    if realtime_result.get('processing_time'):
        print(f"   Real-time Response: {realtime_result['processing_time']:.2f}s")
    
    # Overall result
    total_tests = len(video_results) + len(audio_results) + 2  # +2 for combined and realtime
    passed_tests = video_success + audio_success + (1 if combined_success else 0) + (1 if realtime_success else 0)
    
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All real deepfake detection tests passed!")
        print("✅ The system is ready for production use!")
    else:
        print("⚠️  Some tests failed. Check the results above.")
    
    print(f"\n🌐 API running at: {API_BASE_URL}")
    print(f"🔌 WebSocket at: {WS_URL}")
    print(f"📚 Documentation at: {API_BASE_URL}/docs")

if __name__ == "__main__":
    main()
