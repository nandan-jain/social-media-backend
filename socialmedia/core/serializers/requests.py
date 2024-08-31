from django.contrib.auth import get_user_model
from rest_framework import serializers
from core.models.request import Request

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email','name']


class RequestActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = "__all__"


class RequestListSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='from_user')
    class Meta:
        model = Request
        fields = ["id", "user"]


