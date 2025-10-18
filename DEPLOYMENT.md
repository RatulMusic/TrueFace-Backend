# 🚀 TrueFACE Backend Deployment Guide

## Quick Start (Local Development)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
python start.py
# OR
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. Test the API
python test_api.py
```

**Local URLs:**
- API: http://localhost:8000
- WebSocket: ws://localhost:8000/ws  
- Docs: http://localhost:8000/docs

## ☁️ Cloud Deployment Options

### 1. Render.com (Recommended)

**Steps:**
1. Fork/clone this repository to GitHub
2. Connect GitHub to Render.com
3. Create new Web Service
4. Use repository root as source
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Deploy!

**Environment Variables to Set:**
```
DEBUG=false
LOG_LEVEL=INFO
MODEL_DEVICE=cpu
MAX_SESSIONS=50
```

**Result:**
- API: `https://your-app-name.onrender.com`
- WebSocket: `wss://your-app-name.onrender.com/ws`

### 2. Railway

**Steps:**
1. Connect repository to Railway
2. Deploy automatically using `railway.json`
3. Set environment variables in dashboard

**Environment Variables:**
```
DEBUG=false
LOG_LEVEL=INFO
MODEL_DEVICE=cpu
MAX_SESSIONS=50
```

**Result:**
- API: `https://your-app-name.up.railway.app`
- WebSocket: `wss://your-app-name.up.railway.app/ws`

### 3. Google Cloud Run

**Steps:**
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/trueface-backend

# Deploy to Cloud Run
gcloud run deploy trueface-backend \
  --image gcr.io/PROJECT_ID/trueface-backend \
  --platform managed \
  --port 8000 \
  --set-env-vars DEBUG=false,LOG_LEVEL=INFO,MODEL_DEVICE=cpu
```

### 4. Docker Deployment

**Local Docker:**
```bash
# Build image
docker build -t trueface-backend .

# Run container
docker run -p 8000:8000 \
  -e DEBUG=false \
  -e LOG_LEVEL=INFO \
  trueface-backend
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  trueface-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
      - MODEL_DEVICE=cpu
```

## 🔧 Configuration

### Required Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `DEBUG` | false | Debug mode |
| `LOG_LEVEL` | INFO | Logging level |
| `MODEL_DEVICE` | auto | Device for models (cpu/cuda/auto) |
| `MAX_SESSIONS` | 100 | Maximum concurrent sessions |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VIDEO_WEIGHT` | 0.6 | Weight for video analysis |
| `AUDIO_WEIGHT` | 0.4 | Weight for audio analysis |
| `SESSION_TIMEOUT_MINUTES` | 30 | Session timeout |
| `WS_MAX_CONNECTIONS` | 50 | Max WebSocket connections |

## 📊 Performance Considerations

### Resource Requirements

**Minimum:**
- CPU: 1 vCPU
- RAM: 512MB
- Storage: 1GB

**Recommended:**
- CPU: 2 vCPUs
- RAM: 2GB
- Storage: 5GB

### Scaling

**Horizontal Scaling:**
- Deploy multiple instances behind a load balancer
- Use Redis for session storage (if needed)
- Configure sticky sessions for WebSocket connections

**Vertical Scaling:**
- Increase CPU for faster model inference
- Increase RAM for more concurrent sessions
- Use GPU instances for better performance

## 🔍 Monitoring & Health Checks

### Health Check Endpoints

```bash
# Basic health check
curl https://your-app.com/health

# Detailed status
curl https://your-app.com/
```

### Logging

The application logs to:
- Console (stdout)
- File: `trueface_backend.log`

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Metrics to Monitor

- Response time for `/analyze` endpoint
- WebSocket connection count
- Active session count
- Model inference time
- Memory usage
- CPU usage

## 🚨 Troubleshooting

### Common Issues

**1. Models not loading:**
```
Solution: Check MODEL_DEVICE setting, ensure sufficient RAM
```

**2. WebSocket connections failing:**
```
Solution: Verify WSS in production, check CORS settings
```

**3. High memory usage:**
```
Solution: Reduce MAX_SESSIONS, implement session cleanup
```

**4. Slow inference:**
```
Solution: Use GPU instances, optimize model size
```

### Debug Mode

Enable debug mode for detailed error messages:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## 🔒 Security Best Practices

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Configure proper CORS origins
- [ ] Use HTTPS/WSS in production
- [ ] Set up rate limiting
- [ ] Monitor for unusual traffic patterns
- [ ] Regular security updates
- [ ] Use environment variables for secrets

### API Security

```python
# Example: Add API key authentication
ALLOWED_ORIGINS = ["https://yourdomain.com"]
API_KEY = "your-secure-api-key"
```

## 📈 Performance Optimization

### Model Optimization

1. **Use quantized models** for faster inference
2. **Batch processing** for multiple frames
3. **Model caching** to avoid reloading
4. **Async processing** for concurrent requests

### Infrastructure Optimization

1. **CDN** for static assets
2. **Load balancing** for multiple instances
3. **Database** for session persistence
4. **Caching** for frequent requests

## 🧪 Testing in Production

### Smoke Tests

```bash
# Test basic functionality
curl https://your-app.com/health

# Test WebSocket (using wscat)
wscat -c wss://your-app.com/ws
```

### Load Testing

```python
# Use the provided test_api.py script
python test_api.py

# Or use tools like:
# - Apache Bench (ab)
# - wrk
# - Artillery
```

## 📞 Support & Maintenance

### Regular Maintenance

- Monitor logs for errors
- Update dependencies monthly
- Check resource usage
- Backup configuration
- Test disaster recovery

### Getting Help

1. Check logs first: `tail -f trueface_backend.log`
2. Verify configuration: Review environment variables
3. Test locally: Use `test_api.py`
4. Check documentation: Review API docs at `/docs`

---

**🎉 Your TrueFACE Backend is now ready for production!**

For the frontend integration, use the WebSocket URL provided above and follow the API documentation at `/docs`.
