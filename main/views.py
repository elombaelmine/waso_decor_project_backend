import os
import requests
import secrets
import random
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import GalleryItem, Inquiry, Testimonial, UserProfileOTP, ChatMessage
from .serializers import GalleryItemSerializer, InquirySerializer, TestimonialSerializer, ChatMessageSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class GalleryItemViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD for the Inspiration Gallery.
    Publicly viewable, but only editable by the Manager.
    """
    queryset = GalleryItem.objects.all()
    serializer_class = GalleryItemSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    
    # 1. Enforcement Guard: Anyone can READ, but only logged-in accounts can POST
    permission_classes = [IsAuthenticatedOrReadOnly]

    # 2. Identity Guard: Auto-inject the user's real account name securely on save
    def perform_create(self, serializer):
        # Extract full name or fallback to the clean account username string
        user = self.request.user
        full_name = f"{user.first_name} {user.last_name}".strip()
        final_name = full_name if full_name else user.username
        
        serializer.save(client_name=final_name)


class InquiryViewSet(viewsets.ModelViewSet):
    """
    Handles the Lead Qualification forms.
    Allows anyone to submit an inquiry (creating an account automatically),
    but restricts viewing/listing to authenticated users.
    """
    serializer_class = InquirySerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Inquiry.objects.all().order_by('-created_at')
        return Inquiry.objects.filter(user=self.request.user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        Intercepts the booking submission to automatically spin up a 
        secure client account if it doesn't exist yet.
        """
        data = request.data
        email = data.get('client_email')
        name = data.get('client_name')

        if not email or not name:
            return Response(
                {"error": "Client name and email are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Automate account detection/creation logic
        user_exists = User.objects.filter(username=email).exists()
        generated_password = None
        target_user = None

        if not user_exists:
            generated_password = secrets.token_urlsafe(8)  # Secure temp password
            target_user = User.objects.create_user(
                username=email,
                email=email,
                password=generated_password,
                first_name=name
            )
        else:
            target_user = User.objects.get(username=email)

        # 2. Process and save the Inquiry using your existing serializer logic
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            # Link the newly created or fetched user to this inquiry model
            serializer.save(user=target_user)
            
            # Formulate validation response object boundaries
            response_data = {
                "message": "Inquiry submitted successfully!",
                "inquiry": serializer.data,
                "account_created": not user_exists,
            }

            if generated_password:
                response_data["temporary_password"] = generated_password
                response_data["username"] = email

            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# ==============================================================================
# SECURE CUSTOMER ONBOARDING & ACTIVATION VIEWS (STANDALONE FUNCTIONS)
# ==============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])  # Ensures public signups can access this gate cleanly
def client_registration_view(request):
    data = request.data
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('fullName')
    
    if not email or not password or not full_name:
        return Response({"error": "Missing mandatory registration parameters."}, status=status.HTTP_400_BAD_REQUEST)

    # Prevent duplicate accounts
    if User.objects.filter(username=email).exists():
        return Response({"error": "An account with this email address already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
    # Build user as INACTIVE until they pass the OTP email check
    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=full_name,
        is_active=False 
    )
    
    # Save code to the database profile container
    otp_profile, created = UserProfileOTP.objects.get_or_create(user=user)
    generated_pin = otp_profile.generate_code()
    
    # Pull Brevo credentials directly from your .env
    brevo_api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("EMAIL_FROM", "eventportal0@gmail.com")

    # Fire the transactional activation email using direct Brevo HTTP API
    try:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": brevo_api_key,
            "content-type": "application/json"
        }
        
        payload = {
            "sender": {"name": "Waso Deco", "email": sender_email},
            "to": [{"email": email, "name": full_name}],
            "subject": "Activate Your Waso Deco Lookbook Portal",
            "textContent": f"Hello {full_name},\n\nThank you for registering. Your 6-digit one-time activation pin is: {generated_pin}\n\nThis code will expire in 15 minutes."
        }

        response = requests.post(url, json=payload, headers=headers)
        
        # Check if Brevo accepted the transaction successfully
        if response.status_code == 201 or response.status_code == 200:
            return Response({"message": "User initialized. Validation code dispatched."}, status=status.HTTP_201_CREATED)
        else:
            # If Brevo rejects it, print the exact reason to your console so you see it instantly!
            print(f"❌ Brevo API Error Context: {response.text}")
            return Response({"error": "Mail delivery agent rejected transaction setup."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        print(f"❌ Connection Exception: {str(e)}")
        return Response({"error": f"Failed to send verification email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_view(request):
    data = request.data
    email = data.get('email')
    inserted_code = data.get('verificationCode')
    
    try:
        user = User.objects.get(username=email)
        otp_profile = user.otp_profile
        
        if otp_profile.otp_code == inserted_code and otp_profile.is_valid():
            # Activate account! Now they can log in via JWT
            user.is_active = True
            user.save()
            
            otp_profile.delete() # Clean up the code from the database
            return Response({"message": "Profile verified successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid or expired activation code string."}, status=status.HTTP_400_BAD_REQUEST)
            
    except User.DoesNotExist:
        return Response({"error": "Account target parameter not identified."}, status=status.HTTP_404_NOT_FOUND)
    
class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    Handles fetching and sending messages within the Design Room Chat.
    Enforces data ownership: clients are limited to their own records,
    while staff can access and manage conversations per client room.
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # If staff, they can filter messages for a specific client room using ?client_id=X
        if user.is_staff:
            target_client_id = self.request.query_params.get('client_id')
            if target_client_id:
                return ChatMessage.objects.filter(user_id=target_client_id).order_by('created_at')
            return ChatMessage.objects.all().order_by('created_at')
        
        # Regular clients can only see their own chat messages (Strict Ownership Filtering)
        return ChatMessage.objects.filter(user=user).order_by('created_at')

    def perform_create(self, serializer):
        user = self.request.user
        
        # If staff is writing, attach the message to the client room they are currently viewing
        if user.is_staff:
            target_client_id = self.request.data.get('client_id')
            if target_client_id:
                try:
                    target_user = User.objects.get(id=target_client_id)
                    serializer.save(
                        user=target_user,
                        sender_name=f"Manager ({user.first_name or user.username})",
                        is_from_staff=True
                    )
                    return
                except User.DoesNotExist:
                    pass

        # If a regular client is writing, link it directly to their account
        serializer.save(
            user=user,
            sender_name=user.first_name or user.username,
            is_from_staff=False
        )