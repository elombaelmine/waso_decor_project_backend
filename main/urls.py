from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GalleryItemViewSet, 
    InquiryViewSet, 
    TestimonialViewSet,
    ChatMessageViewSet,  # 1. Imported our new viewset
    client_registration_view,  
    verify_otp_view            
)

# Instantiating the DRF Default Router
router = DefaultRouter()
router.register(r'gallery', GalleryItemViewSet, basename='galleryitem')
router.register(r'inquiries', InquiryViewSet, basename='inquiry')
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')
router.register(r'chat', ChatMessageViewSet, basename='chat')  # 2. Registered the chat endpoint

urlpatterns = [
    # 1. Automated viewset paths
    path('', include(router.urls)),
    
    # 2. Match your folder names perfectly!
    path('auth/sign-up/', client_registration_view, name='client_sign_up'),
    path('auth/otp-verify/', verify_otp_view, name='verify_otp'),
]