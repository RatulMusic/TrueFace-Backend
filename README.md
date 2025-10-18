# TrueFACE Backend

Real-time deepfake detection and authenticity scoring API built with FastAPI.

## 🚀 Features

- **Real-time Analysis**: Process video frames and audio chunks in real-time
- **WebSocket Support**: Bi-directional communication for live streaming
- **Multi-modal Detection**: Combines video and audio analysis for better accuracy
- **Authenticity Scoring**: Provides confidence scores from 0-100
- **Session Management**: Tracks multiple concurrent analysis sessions
- **Cloud Ready**: Deployable on Render, Railway, Google Cloud Run
- **Scalable Architecture**: Async processing with background tasks

## 📋 API Endpoints

### REST API

- `GET /` - Health check and API information
- `GET /health` - Detailed health status
- `POST /analyze` - Analyze media data (video/audio)
- `GET /auth_score/{session_id}` - Get authenticity score for session
- `POST /upload/frame` - Upload single video frame
- `POST /upload/audio` - Upload single audio chunk

### WebSocket

- `WS /ws` - Real-time communication endpoint

## 🛠️ Installation

### Local Development

1. **Clone and navigate to backend directory**
```bash
cd Backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the application**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build image
docker build -t trueface-backend .

# Run container
docker run -p 8000:8000 trueface-backend
```

## ☁️ Cloud Deployment

### Render.com

1. Connect your GitHub repository to Render
2. Use the provided `render.yaml` configuration
3. Deploy automatically on push to main branch

**WebSocket URL**: `wss://your-app-name.onrender.com/ws`

### Railway

1. Connect repository to Railway
2. Use the provided `railway.json` configuration  
3. Deploy with one click

**WebSocket URL**: `wss://your-app-name.up.railway.app/ws`

### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/trueface-backend
gcloud run deploy --image gcr.io/PROJECT_ID/trueface-backend --platform managed
```

## 📡 WebSocket Communication

### Message Format

**Client to Server:**
```json
{
  "type": "frame_data",
  "session_id": "unique_session_id",
  "data": "base64_encoded_frame"
}
```

**Server to Client:**
```json
{
  "type": "analysis_result",
  "data": {
    "session_id": "unique_session_id",
    "authenticity": 87.5,
    "video_score": 0.82,
    "audio_score": 0.91,
    "confidence": 0.95,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Message Types

- `frame_data` - Send video frame for analysis
- `audio_data` - Send audio chunk for analysis  
- `get_score` - Request current authenticity score
- `ping` - Heartbeat message
- `analysis_result` - Analysis results from server
- `auth_score` - Current authenticity score
- `periodic_update` - Periodic score updates
- `error` - Error messages

## 🧠 Model Architecture

### Video Detection
- Face detection using OpenCV Haar Cascades
- CNN-based deepfake classification
- Visual artifact analysis (blur, edge inconsistencies)
- Temporal smoothing for stable scores

### Audio Detection  
- MFCC feature extraction using librosa
- Spectral analysis for synthetic voice detection
- Frequency pattern analysis
- Temporal consistency checking

### Score Calculation
```python
authenticity_score = (video_score * 0.6 + audio_score * 0.4) * 100
```

## 🔧 Configuration

Key configuration options in `config.py`:

```python
# Model weights
VIDEO_WEIGHT = 0.6
AUDIO_WEIGHT = 0.4

# Processing limits
MAX_FRAME_SIZE = 5MB
MAX_AUDIO_SIZE = 10MB
SESSION_TIMEOUT_MINUTES = 30

# WebSocket settings
WS_MAX_CONNECTIONS = 50
WS_HEARTBEAT_INTERVAL = 30
```

## 📊 Usage Examples

### REST API

```python
import requests
import base64

# Analyze video frame
with open("frame.jpg", "rb") as f:
    frame_data = base64.b64encode(f.read()).decode()

response = requests.post("http://localhost:8000/analyze", json={
    "session_id": "test_session",
    "frame_data": frame_data
})

print(response.json())
```

### WebSocket Client

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

// Send frame data
ws.send(JSON.stringify({
    type: 'frame_data',
    session_id: 'test_session',
    data: base64FrameData
}));

// Receive results
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Authenticity Score:', data.data.authenticity);
};
```

## 🔍 Monitoring

The API provides detailed health checks and metrics:

```bash
# Check API health
curl http://localhost:8000/health

# Response includes:
# - Model readiness status
# - Active WebSocket connections
# - System resources
# - Component status
```

## 🚨 Error Handling

The API handles various error scenarios:

- Invalid media formats
- Oversized uploads
- Model initialization failures
- WebSocket disconnections
- Session timeouts

All errors return structured JSON responses with appropriate HTTP status codes.

## 🔒 Security Considerations

- Rate limiting on API endpoints
- Input validation and sanitization
- Secure WebSocket connections (WSS in production)
- Environment variable configuration
- Non-root Docker container execution

## 📈 Performance Optimization

- Async processing for concurrent requests
- Background task management
- Session cleanup and memory management
- Efficient model inference
- Connection pooling for WebSockets

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create GitHub issues for bugs
- Check documentation for common questions
- Review logs for debugging information

---

**Built with ❤️ for real-time deepfake detection**
