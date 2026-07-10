# mailer/admin.py

from django.contrib import admin, messages
from .models import Recipient, Message, Campaign, SendAttempt


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email')
    search_fields = ('full_name', 'email')
    list_filter = ('comment',)

    def save_model(self, request, obj, form, change):
        """Вызывается при сохранении объекта в админке."""
        if not change:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'body_preview')
    search_fields = ('subject', 'body_text')

    def body_preview(self, obj):
        return obj.body_text[:70] + "..." if len(obj.body_text) > 70 else obj.body_text

    body_preview.short_description = 'Текст сообщения'


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'message', 'end_datetime', 'count_recipients')
    list_filter = ('status', 'end_datetime',)
    filter_horizontal = ('recipients',)
    readonly_fields = ('first_send_datetime',)
    actions = ['run_campaign']

    def save_model(self, request, obj, form, change):
        """Вызывается при сохранении объекта в админке."""
        if not change:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def count_recipients(self, obj):
        return obj.recipients.count()

    count_recipients.short_description = 'Кол-во получателей'

    def run_campaign(self, request, queryset):
        """Административный запуск рассылок."""
        for campaign in queryset:
            try:
                campaign.send()
                self.message_user(
                    request,
                    f"Рассылка #{campaign.pk} успешно запущена.",
                    level=messages.SUCCESS
                )
            except ValueError as e:
                self.message_user(request, str(e), level=messages.WARNING)

    run_campaign.short_description = "Запустить выбранные рассылки"
