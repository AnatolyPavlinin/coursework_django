from django.contrib import admin, messages
from .models import Recipient, Message, Campaign, SendAttempt
from .tasks import task_send_campaign
from django.core.exceptions import ValidationError
from django.utils import timezone


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
    list_display = ('id', 'status', 'message', 'end_time', 'count_recipients')
    list_filter = ('status', 'end_time',)
    filter_horizontal = ('recipients',)
    readonly_fields = ('start_time',)
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
                # 1. Проверяем бизнес-логику
                if not (campaign.start_time <= timezone.now() <= campaign.end_time):
                    raise ValidationError(f"Рассылка #{campaign.pk}: текущее время вне окна отправки.")

                if campaign.status == 'Завершена':
                    raise ValueError(f"Рассылка #{campaign.pk} уже завершена.")

                # 2. Обновляем статус рассылки
                now = timezone.now()
                updated_fields = []

                if campaign.first_send_datetime is None:
                    campaign.first_send_datetime = now
                    updated_fields.append('first_send_datetime')

                if campaign.status != 'Запущена':
                    campaign.status = 'Запущена'
                    updated_fields.append('status')

                if updated_fields:
                    campaign.save(update_fields=updated_fields)

                # 3. ОТДАЕМ ЗАДАЧУ CELERY
                task_send_campaign.delay(campaign.id)

                # 4. Сообщаем админу, что всё ок
                self.message_user(
                    request,
                    f"Рассылка #{campaign.pk} поставлена в очередь.",
                    level=messages.SUCCESS
                )

            except (ValidationError, ValueError) as e:

                self.message_user(request, str(e), level=messages.WARNING)
            except Exception as e:

                self.message_user(
                    request,
                    f"Произошла системная ошибка при постановке в очередь: {str(e)}",
                    level=messages.ERROR
                )

    run_campaign.short_description = "Запустить выбранные рассылки"
