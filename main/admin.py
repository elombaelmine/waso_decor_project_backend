from django.contrib import admin
from .models import GalleryItem, Inquiry, Testimonial, UserProfileOTP, ChatMessage

# Clear administrative branding text strings
admin.site.site_header = "WASO DECO Admin Dashboard"
admin.site.site_title = "WASO DECO Portal"
admin.site.index_title = "Bespoke Management Panel"

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'event_date', 'status', 'guest_count')
    list_filter = ('status', 'event_date') 
    search_fields = ('client_name', 'venue_name')

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'is_visible')
    list_editable = ('is_visible',) 

admin.site.register(GalleryItem)

@admin.register(UserProfileOTP)
class UserProfileOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'created_at')
    search_fields = ('user__email', 'otp_code')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'sender_name', 'message_snippet', 'is_from_staff', 'created_at')
    list_filter = ('is_from_staff', 'created_at', 'user')
    search_fields = ('sender_name', 'message', 'user__username', 'user__email')
    ordering = ('-created_at',)

    def message_snippet(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_snippet.short_description = "Message Content"