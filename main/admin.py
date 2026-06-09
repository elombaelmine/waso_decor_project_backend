from django.contrib import admin
from django.utils.html import format_html
from .models import GalleryItem, Inquiry, Testimonial, UserProfileOTP, ChatMessage

# Clear administrative branding text strings
admin.site.site_header = "Waso Deco Admin Dashboard"
admin.site.site_title = "Waso Deco Portal"
admin.site.index_title = "Management Panel"

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'event_date', 'status_badge', 'guest_count', 'budget_estimate', 'town')
    list_filter = ('status', 'event_date', 'town')
    list_editable = ()
    search_fields = ('client_name', 'client_email', 'venue_name', 'town')
    ordering = ('-created_at',)

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        status_class = obj.status.lower()
        return format_html(
            '<span class="waso-status-pill waso-status-{}">{}</span>',
            status_class,
            obj.get_status_display(),
        )

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'visibility_badge')
    list_filter = ('is_visible',)
    search_fields = ('client_name', 'content')
    list_editable = ()

    @admin.display(description="Visible", ordering="is_visible")
    def visibility_badge(self, obj):
        label = "Visible" if obj.is_visible else "Hidden"
        badge_class = "yes" if obj.is_visible else "no"
        return format_html(
            '<span class="waso-boolean-pill waso-boolean-{}">{}</span>',
            badge_class,
            label,
        )

@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'primary_color', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('title', 'primary_color')
    ordering = ('-created_at',)

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
