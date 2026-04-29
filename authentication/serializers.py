from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
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


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UpdateLocationSerializer(serializers.Serializer):
    location = serializers.BooleanField(required=True)

    def save(self, **kwargs):
        user = self.context["request"].user
        set_user_location(user.id, self.validated_data["location"])
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from the old password."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
