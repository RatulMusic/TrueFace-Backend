"""
Test script for time-based analysis optimization
Tests the new 5-second interval analysis system
"""

import asyncio
import websockets
import json
import base64
import time
from datetime import datetime

class TimeBasedAnalysisTest:
    def __init__(self):
        self.websocket_url = "ws://localhost:8000/ws"
        self.websocket = None
        self.session_id = f"test_session_{int(time.time())}"
        self.test_results = []
        
    def create_test_frame(self):
        """Create a simple test frame"""
        # 1x1 pixel PNG in base64
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    
    async def connect(self):
        """Connect to WebSocket"""
        try:
            print(f"🔌 Connecting to {self.websocket_url}...")
            self.websocket = await websockets.connect(self.websocket_url)
            print(f"✅ Connected! Session ID: {self.session_id}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def send_frame(self, frame_number):
        """Send a test frame"""
        if not self.websocket:
            return None
            
        try:
            frame_data = self.create_test_frame()
            message = {
                "type": "frame_data",
                "session_id": self.session_id,
                "data": frame_data
            }
            
            start_time = time.time()
            await self.websocket.send(json.dumps(message))
            
            # Wait for response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            end_time = time.time()
            
            data = json.loads(response)
            if data.get("type") == "analysis_result":
                result = data.get("data", {})
                processing_time = (end_time - start_time) * 1000  # ms
                
                test_result = {
                    'frame_number': frame_number,
                    'timestamp': datetime.now().isoformat(),
                    'authenticity': result.get('authenticity', 0),
                    'analysis_type': 'full' if processing_time > 100 else 'cached',  # Estimate
                    'processing_time_ms': processing_time,
                    'session_id': result.get('session_id')
                }
                
                self.test_results.append(test_result)
                return test_result
            
        except Exception as e:
            print(f"❌ Error sending frame {frame_number}: {e}")
            return None
    
    async def test_time_based_analysis(self):
        """Test the time-based analysis system"""
        print("🧪 Testing Time-Based Analysis System")
        print("=" * 50)
        print(f"📊 Expected behavior:")
        print(f"   - First frame: Full analysis (~200-500ms)")
        print(f"   - Next 4 seconds: Cached results (~10-50ms)")
        print(f"   - After 5 seconds: Full analysis again")
        print()
        
        # Test rapid frame sending (simulating high FPS)
        print("🚀 Sending 10 frames rapidly (simulating 1 FPS for 10 seconds)...")
        
        for i in range(10):
            print(f"\n📤 Sending frame {i+1}/10...")
            
            result = await self.send_frame(i+1)
            if result:
                analysis_type = "🔍 FULL" if result['processing_time_ms'] > 100 else "💾 CACHED"
                print(f"📥 {analysis_type} | Score: {result['authenticity']:.1f}% | Time: {result['processing_time_ms']:.1f}ms")
            
            # Wait 1 second before next frame
            await asyncio.sleep(1)
        
        print("\n" + "=" * 50)
        self.analyze_results()
    
    def analyze_results(self):
        """Analyze test results"""
        if not self.test_results:
            print("❌ No results to analyze")
            return
        
        print("📊 ANALYSIS RESULTS:")
        print("-" * 30)
        
        full_analyses = [r for r in self.test_results if r['processing_time_ms'] > 100]
        cached_analyses = [r for r in self.test_results if r['processing_time_ms'] <= 100]
        
        print(f"🔍 Full Analyses: {len(full_analyses)}")
        print(f"💾 Cached Results: {len(cached_analyses)}")
        print(f"⚡ Efficiency: {len(cached_analyses)}/{len(self.test_results)} cached ({100*len(cached_analyses)/len(self.test_results):.1f}%)")
        
        if full_analyses:
            avg_full_time = sum(r['processing_time_ms'] for r in full_analyses) / len(full_analyses)
            print(f"⏱️ Avg Full Analysis Time: {avg_full_time:.1f}ms")
        
        if cached_analyses:
            avg_cached_time = sum(r['processing_time_ms'] for r in cached_analyses) / len(cached_analyses)
            print(f"⚡ Avg Cached Time: {avg_cached_time:.1f}ms")
        
        # Check authenticity scores
        scores = [r['authenticity'] for r in self.test_results]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        print(f"\n🎯 AUTHENTICITY SCORES:")
        print(f"   Average: {avg_score:.1f}%")
        print(f"   Range: {min_score:.1f}% - {max_score:.1f}%")
        
        # Expected: 77-94% for real faces with new optimizations
        if avg_score >= 75:
            print("✅ Scores look good for real faces!")
        elif avg_score >= 60:
            print("⚠️ Scores are moderate - may need calibration")
        else:
            print("❌ Scores are low - optimization may not be working")
        
        print(f"\n🔄 TIME-BASED ANALYSIS:")
        expected_full = 2  # Should have ~2 full analyses in 10 seconds (every 5 seconds)
        if len(full_analyses) <= expected_full + 1:
            print("✅ Time-based analysis working correctly!")
        else:
            print("⚠️ Too many full analyses - time-based optimization may not be working")
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            print("❌ Disconnected")

async def main():
    """Run the time-based analysis test"""
    print("🎯 TrueFACE Time-Based Analysis Test")
    print("=" * 50)
    print("This test verifies the new 5-second interval optimization")
    print("Make sure the TrueFACE backend is running on localhost:8000")
    print()
    
    tester = TimeBasedAnalysisTest()
    
    # Connect
    connected = await tester.connect()
    if not connected:
        return
    
    try:
        # Run test
        await tester.test_time_based_analysis()
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    finally:
        await tester.disconnect()

if __name__ == "__main__":
    print("🚀 Starting Time-Based Analysis Test...")
    asyncio.run(main())
