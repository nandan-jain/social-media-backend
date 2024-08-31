from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.timezone import now

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from core.models.request import Request
from core.filters import SearchFilter
from core.serializers.requests import UserSerializer,RequestActionSerializer, RequestListSerializer


class UsersListAPIView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]    
    filter_backends = [SearchFilter]

    def get_queryset(self):
        User = get_user_model() 
        current_user = self.request.user
        # Exclude users who are in the 'admin' group and the current user
        return User.objects.exclude(is_superuser=True).exclude(id=current_user.id)
    

class RequestViewSet(viewsets.ModelViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestActionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Send a request"""
        request_time_key = f"user_{request.user.id}_requests"
        current_time = now()

        # Check request rate limiting
        if self._has_exceeded_request_limit(request_time_key, current_time):
            return Response(
                {'error': 'You have exceeded the limit of 3 requests per minute.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        request.data['from_user'] = request.user.id
        request.data['status'] = 'sent'
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not self._is_valid_request(serializer):
                return Response({'error': self.error_message}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            self._update_request_timestamps(request_time_key, current_time)
            return Response({"data": serializer.data, "message": "Request Sent"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _has_exceeded_request_limit(self, request_time_key, current_time):
        """Check if the user has exceeded the request limit."""
        minute_ago = current_time - timedelta(minutes=1)
        timestamps = cache.get(request_time_key, [])

        # Filter out timestamps older than a minute
        timestamps = [t for t in timestamps if t > minute_ago]

        # Update the cache with filtered timestamps
        cache.set(request_time_key, timestamps, timeout=60)

        return len(timestamps) >= 3

    def _is_valid_request(self, serializer):
        """Validate if the request is legitimate and meets all criteria."""
        from_user = serializer.validated_data['from_user']
        to_user = serializer.validated_data['to_user']

        if from_user.id == to_user.id:
            self.error_message = 'You cannot send a request to yourself.'
            return False

        if Request.objects.filter(from_user=from_user, to_user=to_user).exclude(status='rejected').exists():
            self.error_message = 'A request to this user already exists and is not rejected.'
            return False

        if Request.objects.filter(from_user=to_user, to_user=from_user).exclude(status='rejected').exists():
            self.error_message = 'A request is already received from this user or you are already friends.'
            return False

        return True

    def _update_request_timestamps(self, request_time_key, current_time):
        """Update request timestamps in the cache."""
        timestamps = cache.get(request_time_key, [])
        timestamps.append(current_time)
        cache.set(request_time_key, timestamps, timeout=60)


    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Ensure that the 'status' field is provided
        new_status = request.data.get('status')
        if new_status is None:
            return Response({'error': 'Status field is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Prevent updating the status to 'sent'
        if new_status == 'sent':
            return Response({'error': 'Invalid Status'}, status=status.HTTP_400_BAD_REQUEST)

        if instance.to_user != request.user:
            return Response({'error': 'You do not have permission to update this request'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)
    

class FriendsListAPIView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]    

    def get_queryset(self):
        User = get_user_model()
        current_user = self.request.user

        # Get users who have accepted requests from the current user
        user_accepted_my_requests = Request.objects.filter(
            from_user=current_user, 
            status="accepted"
        ).values_list('to_user', flat=True).distinct()

        # Get users who the current user has accepted requests from
        my_accepted_user_requests = Request.objects.filter(
            to_user=current_user, 
            status="accepted"
        ).values_list('from_user', flat=True).distinct()

        # Combine both sets of user IDs
        friend_ids = set(user_accepted_my_requests) | set(my_accepted_user_requests)

        # Return User objects for the combined IDs, excluding admins and the current user
        return User.objects.filter(id__in=friend_ids).exclude(is_superuser=True).exclude(id=current_user.id)
    

class PendingRequestListAPIView(ListAPIView):
    serializer_class = RequestListSerializer
    permission_classes = [IsAuthenticated]    

    def get_queryset(self):
        return Request.objects.filter(to_user=self.request.user,status='sent')




    