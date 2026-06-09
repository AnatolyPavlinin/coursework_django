from django.contrib import admin
from .models import Recipient

@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email')
    search_fields = ('full_name', 'email')
    list_filter = ('comment',)