from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer, 
    ConversationDetailSerializer,
    ConversationListSerializer,
    ConversationCreateSerializer,
    ConversationParticipantSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    MessageBulkSerializer,
    UserSerializer
)

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    
    Provides CRUD operations for conversations with proper permissions
    and filtering based on user participation.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['created_at']
    search_fields = ['participants__first_name', 'participants__last_name', 'participants__email']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return conversations where the current user is a participant.
        Optimizes queries with prefetch_related for better performance.
        """
        user = self.request.user
        return Conversation.objects.filter(
            participants=user
        ).prefetch_related(
            'participants',
            Prefetch(
                'messages',
                queryset=Message.objects.select_related('sender').order_by('-sent_at')
            )
        ).distinct()
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return ConversationCreateSerializer
        elif self.action == 'retrieve':
            return ConversationDetailSerializer
        elif self.action == 'list':
            return ConversationListSerializer
        elif self.action in ['add_participants', 'remove_participants']:
            return ConversationParticipantSerializer
        return ConversationSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new conversation with participants and optional initial message.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        
        # Return detailed conversation data
        response_serializer = ConversationDetailSerializer(
            conversation, 
            context={'request': request}
        )
        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a conversation with all messages.
        """
        conversation = self.get_object()
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        """
        List all conversations for the current user.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_participants(self, request, pk=None):
        """
        Add participants to an existing conversation.
        """
        conversation = self.get_object()
        serializer = ConversationParticipantSerializer(data=request.data)
        
        if serializer.is_valid():
            participant_ids = serializer.validated_data['participant_ids']
            participants = User.objects.filter(id__in=participant_ids)
            
            # Add new participants
            conversation.participants.add(*participants)
            
            # Return updated conversation
            response_serializer = ConversationDetailSerializer(
                conversation, 
                context={'request': request}
            )
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def remove_participants(self, request, pk=None):
        """
        Remove participants from an existing conversation.
        """
        conversation = self.get_object()
        serializer = ConversationParticipantSerializer(data=request.data)
        
        if serializer.is_valid():
            participant_ids = serializer.validated_data['participant_ids']
            
            # Prevent removing all participants
            if conversation.participants.count() - len(participant_ids) < 2:
                return Response(
                    {'error': 'A conversation must have at least 2 participants.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Prevent user from removing themselves
            if request.user.id in participant_ids:
                return Response(
                    {'error': 'You cannot remove yourself from the conversation.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            participants = User.objects.filter(id__in=participant_ids)
            conversation.participants.remove(*participants)
            
            # Return updated conversation
            response_serializer = ConversationDetailSerializer(
                conversation, 
                context={'request': request}
            )
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get all messages for a specific conversation with pagination.
        """
        conversation = self.get_object()
        messages = conversation.messages.select_related('sender').order_by('-sent_at')
        
        # Apply pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search_users(self, request):
        """
        Search for users to add to conversations.
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Query parameter "q" is required.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(username__icontains=query)
        ).exclude(id=request.user.id)[:10]  # Limit to 10 results
        
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages within conversations.
    
    Provides CRUD operations for messages with proper permissions
    ensuring users can only access messages from their conversations.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['conversation', 'sender', 'sent_at']
    search_fields = ['message_body', 'sender__first_name', 'sender__last_name']
    ordering_fields = ['sent_at']
    ordering = ['-sent_at']
    
    def get_queryset(self):
        """
        Return messages from conversations where the current user is a participant.
        """
        user = self.request.user
        user_conversations = Conversation.objects.filter(participants=user)
        
        return Message.objects.filter(
            conversation__in=user_conversations
        ).select_related('sender', 'conversation').order_by('-sent_at')
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return MessageCreateSerializer
        elif self.action == 'bulk_operations':
            return MessageBulkSerializer
        return MessageSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Send a new message to an existing conversation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        
        # Return the created message with full details
        response_serializer = MessageSerializer(message, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Update a message (only sender can update their own messages).
        """
        message = self.get_object()
        
        # Check if user is the sender
        if message.sender != request.user:
            return Response(
                {'error': 'You can only update your own messages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow updating message_body
        allowed_fields = {'message_body'}
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = self.get_serializer(message, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a message (only sender can delete their own messages).
        """
        message = self.get_object()
        
        # Check if user is the sender
        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """
        Perform bulk operations on messages (delete, mark as read, etc.).
        """
        serializer = MessageBulkSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            message_ids = serializer.validated_data['message_ids']
            action_type = serializer.validated_data['action']
            
            messages = Message.objects.filter(
                message_id__in=message_ids,
                conversation__participants=request.user
            )
            
            if action_type == 'delete':
                # Only allow deleting own messages
                own_messages = messages.filter(sender=request.user)
                deleted_count = own_messages.count()
                own_messages.delete()
                
                return Response({
                    'message': f'{deleted_count} messages deleted successfully.'
                })
            
            elif action_type == 'mark_read':
                # TODO: Implement read status tracking
                return Response({
                    'message': 'Read status updated successfully.',
                    'note': 'Read status tracking not yet implemented.'
                })
            
            return Response({'error': 'Invalid action.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_conversation(self, request):
        """
        Get messages filtered by conversation ID.
        """
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response(
                {'error': 'conversation_id parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify user is participant in the conversation
        conversation = get_object_or_404(
            Conversation,
            conversation_id=conversation_id,
            participants=request.user
        )
        
        messages = self.get_queryset().filter(conversation=conversation)
        page = self.paginate_queryset(messages)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent messages across all user's conversations.
        """
        limit = min(int(request.query_params.get('limit', 20)), 100)  # Max 100
        messages = self.get_queryset()[:limit]
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


# Additional utility views that might be helpful
class ConversationPermission(permissions.BasePermission):
    """
    Custom permission to ensure users can only access their own conversations.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is a participant in the conversation
        return obj.participants.filter(id=request.user.id).exists()


class MessagePermission(permissions.BasePermission):
    """
    Custom permission for message operations.
    """
    def has_object_permission(self, request, view, obj):
        # Users can read messages from their conversations
        if request.method in permissions.SAFE_METHODS:
            return obj.conversation.participants.filter(id=request.user.id).exists()
        
        # Only message sender can modify/delete
        return obj.sender == request.user


# You can add these custom permissions to your ViewSets:
# ConversationViewSet.permission_classes = [IsAuthenticated, ConversationPermission]
# MessageViewSet.permission_classes = [IsAuthenticated, MessagePermission]