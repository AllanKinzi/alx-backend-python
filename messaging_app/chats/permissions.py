# from rest_framework import permissions

# class IsOwner(permissions.BasePermission):
#     def has_object_permission(self, request, view, obj):
#         return obj.sender == request.user or obj.receiver == request.user

from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Conversation

class IsParticipantOfConversation(BasePermission):
    """
    Allows access only to authenticated users who are participants of a conversation.
    """

    def has_permission(self, request, view):
        # Must be authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Object-level permission: applies to individual message/conversation objects
        if hasattr(obj, 'conversation'):
            # For Message objects
            return request.user in obj.conversation.participants.all()
        elif isinstance(obj, Conversation):
            return request.user in obj.participants.all()
        return False