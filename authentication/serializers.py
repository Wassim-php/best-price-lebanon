from django.contrib.auth.models import User
from rest_framework import serializers

from .models import set_user_location


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=True)
    location = serializers.BooleanField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "location"]

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        location = validated_data.pop("location")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        set_user_location(user.id, location)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
