"""
Stream Processing Pipeline
Handles real-time processing of video and audio streams for deepfake detection
"""

import asyncio
import base64
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)

class StreamProcessor:
    """
    Manages real-time stream processing and authenticity score calculation
    """
    
    def __init__(self, deepfake_detector):
        self.deepfake_detector = deepfake_detector
        self.sessions: Dict[str, SessionData] = {}
        self.processing_queue = asyncio.Queue()
        self.is_processing = False
        
        # Start background processing
        asyncio.create_task(self._background_processor())
    
    def is_ready(self) -> bool:
        """Check if the stream processor is ready"""
        return self.deepfake_detector.is_ready()
    
    async def process_media(self, session_id: str, frame_data: Optional[str] = None, 
                          audio_data: Optional[str] = None) -> Dict[str, Any]:
        """
        Process incoming media data (video frame and/or audio chunk)
        
        Args:
            session_id: Unique session identifier
            frame_data: Base64 encoded video frame
            audio_data: Base64 encoded audio chunk
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Initialize session if it doesn't exist
            if session_id not in self.sessions:
                self.sessions[session_id] = SessionData(session_id)
            
            session = self.sessions[session_id]
            session.update_last_activity()
            
            # Process the media data
            results = await self._analyze_media_data(frame_data, audio_data)
            
            # Update session with new results
            session.add_analysis_result(results)
            
            # Calculate current authenticity score
            auth_score = self._calculate_authenticity_score(session)
            
            # Prepare response
            response = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "video_score": results.get("video_score", 0.5),
                "audio_score": results.get("audio_score", 0.5),
                "authenticity": auth_score,
                "confidence": session.get_confidence_level(),
                "sample_count": session.get_sample_count()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing media for session {session_id}: {e}")
            return {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "video_score": 0.5,
                "audio_score": 0.5,
                "authenticity": 50.0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _analyze_media_data(self, frame_data: Optional[str], 
                                audio_data: Optional[str]) -> Dict[str, float]:
        """
        Analyze the provided media data using the deepfake detector
        """
        results = {"video_score": 0.5, "audio_score": 0.5}
        
        try:
            # Convert base64 data to bytes if provided
            frame_bytes = None
            audio_bytes = None
            
            if frame_data:
                try:
                    frame_bytes = base64.b64decode(frame_data)
                except Exception as e:
                    logger.error(f"Error decoding frame data: {e}")
            
            if audio_data:
                try:
                    audio_bytes = base64.b64decode(audio_data)
                except Exception as e:
                    logger.error(f"Error decoding audio data: {e}")
            
            # Analyze using the deepfake detector
            analysis_results = await self.deepfake_detector.analyze_combined(
                frame_data=frame_bytes,
                audio_data=audio_bytes
            )
            
            results.update(analysis_results)
            
        except Exception as e:
            logger.error(f"Error in media analysis: {e}")
        
        return results
    
    def _calculate_authenticity_score(self, session: 'SessionData') -> float:
        """
        Calculate the overall authenticity score for a session
        
        Uses weighted average of recent results with temporal smoothing
        """
        try:
            if not session.analysis_history:
                return 50.0  # Neutral score
            
            # Get recent results (last 30 seconds)
            recent_results = session.get_recent_results(seconds=30)
            
            if not recent_results:
                return 50.0
            
            # Calculate weighted scores
            video_scores = [r["video_score"] for r in recent_results if "video_score" in r]
            audio_scores = [r["audio_score"] for r in recent_results if "audio_score" in r]
            
            # Compute averages
            avg_video = np.mean(video_scores) if video_scores else 0.5
            avg_audio = np.mean(audio_scores) if audio_scores else 0.5
            
            # Apply temporal smoothing
            smoothed_video = self._apply_temporal_smoothing(session, avg_video, "video")
            smoothed_audio = self._apply_temporal_smoothing(session, avg_audio, "audio")
            
            # Calculate final authenticity score (0-100 scale)
            video_weight = 0.6
            audio_weight = 0.4
            
            final_score = (smoothed_video * video_weight + smoothed_audio * audio_weight) * 100
            
            # Apply confidence-based adjustment
            confidence = session.get_confidence_level()
            adjusted_score = final_score * confidence + 50.0 * (1 - confidence)
            
            return np.clip(adjusted_score, 0.0, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating authenticity score: {e}")
            return 50.0
    
    def _apply_temporal_smoothing(self, session: 'SessionData', current_score: float, 
                                modality: str) -> float:
        """
        Apply temporal smoothing to reduce score fluctuations
        """
        try:
            # Get previous smoothed score
            prev_key = f"prev_{modality}_score"
            prev_score = getattr(session, prev_key, current_score)
            
            # Apply exponential moving average
            alpha = 0.3  # Smoothing factor
            smoothed_score = alpha * current_score + (1 - alpha) * prev_score
            
            # Store for next iteration
            setattr(session, prev_key, smoothed_score)
            
            return smoothed_score
            
        except Exception as e:
            logger.error(f"Error in temporal smoothing: {e}")
            return current_score
    
    async def get_authenticity_score(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current authenticity score for a session
        """
        try:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            
            # Check if session is still active
            if session.is_expired():
                self._cleanup_session(session_id)
                return None
            
            auth_score = self._calculate_authenticity_score(session)
            
            # Get latest individual scores
            latest_result = session.get_latest_result()
            video_score = latest_result.get("video_score", 0.5) if latest_result else 0.5
            audio_score = latest_result.get("audio_score", 0.5) if latest_result else 0.5
            
            return {
                "session_id": session_id,
                "authenticity": auth_score,
                "video_score": video_score,
                "audio_score": audio_score,
                "timestamp": datetime.now().isoformat(),
                "confidence": session.get_confidence_level(),
                "sample_count": session.get_sample_count(),
                "session_duration": session.get_duration_seconds()
            }
            
        except Exception as e:
            logger.error(f"Error getting authenticity score for session {session_id}: {e}")
            return None
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of currently active session IDs
        """
        active_sessions = []
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)
            else:
                active_sessions.append(session_id)
        
        # Cleanup expired sessions
        for session_id in expired_sessions:
            self._cleanup_session(session_id)
        
        return active_sessions
    
    def _cleanup_session(self, session_id: str):
        """
        Clean up an expired session
        """
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Cleaned up expired session: {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
    
    async def _background_processor(self):
        """
        Background task for periodic processing and cleanup
        """
        while True:
            try:
                # Cleanup expired sessions every 60 seconds
                self.get_active_sessions()
                
                # Log session statistics
                active_count = len(self.sessions)
                if active_count > 0:
                    logger.info(f"Active sessions: {active_count}")
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in background processor: {e}")
                await asyncio.sleep(30)


class SessionData:
    """
    Stores data and analysis results for a single session
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.analysis_history = deque(maxlen=1000)  # Keep last 1000 results
        
        # Smoothing state
        self.prev_video_score = 0.5
        self.prev_audio_score = 0.5
        
        # Session statistics
        self.total_frames_processed = 0
        self.total_audio_chunks_processed = 0
    
    def update_last_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = datetime.now()
    
    def add_analysis_result(self, result: Dict[str, Any]):
        """Add a new analysis result to the history"""
        result["timestamp"] = datetime.now()
        self.analysis_history.append(result)
        
        # Update counters
        if "video_score" in result:
            self.total_frames_processed += 1
        if "audio_score" in result:
            self.total_audio_chunks_processed += 1
    
    def get_recent_results(self, seconds: int = 30) -> List[Dict[str, Any]]:
        """
        Get analysis results from the last N seconds
        """
        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        
        recent_results = []
        for result in reversed(self.analysis_history):
            if result["timestamp"] >= cutoff_time:
                recent_results.append(result)
            else:
                break
        
        return recent_results
    
    def get_latest_result(self) -> Optional[Dict[str, Any]]:
        """Get the most recent analysis result"""
        return self.analysis_history[-1] if self.analysis_history else None
    
    def get_confidence_level(self) -> float:
        """
        Calculate confidence level based on sample count and consistency
        """
        try:
            sample_count = len(self.analysis_history)
            
            if sample_count == 0:
                return 0.0
            
            # Base confidence on sample count (more samples = higher confidence)
            count_confidence = min(sample_count / 50.0, 1.0)  # Max confidence at 50 samples
            
            # Calculate consistency (lower variance = higher confidence)
            recent_results = self.get_recent_results(30)
            if len(recent_results) < 2:
                return count_confidence * 0.5
            
            # Calculate score variance
            scores = []
            for result in recent_results:
                if "video_score" in result and "audio_score" in result:
                    combined = result["video_score"] * 0.6 + result["audio_score"] * 0.4
                    scores.append(combined)
            
            if len(scores) < 2:
                return count_confidence * 0.5
            
            variance = np.var(scores)
            consistency_confidence = 1.0 / (1.0 + variance * 10)  # Lower variance = higher confidence
            
            # Combine confidences
            final_confidence = (count_confidence * 0.6 + consistency_confidence * 0.4)
            
            return np.clip(final_confidence, 0.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def get_sample_count(self) -> int:
        """Get total number of samples processed"""
        return len(self.analysis_history)
    
    def get_duration_seconds(self) -> float:
        """Get session duration in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """
        Check if the session has expired (no activity for timeout_minutes)
        """
        timeout = timedelta(minutes=timeout_minutes)
        return (datetime.now() - self.last_activity) > timeout
