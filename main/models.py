import secrets
import random
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User 
from django.utils import timezone
from cloudinary.models import CloudinaryField

class GalleryItem(models.Model):
    EVENT_TYPES = [
        ('WEDDING', 'Weddings'), 
        ('BIRTHDAY', 'Birthdays'), 
        ('CORPORATE', 'Corporate Events'), 
        ('MEETING', 'Meetings'), 
        ('BURIAL', 'Burial Ceremony'), 
        ('GENERAL', 'General Events'), 
    ]
    
    title = models.CharField(max_length=200)
    image = CloudinaryField('image') # Change ImageField to this for Cloudinary integration
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    primary_color = models.CharField(max_length=50) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.event_type}"

    
class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('BOOKED', 'Booked'),
    ]
    
    # Links the Inquiry to their User account (handled cleanly via Views/Serializers)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='inquiries')
    client_name = models.CharField(max_length=200)
    client_email = models.EmailField()
    event_date = models.DateField()
    venue_name = models.CharField(max_length=255)
    town = models.CharField(max_length=100, default="Yaoundé")  
    guest_count = models.IntegerField()
    budget_estimate = models.DecimalField(max_digits=10, decimal_places=2)
    color_palette = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inquiry"
        verbose_name_plural = "Inquiries"

    def __str__(self):
        return f"Inquiry from {self.client_name} for {self.event_date}"

    
class Testimonial(models.Model):
    client_name = models.CharField(max_length=100)
    content = models.TextField()
    is_visible = models.BooleanField(default=False) 

    def __str__(self):
        return self.client_name


class UserProfileOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="otp_profile")
    otp_code = models.CharField(max_length=6, default="")
    created_at = models.DateTimeField(auto_now=True) 
    
    def generate_code(self):
        """Generates a random secure 6-digit pin and saves it."""
        self.otp_code = f"{random.randint(100000, 999999)}"
        self.save()
        return self.otp_code

    def is_valid(self):
        """Validates that the code hasn't expired (15-minute window)."""
        return timezone.now() < self.created_at + timedelta(minutes=15)
    

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")
    sender_name = models.CharField(max_length=150)
    message = models.TextField()
    is_from_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {self.sender_name}: {self.message[:30]}"