"""
Real-Time Deepfake Detection Simulation
Simulates a browser extension sending video frames from Google Meet
"""

import asyncio
import websockets
import json
import base64
import time
from datetime import datetime
import numpy as np
from PIL import Image
from io import BytesIO

class GoogleMeetSimulator:
    def __init__(self, websocket_url="ws://localhost:8000/ws"):
        self.websocket_url = websocket_url
        self.websocket = None
        self.session_id = f"meet_user_{int(time.time())}"
        self.frame_count = 0
        self.running = False
        
    def create_fake_frame(self):
        """Create a fake video frame (simulates webcam capture)"""
        # Create a random 320x240 RGB image (simulating webcam frame)
        width, height = 320, 240
        
        # Generate random image data
        img_array = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        
        # Add some structure to make it look more like a face
        # Add a simple face-like pattern
        center_x, center_y = width // 2, height // 2
        
        # Face oval
        for y in range(height):
            for x in range(width):
                dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                if dist < 80:  # Face region
                    img_array[y, x] = [200, 180, 160]  # Skin tone
                    
        # Eyes
        img_array[center_y-20:center_y-10, center_x-30:center_x-20] = [50, 50, 50]  # Left eye
        img_array[center_y-20:center_y-10, center_x+20:center_x+30] = [50, 50, 50]  # Right eye
        
        # Convert to PIL Image
        img = Image.fromarray(img_array)
        
        # Convert to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_data = img_bytes.getvalue()
        
        # Encode to base64
        return base64.b64encode(img_data).decode('utf-8')
    
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            print(f"🔌 Connecting to {self.websocket_url}...")
            self.websocket = await websockets.connect(self.websocket_url)
            print(f"✅ Connected! Session ID: {self.session_id}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def send_ping(self):
        """Send ping to check connection health"""
        if self.websocket:
            ping_msg = {"type": "ping"}
            await self.websocket.send(json.dumps(ping_msg))
            print("📤 Ping sent")
    
    async def send_frame(self):
        """Send a video frame for analysis"""
        if not self.websocket:
            return False
            
        try:
            frame_data = self.create_fake_frame()
            
            message = {
                "type": "frame_data",
                "session_id": self.session_id,
                "data": frame_data
            }
            
            await self.websocket.send(json.dumps(message))
            self.frame_count += 1
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"📤 [{timestamp}] Frame #{self.frame_count} sent for analysis")
            return True
            
        except Exception as e:
            print(f"❌ Error sending frame: {e}")
            return False
    
    async def listen_for_responses(self):
        """Listen for analysis results"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if data.get("type") == "pong":
                    print(f"📥 [{timestamp}] Pong received - connection healthy")
                    
                elif data.get("type") == "analysis_result":
                    result = data.get("data", {})
                    authenticity = result.get("authenticity", 0)
                    video_score = result.get("video_score", 0)
                    confidence = result.get("confidence", 0)
                    
                    # Determine if it's likely real or fake
                    if authenticity >= 70:
                        status = "✅ LIKELY REAL"
                        color = "\033[92m"  # Green
                    elif authenticity <= 30:
                        status = "🚨 LIKELY DEEPFAKE"
                        color = "\033[91m"  # Red
                    else:
                        status = "⚠️ UNCERTAIN"
                        color = "\033[93m"  # Yellow
                    
                    reset_color = "\033[0m"
                    
                    print(f"📥 [{timestamp}] {color}ANALYSIS RESULT:{reset_color}")
                    print(f"   Authenticity: {authenticity}% ({status})")
                    print(f"   Video Score: {video_score}")
                    print(f"   Confidence: {confidence}")
                    print(f"   Session: {result.get('session_id', 'Unknown')}")
                    print("-" * 50)
                    
        except websockets.exceptions.ConnectionClosed:
            print("❌ Connection closed by server")
        except Exception as e:
            print(f"❌ Error receiving messages: {e}")
    
    async def simulate_real_time_analysis(self, duration_seconds=30, fps=2):
        """Simulate real-time video analysis"""
        print(f"🎥 Starting real-time simulation:")
        print(f"   Duration: {duration_seconds} seconds")
        print(f"   Frame rate: {fps} FPS")
        print(f"   Total frames: {duration_seconds * fps}")
        print("=" * 60)
        
        self.running = True
        frame_interval = 1.0 / fps
        
        # Start listening for responses in background
        listen_task = asyncio.create_task(self.listen_for_responses())
        
        try:
            start_time = time.time()
            
            while self.running and (time.time() - start_time) < duration_seconds:
                # Send frame
                success = await self.send_frame()
                if not success:
                    break
                
                # Wait for next frame
                await asyncio.sleep(frame_interval)
            
            print(f"\n🏁 Simulation completed!")
            print(f"   Total frames sent: {self.frame_count}")
            print(f"   Duration: {time.time() - start_time:.1f} seconds")
            
        except KeyboardInterrupt:
            print("\n⏹️ Simulation stopped by user")
        finally:
            self.running = False
            listen_task.cancel()
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            print("❌ Disconnected")

async def main():
    """Main function to run the simulation"""
    print("🎯 TrueFACE Real-Time Deepfake Detection Simulation")
    print("=" * 60)
    print("This simulates a browser extension analyzing video frames from Google Meet")
    print()
    
    simulator = GoogleMeetSimulator()
    
    # Connect to backend
    connected = await simulator.connect()
    if not connected:
        return
    
    try:
        # Send initial ping
        await simulator.send_ping()
        await asyncio.sleep(1)
        
        # Test single frame
        print("\n🧪 Testing single frame analysis...")
        await simulator.send_frame()
        await asyncio.sleep(2)
        
        # Start real-time simulation
        print("\n🎥 Starting real-time simulation...")
        print("Press Ctrl+C to stop")
        await simulator.simulate_real_time_analysis(duration_seconds=60, fps=1)
        
    except KeyboardInterrupt:
        print("\n⏹️ Stopping simulation...")
    finally:
        await simulator.disconnect()

if __name__ == "__main__":
    print("🚀 Starting TrueFACE Real-Time Test...")
    print("Make sure the TrueFACE backend is running on localhost:8000")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
