"""
SessionManager - Session lifecycle management for SuperVoiceAgent

This module handles session creation, storage, updates, and cleanup
with optional Redis backing for persistence and high availability.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from super.core.voice.schema import CallMeta


class SessionData:
    """Session data container"""
    
    def __init__(
        self,
        session_id: str,
        transport: str,
        call_meta: CallMeta,
        agent_name: Optional[str] = None
    ):
        self.session_id = session_id
        self.transport = transport
        self.call_meta = call_meta
        self.agent_name = agent_name
        
        # Timestamps
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.last_activity = datetime.now()
        
        # State
        self.state = "created"  # created, active, recording, transferring, ended
        self.recording = False
        self.recording_target = None
        
        # Additional data
        self.custom_data = {}
        self.agent_config = None
        
        # Statistics
        self.total_frames_in = 0
        self.total_frames_out = 0
        self.total_bytes_in = 0
        self.total_bytes_out = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'session_id': self.session_id,
            'transport': self.transport,
            'call_meta': {
                'call_id': self.call_meta.call_id,
                'direction': self.call_meta.direction,
                'from_number': self.call_meta.from_number,
                'to_number': self.call_meta.to_number,
                'sip_headers': self.call_meta.sip_headers,
                'custom_data': self.call_meta.custom_data,
                'agent_name': self.call_meta.agent_name
            },
            'agent_name': self.agent_name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'state': self.state,
            'recording': self.recording,
            'recording_target': self.recording_target,
            'custom_data': self.custom_data,
            'stats': {
                'total_frames_in': self.total_frames_in,
                'total_frames_out': self.total_frames_out,
                'total_bytes_in': self.total_bytes_in,
                'total_bytes_out': self.total_bytes_out
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create from dictionary"""
        call_meta_data = data['call_meta']
        call_meta = CallMeta(
            call_id=call_meta_data['call_id'],
            direction=call_meta_data['direction'],
            from_number=call_meta_data.get('from_number'),
            to_number=call_meta_data.get('to_number'),
            sip_headers=call_meta_data.get('sip_headers', {}),
            custom_data=call_meta_data.get('custom_data', {}),
            agent_name=call_meta_data.get('agent_name')
        )
        
        session = cls(
            session_id=data['session_id'],
            transport=data['transport'],
            call_meta=call_meta,
            agent_name=data.get('agent_name')
        )
        
        # Restore timestamps
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.updated_at = datetime.fromisoformat(data['updated_at'])
        session.last_activity = datetime.fromisoformat(data['last_activity'])
        
        # Restore state
        session.state = data.get('state', 'created')
        session.recording = data.get('recording', False)
        session.recording_target = data.get('recording_target')
        session.custom_data = data.get('custom_data', {})
        
        # Restore stats
        stats = data.get('stats', {})
        session.total_frames_in = stats.get('total_frames_in', 0)
        session.total_frames_out = stats.get('total_frames_out', 0)
        session.total_bytes_in = stats.get('total_bytes_in', 0)
        session.total_bytes_out = stats.get('total_bytes_out', 0)
        
        return session
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
        self.updated_at = datetime.now()


class SessionManager:
    """Session lifecycle manager with TTL and optional Redis backing"""
    
    def __init__(
        self,
        session_ttl_minutes: int = 60,
        cleanup_interval_seconds: int = 300,
        redis_client=None,
        logger: Optional[logging.Logger] = None
    ):
        self.session_ttl = timedelta(minutes=session_ttl_minutes)
        self.cleanup_interval = cleanup_interval_seconds
        self.redis_client = redis_client
        self.logger = logger or logging.getLogger(__name__)
        
        # In-memory session storage
        self._sessions: Dict[str, SessionData] = {}
        
        # Background tasks
        self._cleanup_task = None
        self._running = False
        
        self.logger.info("SessionManager initialized")
    
    async def start(self) -> bool:
        """Start the session manager"""
        try:
            self._running = True
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            
            self.logger.info("SessionManager started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start SessionManager: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the session manager"""
        try:
            self._running = False
            
            # Cancel cleanup task
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Optionally persist sessions to Redis before shutdown
            if self.redis_client:
                await self._persist_all_sessions()
            
            self.logger.info("SessionManager stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping SessionManager: {e}")
            return False
    
    async def create_session(
        self,
        session_id: str,
        transport: str,
        call_meta: CallMeta,
        agent_name: Optional[str] = None
    ) -> bool:
        """Create a new session"""
        try:
            if session_id in self._sessions:
                self.logger.warning(f"Session already exists: {session_id}")
                return False
            
            session_data = SessionData(
                session_id=session_id,
                transport=transport,
                call_meta=call_meta,
                agent_name=agent_name
            )
            
            self._sessions[session_id] = session_data
            
            # Persist to Redis if available
            if self.redis_client:
                await self._persist_session(session_data)
            
            self.logger.info(f"Created session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create session {session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        try:
            # Check in-memory first
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.update_activity()
                return session.to_dict()
            
            # Try to load from Redis
            if self.redis_client:
                session_data = await self._load_session_from_redis(session_id)
                if session_data:
                    self._sessions[session_id] = session_data
                    return session_data.to_dict()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update session data"""
        try:
            if session_id not in self._sessions:
                # Try to load from Redis first
                if self.redis_client:
                    session_data = await self._load_session_from_redis(session_id)
                    if session_data:
                        self._sessions[session_id] = session_data
                    else:
                        self.logger.warning(f"Session not found for update: {session_id}")
                        return False
                else:
                    self.logger.warning(f"Session not found for update: {session_id}")
                    return False
            
            session = self._sessions[session_id]
            
            # Update fields
            for key, value in updates.items():
                if key == 'state':
                    session.state = value
                elif key == 'recording':
                    session.recording = value
                elif key == 'recording_target':
                    session.recording_target = value
                elif key == 'agent_name':
                    session.agent_name = value
                elif key == 'agent_config':
                    session.agent_config = value
                elif key in ['custom_data']:
                    if isinstance(value, dict):
                        session.custom_data.update(value)
                    else:
                        session.custom_data[key] = value
            
            session.update_activity()
            
            # Persist to Redis
            if self.redis_client:
                await self._persist_session(session)
            
            self.logger.debug(f"Updated session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    async def remove_session(self, session_id: str) -> bool:
        """Remove a session"""
        try:
            # Remove from memory
            if session_id in self._sessions:
                del self._sessions[session_id]
            
            # Remove from Redis
            if self.redis_client:
                await self._remove_session_from_redis(session_id)
            
            self.logger.info(f"Removed session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove session {session_id}: {e}")
            return False
    
    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        try:
            active_sessions = []
            
            # Check in-memory sessions
            for session_id, session in self._sessions.items():
                if session.state not in ['ended', 'error']:
                    active_sessions.append(session_id)
            
            # If using Redis, also check for sessions not in memory
            if self.redis_client:
                redis_sessions = await self._get_redis_session_ids()
                for session_id in redis_sessions:
                    if session_id not in active_sessions:
                        # Load and check state
                        session_data = await self._load_session_from_redis(session_id)
                        if session_data and session_data.state not in ['ended', 'error']:
                            active_sessions.append(session_id)
            
            return active_sessions
            
        except Exception as e:
            self.logger.error(f"Failed to get active sessions: {e}")
            return []
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            total_sessions = len(self._sessions)
            active_sessions = await self.get_active_sessions()
            
            # Transport breakdown
            transport_counts = {}
            state_counts = {}
            
            for session in self._sessions.values():
                transport = session.transport
                state = session.state
                
                transport_counts[transport] = transport_counts.get(transport, 0) + 1
                state_counts[state] = state_counts.get(state, 0) + 1
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': len(active_sessions),
                'transport_breakdown': transport_counts,
                'state_breakdown': state_counts,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get session stats: {e}")
            return {}
    
    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self._running:
                    break
                
                expired_sessions = []
                current_time = datetime.now()
                
                for session_id, session in self._sessions.items():
                    # Check if session is expired
                    if current_time - session.last_activity > self.session_ttl:
                        expired_sessions.append(session_id)
                
                # Remove expired sessions
                for session_id in expired_sessions:
                    await self.remove_session(session_id)
                    self.logger.info(f"Cleaned up expired session: {session_id}")
                
                if expired_sessions:
                    self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in session cleanup: {e}")
    
    async def _persist_session(self, session: SessionData):
        """Persist session to Redis"""
        if not self.redis_client:
            return
        
        try:
            key = f"session:{session.session_id}"
            data = json.dumps(session.to_dict())
            
            # Set with TTL
            ttl_seconds = int(self.session_ttl.total_seconds())
            await self.redis_client.setex(key, ttl_seconds, data)
            
        except Exception as e:
            self.logger.error(f"Failed to persist session to Redis: {e}")
    
    async def _load_session_from_redis(self, session_id: str) -> Optional[SessionData]:
        """Load session from Redis"""
        if not self.redis_client:
            return None
        
        try:
            key = f"session:{session_id}"
            data = await self.redis_client.get(key)
            
            if data:
                session_dict = json.loads(data)
                return SessionData.from_dict(session_dict)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load session from Redis: {e}")
            return None
    
    async def _remove_session_from_redis(self, session_id: str):
        """Remove session from Redis"""
        if not self.redis_client:
            return
        
        try:
            key = f"session:{session_id}"
            await self.redis_client.delete(key)
            
        except Exception as e:
            self.logger.error(f"Failed to remove session from Redis: {e}")
    
    async def _get_redis_session_ids(self) -> List[str]:
        """Get all session IDs from Redis"""
        if not self.redis_client:
            return []
        
        try:
            keys = await self.redis_client.keys("session:*")
            session_ids = [key.decode().split(":", 1)[1] for key in keys]
            return session_ids
            
        except Exception as e:
            self.logger.error(f"Failed to get Redis session IDs: {e}")
            return []
    
    async def _persist_all_sessions(self):
        """Persist all in-memory sessions to Redis"""
        if not self.redis_client:
            return
        
        try:
            for session in self._sessions.values():
                await self._persist_session(session)
            
            self.logger.info(f"Persisted {len(self._sessions)} sessions to Redis")
            
        except Exception as e:
            self.logger.error(f"Failed to persist all sessions: {e}")
