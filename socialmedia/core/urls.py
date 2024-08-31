from django.urls import path, include
from core.views.authentication import SignupAPIView,LoginAPIView
from core.views.requests import UsersListAPIView, RequestViewSet, FriendsListAPIView,PendingRequestListAPIView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('request',RequestViewSet)

urlpatterns = [
    path('signup', SignupAPIView.as_view()),
    path('login', LoginAPIView.as_view()),
    path('users', UsersListAPIView.as_view()),
    path('friends', FriendsListAPIView.as_view()),
    path('requests/pending', PendingRequestListAPIView.as_view()),
    path('', include(router.urls)),
]
