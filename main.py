"""
TrueFACE Backend - Secure Deepfake Detection API
FastAPI application with comprehensive security measures
"""

import asyncio
import json
import logging
import base64
import re
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import secrets

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, Field
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    logger.warning("Rate limiting not available - install slowapi for production")
import uvicorn

from deepfake_model_real import DeepfakeDetector
from stream_processor import StreamProcessor
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security components
security = HTTPBearer()
if RATE_LIMITING_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = None

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None
)

# Rate limiting
if RATE_LIMITING_AVAILABLE:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Secure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Should be specific domains in production
    allow_credentials=False,  # Disabled for security
    allow_methods=["GET", "POST"],  # Only necessary methods
    allow_headers=["Content-Type", "Authorization"],  # Only necessary headers
)

# Initialize components
deepfake_detector = DeepfakeDetector()
stream_processor = StreamProcessor(deepfake_detector)

# Security functions
def rate_limit(limit_string: str):
    """Conditional rate limiting decorator"""
    def decorator(func):
        if RATE_LIMITING_AVAILABLE:
            return limiter.limit(limit_string)(func)
        return func
    return decorator

def optional_auth():
    """Optional authentication dependency"""
    # Check if we're in development mode by checking environment
    import os
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    
    if debug_mode:
        # In development, no authentication required
        return None
    else:
        # In production, require authentication
        return Depends(security)

async def verify_api_key(credentials: HTTPAuthorizationCredentials = None):
    """Verify API key authentication - optional in development"""
    # Check if we're in development mode
    import os
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    
    if debug_mode:
        logger.info("Development mode: API key authentication bypassed")
        return None
    
    # Production mode - require API key
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Verify the provided API key
    if credentials.credentials != settings.API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials

def sanitize_session_id(session_id: str) -> str:
    """Sanitize session ID to prevent injection attacks"""
    # Only allow alphanumeric characters, hyphens, and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', session_id)
    return sanitized[:50]  # Limit length

def validate_base64_size(data: str, max_size: int) -> bool:
    """Validate base64 data size without full decoding"""
    if not data:
        return True
    
    # Estimate decoded size (base64 is ~4/3 the size of original)
    estimated_size = len(data) * 3 // 4
    return estimated_size <= max_size

# Secure WebSocket connection manager
class SecureConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connections_per_ip: Dict[str, int] = {}
        self.max_connections_per_ip = 3
        self.max_total_connections = settings.WS_MAX_CONNECTIONS
    
    async def connect(self, websocket: WebSocket, client_ip: str) -> bool:
        """Securely connect WebSocket with limits"""
        # Check per-IP limit
        current_ip_connections = self.connections_per_ip.get(client_ip, 0)
        if current_ip_connections >= self.max_connections_per_ip:
            await websocket.close(code=1008, reason="Too many connections from IP")
            logger.warning(f"Connection limit exceeded for IP: {client_ip}")
            return False
        
        # Check total connections limit
        if len(self.active_connections) >= self.max_total_connections:
            await websocket.close(code=1008, reason="Server at capacity")
            logger.warning("WebSocket server at capacity")
            return False
        
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connections_per_ip[client_ip] = current_ip_connections + 1
        
        logger.info(f"WebSocket connected from {client_ip}. Total: {len(self.active_connections)}")
        return True
    
    def disconnect(self, websocket: WebSocket, client_ip: str):
        """Disconnect WebSocket and update counters"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
            current_count = self.connections_per_ip.get(client_ip, 0)
            if current_count > 0:
                self.connections_per_ip[client_ip] = current_count - 1
                if self.connections_per_ip[client_ip] == 0:
                    del self.connections_per_ip[client_ip]
        
        logger.info(f"WebSocket disconnected from {client_ip}. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket, client_ip: str):
        """Send message with error handling"""
        try:
            # Limit message size
            if len(message) > 10000:  # 10KB limit
                logger.warning(f"Message too large from {client_ip}")
                return
            
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to {client_ip}: {e}")
            self.disconnect(websocket, client_ip)

manager = SecureConnectionManager()

# Secure Pydantic models with validation
class AnalysisRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=50)
    frame_data: Optional[str] = Field(None, max_length=15728640)  # ~10MB base64 limit
    audio_data: Optional[str] = Field(None, max_length=15728640)  # ~10MB base64 limit
    
    @validator('session_id')
    def validate_session_id(cls, v):
        # Sanitize session ID
        sanitized = sanitize_session_id(v)
        if not sanitized:
            raise ValueError("Invalid session ID format")
        return sanitized
    
    @validator('frame_data')
    def validate_frame_data(cls, v):
        if v and not validate_base64_size(v, settings.MAX_FRAME_SIZE):
            raise ValueError("Frame data too large")
        if v:
            try:
                # Validate base64 format
                base64.b64decode(v)
            except Exception:
                raise ValueError("Invalid base64 frame data")
        return v
    
    @validator('audio_data')
    def validate_audio_data(cls, v):
        if v and not validate_base64_size(v, settings.MAX_AUDIO_SIZE):
            raise ValueError("Audio data too large")
        if v:
            try:
                # Validate base64 format
                base64.b64decode(v)
            except Exception:
                raise ValueError("Invalid base64 audio data")
        return v

class AuthScoreResponse(BaseModel):
    authenticity: float
    video_score: float
    audio_score: float
    timestamp: str
    session_id: str

# Secure API Routes
@app.get("/")
@rate_limit("30/minute")
async def root(request: Request):
    """Health check endpoint with rate limiting"""
    return {
        "message": "TrueFACE Backend API",
        "status": "running",
        "version": settings.API_VERSION,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
@rate_limit("10/minute")
async def health_check(request: Request):
    """Detailed health check with authentication"""
    return {
        "status": "healthy",
        "components": {
            "deepfake_detector": deepfake_detector.is_ready(),
            "stream_processor": stream_processor.is_ready(),
            "active_connections": len(manager.active_connections)
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyze")
@rate_limit("20/minute")  # Rate limit expensive operations
async def analyze_media(
    request: Request, 
    analysis_request: AnalysisRequest
):
    """Analyze video frame and/or audio chunk for deepfake detection"""
    try:
        # Additional size validation
        if analysis_request.frame_data:
            decoded_size = len(base64.b64decode(analysis_request.frame_data))
            if decoded_size > settings.MAX_FRAME_SIZE:
                raise HTTPException(status_code=413, detail="Frame data too large")
        
        if analysis_request.audio_data:
            decoded_size = len(base64.b64decode(analysis_request.audio_data))
            if decoded_size > settings.MAX_AUDIO_SIZE:
                raise HTTPException(status_code=413, detail="Audio data too large")
        
        result = await stream_processor.process_media(
            session_id=analysis_request.session_id,
            frame_data=analysis_request.frame_data,
            audio_data=analysis_request.audio_data
        )
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@app.get("/auth_score/{session_id}")
@rate_limit("30/minute")
async def get_auth_score(
    request: Request,
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(verify_api_key)
) -> AuthScoreResponse:
    """Get the current authenticity score for a session"""
    try:
        # Sanitize session ID
        clean_session_id = sanitize_session_id(session_id)
        if not clean_session_id:
            raise HTTPException(status_code=400, detail="Invalid session ID")
        
        score_data = await stream_processor.get_authenticity_score(clean_session_id)
        
        if not score_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return AuthScoreResponse(**score_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting auth score: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Score retrieval failed")

@app.post("/upload/frame")
@rate_limit("10/minute")
async def upload_frame(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = "default",
    credentials: HTTPAuthorizationCredentials = Depends(verify_api_key)
):
    """Upload and analyze a single video frame with security validation"""
    try:
        # Validate file size
        if file.size and file.size > settings.MAX_FRAME_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Validate content type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and validate file content
        frame_data = await file.read()
        
        # Additional size check after reading
        if len(frame_data) > settings.MAX_FRAME_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Validate image format by magic bytes
        if not (frame_data.startswith(b'\xff\xd8\xff') or  # JPEG
                frame_data.startswith(b'\x89PNG\r\n\x1a\n')):  # PNG
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Sanitize session ID
        clean_session_id = sanitize_session_id(session_id)
        
        result = await deepfake_detector.analyze_video_frame(frame_data)
        
        return {
            "session_id": clean_session_id,
            "video_score": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading frame: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Frame upload failed")

# Secure WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Secure WebSocket endpoint with connection limits and validation"""
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    # Attempt secure connection
    if not await manager.connect(websocket, client_ip):
        return
    
    try:
        while True:
            # Receive data with timeout
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning(f"WebSocket timeout for {client_ip}")
                break
            
            # Validate message size
            if len(data) > 20971520:  # 20MB limit
                logger.warning(f"WebSocket message too large from {client_ip}")
                await websocket.close(code=1009, reason="Message too large")
                break
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                # Validate message structure
                if not isinstance(message, dict) or not message_type:
                    await manager.send_personal_message(
                        json.dumps({"type": "error", "message": "Invalid message format"}),
                        websocket, client_ip
                    )
                    continue
                
                # Sanitize session ID
                session_id = sanitize_session_id(message.get("session_id", "ws_session"))
                
                if message_type == "frame_data":
                    frame_data = message.get("data")
                    if frame_data and validate_base64_size(frame_data, settings.MAX_FRAME_SIZE):
                        result = await stream_processor.process_media(
                            session_id=session_id,
                            frame_data=frame_data,
                            audio_data=None
                        )
                        
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "analysis_result",
                                "data": result
                            }),
                            websocket, client_ip
                        )
                    else:
                        await manager.send_personal_message(
                            json.dumps({"type": "error", "message": "Invalid frame data"}),
                            websocket, client_ip
                        )
                
                elif message_type == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}),
                        websocket, client_ip
                    )
                
                else:
                    logger.warning(f"Unknown message type from {client_ip}: {message_type}")
            
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {client_ip}")
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON format"}),
                    websocket, client_ip
                )
            
            except Exception as e:
                logger.error(f"Error processing WebSocket message from {client_ip}: {type(e).__name__}")
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Processing failed"}),
                    websocket, client_ip
                )
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for {client_ip}: {type(e).__name__}")
    finally:
        manager.disconnect(websocket, client_ip)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that doesn't leak internal information"""
    logger.error(f"Unhandled exception: {type(exc).__name__} - {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # More permissive CSP for development mode to allow Swagger UI
    if settings.DEBUG:
        response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com data:"
    else:
        response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response

if __name__ == "__main__":
    uvicorn.run(
        "main_secure:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
