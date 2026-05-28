from rest_framework import serializers
from .models import GalleryItem, Inquiry, Testimonial
from datetime import date
from .models import ChatMessage

class GalleryItemSerializer(serializers.ModelSerializer):
    # This creates a custom way to handle the image field
    image = serializers.SerializerMethodField()

    class Meta:
        model = GalleryItem
        fields = '__all__'

    def get_image(self, obj):
        # Check if the image exists and return its full Cloudinary URL
        if obj.image:
            return obj.image.url
        return None

class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = '__all__'
        # Strict security guard: This field cannot be falsified by incoming payload data
        read_only_fields = ['client_name']

class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = '__all__'
        # Add this line right here to make user field optional for incoming frontend data
        read_only_fields = ['user']

    # BUSINESS RULE VALIDATION (Criterion 7) 
    def validate_event_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("The event date cannot be in the past.")
        return value

    def validate_guest_count(self, value):
        if value <= 0:
            raise serializers.ValidationError("Guest count must be at least 1.")
        return value
    

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'sender_name', 'message', 'is_from_staff', 'created_at']
        # These are set automatically by the backend server for security
        read_only_fields = ['id', 'user', 'sender_name', 'is_from_staff', 'created_at']