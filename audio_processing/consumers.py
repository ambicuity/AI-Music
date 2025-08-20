import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import RealtimeSession, AudioVisualization
from .audio_analyzer import AudioAnalyzer


class AudioProcessingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time audio processing"""
    
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Join user-specific group
        self.group_name = f"audio_processing_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection.established',
            'message': 'Audio processing WebSocket connected'
        }))
    
    async def disconnect(self, close_code):
        # Leave group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        
        # Deactivate any active sessions
        if hasattr(self, 'session'):
            await self.deactivate_session(self.session.id)
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'start_session':
                await self.start_processing_session(data)
            elif message_type == 'stop_session':
                await self.stop_processing_session(data)
            elif message_type == 'audio_data':
                await self.process_audio_data(data)
            elif message_type == 'update_config':
                await self.update_session_config(data)
            else:
                await self.send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON data")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")
    
    async def start_processing_session(self, data):
        """Start a new real-time processing session"""
        processing_type = data.get('processing_type', 'spectrum')
        session_id = data.get('session_id')
        
        if not session_id:
            await self.send_error("session_id required")
            return
        
        # Get or create session
        session = await self.get_or_create_session(session_id, processing_type)
        if session:
            self.session = session
            
            # Update session with channel name
            await self.update_session_channel(session.id, self.channel_name)
            
            # Send confirmation
            await self.send(text_data=json.dumps({
                'type': 'session.started',
                'session_id': session.session_id,
                'processing_type': session.processing_type
            }))
            
            # Start sending simulated data
            asyncio.create_task(self.send_realtime_data())
        else:
            await self.send_error("Failed to create session")
    
    async def stop_processing_session(self, data):
        """Stop the current processing session"""
        if hasattr(self, 'session'):
            await self.deactivate_session(self.session.id)
            
            await self.send(text_data=json.dumps({
                'type': 'session.stopped',
                'session_id': self.session.session_id
            }))
            
            delattr(self, 'session')
        else:
            await self.send_error("No active session to stop")
    
    async def process_audio_data(self, data):
        """Process incoming audio data"""
        if not hasattr(self, 'session'):
            await self.send_error("No active session")
            return
        
        # Simulate processing audio data
        audio_data = data.get('audio_data', '')  # Base64 encoded audio
        config = data.get('config', {})
        
        # In a real implementation, this would process the actual audio
        processed_data = AudioAnalyzer.process_realtime_audio(
            audio_data.encode() if audio_data else b'', 
            config
        )
        
        # Add timestamp
        from django.utils import timezone
        processed_data['timestamp'] = timezone.now().isoformat()
        
        # Send processed data back
        await self.send(text_data=json.dumps({
            'type': 'audio.processed',
            'session_id': self.session.session_id,
            'data': processed_data
        }))
        
        # Optionally save visualization data
        if self.session.processing_type == 'visualization':
            await self.save_visualization_data(processed_data)
    
    async def update_session_config(self, data):
        """Update session configuration"""
        if not hasattr(self, 'session'):
            await self.send_error("No active session")
            return
        
        config = data.get('config', {})
        
        # Update session (in a real implementation, would save to DB)
        self.session_config = config
        
        await self.send(text_data=json.dumps({
            'type': 'config.updated',
            'session_id': self.session.session_id,
            'config': config
        }))
    
    async def send_realtime_data(self):
        """Send simulated real-time data (for demo purposes)"""
        if not hasattr(self, 'session'):
            return
        
        while hasattr(self, 'session') and self.session:
            try:
                # Check if session is still active
                session = await self.get_session(self.session.id)
                if not session or not session.is_active:
                    break
                
                # Generate simulated data based on processing type
                if session.processing_type == 'spectrum':
                    data = {
                        'frequencies': [
                            __import__('random').uniform(0, 1) for _ in range(32)
                        ],
                        'peak_freq': __import__('random').uniform(100, 8000)
                    }
                elif session.processing_type == 'beat':
                    data = {
                        'beat_detected': __import__('random').choice([True, False]),
                        'bpm': __import__('random').uniform(80, 160)
                    }
                else:
                    data = {'type': 'generic', 'value': __import__('random').uniform(0, 1)}
                
                await self.send(text_data=json.dumps({
                    'type': 'realtime.data',
                    'session_id': session.session_id,
                    'data': data,
                    'timestamp': __import__('django.utils.timezone').now().isoformat()
                }))
                
                # Wait before sending next data point
                await asyncio.sleep(0.1)  # 10 FPS
                
            except Exception as e:
                print(f"Error sending realtime data: {e}")
                break
    
    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    # Database operations (async)
    @database_sync_to_async
    def get_or_create_session(self, session_id, processing_type):
        try:
            session, created = RealtimeSession.objects.get_or_create(
                user=self.user,
                session_id=session_id,
                defaults={
                    'processing_type': processing_type,
                    'is_active': True
                }
            )
            if not created:
                session.is_active = True
                session.processing_type = processing_type
                session.save()
            return session
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
    
    @database_sync_to_async
    def get_session(self, session_id):
        try:
            return RealtimeSession.objects.get(id=session_id)
        except RealtimeSession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def update_session_channel(self, session_id, channel_name):
        try:
            session = RealtimeSession.objects.get(id=session_id)
            session.channel_name = channel_name
            session.save()
        except RealtimeSession.DoesNotExist:
            pass
    
    @database_sync_to_async
    def deactivate_session(self, session_id):
        try:
            session = RealtimeSession.objects.get(id=session_id)
            session.is_active = False
            session.save()
        except RealtimeSession.DoesNotExist:
            pass
    
    @database_sync_to_async
    def save_visualization_data(self, data):
        try:
            AudioVisualization.objects.create(
                user=self.user,
                session_id=self.session.session_id,
                frequency_data=data.get('spectrum', []),
                amplitude_data=data.get('amplitude', []),
                beat_data=data.get('beats', [])
            )
        except Exception as e:
            print(f"Error saving visualization data: {e}")
    
    # Channel layer message handlers
    async def processing_start(self, event):
        """Handle processing start message from views"""
        await self.send(text_data=json.dumps({
            'type': 'processing.started',
            'session_id': event['session_id'],
            'processing_type': event['processing_type']
        }))
    
    async def processing_stop(self, event):
        """Handle processing stop message from views"""
        await self.send(text_data=json.dumps({
            'type': 'processing.stopped',
            'session_id': event['session_id']
        }))