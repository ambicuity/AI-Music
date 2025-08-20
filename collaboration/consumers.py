import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from .models import CollaborativeSession, SessionParticipant, CompositionChange, RealTimeEvent


class CollaborationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time collaborative composition"""
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.session_group_name = f'collaboration_{self.session_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated and has access to session
        if not self.user.is_authenticated:
            await self.close()
            return
            
        try:
            self.session = await self.get_session()
            self.participant = await self.get_or_create_participant()
            
            # Join session group
            await self.channel_layer.group_add(
                self.session_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Mark user as online and send join event
            await self.update_participant_status(True)
            await self.broadcast_user_event('user_joined', {
                'user': {
                    'id': self.user.id,
                    'username': self.user.username,
                    'permission_level': self.participant.permission_level
                }
            })
            
            # Send current session state to newly connected user
            await self.send_session_state()
            
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'participant'):
            # Mark user as offline and send leave event
            await self.update_participant_status(False)
            await self.broadcast_user_event('user_left', {
                'user': {
                    'id': self.user.id,
                    'username': self.user.username
                }
            })
        
        if hasattr(self, 'session_group_name'):
            # Leave session group
            await self.channel_layer.group_discard(
                self.session_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'composition_change':
                await self.handle_composition_change(data)
            elif message_type == 'comment':
                await self.handle_comment(data)
            elif message_type == 'playback_sync':
                await self.handle_playback_sync(data)
            elif message_type == 'cursor_position':
                await self.handle_cursor_position(data)
            elif message_type == 'heartbeat':
                await self.handle_heartbeat(data)
            else:
                print(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            print("Invalid JSON received")
        except Exception as e:
            print(f"Error handling message: {e}")
    
    async def handle_composition_change(self, data):
        """Handle composition changes from participants"""
        # Check permissions
        if self.participant.permission_level in ['view', 'comment']:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'You do not have permission to edit this composition'
            }))
            return
        
        change_data = data.get('change_data', {})
        change_type = data.get('change_type')
        
        # Record the change
        change = await self.record_change(change_type, change_data)
        
        # Update session composition data
        await self.update_session_composition(change_data)
        
        # Broadcast change to all participants
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'composition_change',
                'change': {
                    'id': change.id,
                    'type': change_type,
                    'data': change_data,
                    'user': {
                        'id': self.user.id,
                        'username': self.user.username
                    },
                    'timestamp': change.timestamp.isoformat()
                }
            }
        )
    
    async def handle_comment(self, data):
        """Handle comments from participants"""
        if self.participant.permission_level == 'view':
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'You do not have permission to comment'
            }))
            return
        
        comment_data = data.get('comment_data', {})
        content = comment_data.get('content', '')
        measure = comment_data.get('measure')
        beat = comment_data.get('beat')
        track_name = comment_data.get('track_name', '')
        
        # Create comment
        comment = await self.create_comment(content, measure, beat, track_name)
        
        # Broadcast comment to all participants
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'new_comment',
                'comment': {
                    'id': comment.id,
                    'content': content,
                    'user': {
                        'id': self.user.id,
                        'username': self.user.username
                    },
                    'measure': measure,
                    'beat': beat,
                    'track_name': track_name,
                    'timestamp': comment.created_at.isoformat()
                }
            }
        )
    
    async def handle_playback_sync(self, data):
        """Handle playback synchronization"""
        playback_data = data.get('playback_data', {})
        
        # Broadcast playback sync to all participants except sender
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'playback_sync',
                'playback_data': playback_data,
                'user': {
                    'id': self.user.id,
                    'username': self.user.username
                }
            }
        )
    
    async def handle_cursor_position(self, data):
        """Handle cursor position updates for showing where users are working"""
        cursor_data = data.get('cursor_data', {})
        
        # Broadcast cursor position to all participants except sender
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'cursor_update',
                'cursor_data': cursor_data,
                'user': {
                    'id': self.user.id,
                    'username': self.user.username
                }
            }
        )
    
    async def handle_heartbeat(self, data):
        """Handle heartbeat to keep connection alive and update last seen"""
        await self.update_participant_last_seen()
        
        # Send heartbeat response
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_response',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def composition_change(self, event):
        """Send composition change to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'composition_change',
            'change': event['change']
        }))
    
    async def new_comment(self, event):
        """Send new comment to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'comment',
            'comment': event['comment']
        }))
    
    async def playback_sync(self, event):
        """Send playback sync to WebSocket"""
        # Don't send back to sender
        if event.get('user', {}).get('id') != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'playback_sync',
                'playback_data': event['playback_data'],
                'user': event['user']
            }))
    
    async def cursor_update(self, event):
        """Send cursor update to WebSocket"""
        # Don't send back to sender
        if event.get('user', {}).get('id') != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'cursor_update',
                'cursor_data': event['cursor_data'],
                'user': event['user']
            }))
    
    async def user_joined(self, event):
        """Send user joined notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user': event['user']
        }))
    
    async def user_left(self, event):
        """Send user left notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user': event['user']
        }))
    
    async def send_session_state(self):
        """Send current session state to newly connected user"""
        session_data = await self.get_session_data()
        participants_data = await self.get_participants_data()
        
        await self.send(text_data=json.dumps({
            'type': 'session_state',
            'session': session_data,
            'participants': participants_data
        }))
    
    async def broadcast_user_event(self, event_type, event_data):
        """Broadcast user events to all participants"""
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': event_type,
                **event_data
            }
        )
        
        # Record event
        await self.record_event(event_type, event_data)
    
    # Database operations
    @database_sync_to_async
    def get_session(self):
        return CollaborativeSession.objects.get(
            id=self.session_id,
            status='active'
        )
    
    @database_sync_to_async
    def get_or_create_participant(self):
        participant, created = SessionParticipant.objects.get_or_create(
            session=self.session,
            user=self.user,
            defaults={'permission_level': 'edit'}
        )
        return participant
    
    @database_sync_to_async
    def update_participant_status(self, is_online):
        self.participant.is_online = is_online
        self.participant.last_seen = timezone.now()
        self.participant.save()
    
    @database_sync_to_async
    def update_participant_last_seen(self):
        self.participant.last_seen = timezone.now()
        self.participant.save()
    
    @database_sync_to_async
    def record_change(self, change_type, change_data):
        change = CompositionChange.objects.create(
            session=self.session,
            participant=self.participant,
            change_type=change_type,
            change_data=change_data
        )
        
        # Update participant contribution count
        self.participant.contributions_count += 1
        self.participant.save()
        
        return change
    
    @database_sync_to_async
    def update_session_composition(self, change_data):
        # Update the session's composition data
        # This would involve merging the changes into the existing composition
        # Implementation depends on your composition data structure
        
        self.session.version += 1
        self.session.last_activity = timezone.now()
        self.session.save()
    
    @database_sync_to_async
    def create_comment(self, content, measure, beat, track_name):
        from .models import SessionComment
        
        comment = SessionComment.objects.create(
            session=self.session,
            participant=self.participant,
            content=content,
            measure=measure,
            beat=beat,
            track_name=track_name
        )
        return comment
    
    @database_sync_to_async
    def record_event(self, event_type, event_data):
        RealTimeEvent.objects.create(
            session=self.session,
            event_type=event_type,
            user=self.user,
            event_data=event_data
        )
    
    @database_sync_to_async
    def get_session_data(self):
        return {
            'id': self.session.id,
            'title': self.session.title,
            'description': self.session.description,
            'creator': {
                'id': self.session.creator.id,
                'username': self.session.creator.username
            },
            'composition_data': self.session.composition_data,
            'version': self.session.version,
            'target_tempo': self.session.target_tempo,
            'key_signature': self.session.key_signature,
            'target_duration': self.session.target_duration
        }
    
    @database_sync_to_async
    def get_participants_data(self):
        participants = []
        for participant in self.session.participants.select_related('user').filter(is_online=True):
            participants.append({
                'id': participant.user.id,
                'username': participant.user.username,
                'permission_level': participant.permission_level,
                'is_online': participant.is_online,
                'contributions_count': participant.contributions_count
            })
        return participants