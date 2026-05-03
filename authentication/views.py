from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import get_user_location, set_user_location
from .serializers import (
    ChangePasswordSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UpdateLocationSerializer,
)


def _build_auth_response(user):
    """Create the shared auth payload returned by login/register providers."""
    refresh = RefreshToken.for_user(user)
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "location": get_user_location(user.id),
        },
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
    }


def _unique_google_username(email):
    """Generate a valid unique Django username from a Google account email."""
    base_username = email.split("@", 1)[0].strip() or "google_user"
    base_username = "".join(
        char if char.isalnum() or char in ("_", ".", "-") else "_"
        for char in base_username
    )[:120]

    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        suffix = f"_{counter}"
        username = f"{base_username[:150 - len(suffix)]}{suffix}"
        counter += 1

    return username


@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(_build_auth_response(user), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = authenticate(
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )
    if not user:
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return Response(_build_auth_response(user), status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def google_login(request):
    serializer = GoogleLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        return Response(
            {"error": "Google login is not configured on the server."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        token_info = google_id_token.verify_oauth2_token(
            serializer.validated_data["id_token"],
            google_requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID,
        )
    except ValueError:
        return Response(
            {"error": "Invalid Google sign-in token."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    email = (token_info.get("email") or "").strip().lower()
    if not email or not token_info.get("email_verified"):
        return Response(
            {"error": "Google account email must be verified."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Link Google login to an existing email account when possible.
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = User(
            username=_unique_google_username(email),
            email=email,
            first_name=(token_info.get("given_name") or "")[:150],
            last_name=(token_info.get("family_name") or "")[:150],
        )
        user.set_unusable_password()
        user.save()
        set_user_location(user.id, False)

    return Response(_build_auth_response(user), status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    serializer = LogoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        token = RefreshToken(serializer.validated_data["refresh"])
        token.blacklist()
    except TokenError:
        return Response(
            {"error": "Invalid or expired refresh token."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_location(request):
    serializer = UpdateLocationSerializer(
        data=request.data,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    return Response(
        {
            "message": "Location updated successfully.",
            "location": get_user_location(user.id),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {"message": "Password changed successfully."},
        status=status.HTTP_200_OK,
    )
