from django.contrib import admin
from .models import Recipient, Message

@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email')
    search_fields = ('full_name', 'email')
    list_filter = ('comment',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'body_preview')
    search_fields = ('subject', 'body_text')

    def body_preview(self, obj):
        return obj.body_text[:70] + "..." if len(obj.body_text) > 70 else obj.body_text
    body_preview.short_description = 'Текст сообщения'
