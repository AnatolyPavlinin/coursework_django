from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.core.exceptions import ValidationError



class Recipient(models.Model):
    """Модель получателя рассылки"""
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=150, verbose_name="Ф.И.О")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    def __str__(self):
        return f"{self.full_name} <{self.email}>" if self.full_name else self.email

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"


class Message(models.Model):
    """Модель сообщения"""
    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body_text = models.TextField(verbose_name="Текст сообщения")

    def __str__(self):
        preview = self.body_text[:50]
        return f"{self.subject} | {preview}..."

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"


class SendAttempt(models.Model):
    """Попытка рассылки"""
    STATUS_SUCCESS = 'Успешно'
    STATUS_FAILURE = 'Не успешно'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAILURE, 'Не успешно'),
    ]

    attempt_datetime = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Статус")
    server_response = models.TextField(blank=True, verbose_name="Ответ почтового сервера")

    campaign = models.ForeignKey(
        'Campaign',
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name="Рассылка"
    )

    def __str__(self):
        return f"Попытка {self.status} от {self.attempt_datetime}"

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"


class Campaign(models.Model):
    """Модель для управления рассылками."""

    STATUS_CREATED = 'Создана'
    STATUS_LAUNCHED = 'Запущена'
    STATUS_COMPLETED = 'Завершена'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_LAUNCHED, 'Запущена'),
        (STATUS_COMPLETED, 'Завершена'),
    ]

    first_send_datetime = models.DateTimeField(
        verbose_name="Дата и время первой отправки",
        null=True,
        blank=True,
        help_text="Будет заполнено автоматически при первой отправке."
    )
    end_datetime = models.DateTimeField(verbose_name="Дата и время окончания отправки")
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default=STATUS_CREATED,verbose_name="Статус")
    message = models.ForeignKey(Message,on_delete=models.PROTECT,verbose_name="Сообщение")
    recipients = models.ManyToManyField(Recipient,verbose_name="Получатели")

    def __str__(self):
        return f"Рассылка #{self.pk} - {self.status}"

    def send(self):
        """Метод для запуска рассылки."""

        if timezone.now() < self.first_send_datetime:
            raise ValidationError("Рассылку нельзя запустить раньше запланированного времени.")

        if self.status not in [self.STATUS_CREATED, self.STATUS_LAUNCHED]:
            raise ValueError(f"Нельзя отправить рассылку со статусом '{self.status}'")

        # Обновляем статус и дату первой отправки только если это первый запуск
        if self.first_send_datetime is None:
            self.first_send_datetime = timezone.now()
            self.status = self.STATUS_LAUNCHED
            self.save(update_fields=['first_send_datetime', 'status'])

        subject = self.message.subject
        body = self.message.body_text
        recipient_list = list(self.recipients.values_list('email', flat=True))

        #  пустой список для накопления объектов попыток
        attempts_to_create = []

        for recipient_email in recipient_list:
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=None,
                    recipient_list=[recipient_email],
                    fail_silently=False,
                )

                attempt = SendAttempt(
                    campaign=self,
                    status=SendAttempt.STATUS_SUCCESS,
                    server_response=f'Письмо отправлено на {recipient_email}'
                )
                attempts_to_create.append(attempt)

            except Exception as e:

                attempt = SendAttempt(
                    campaign=self,
                    status=SendAttempt.STATUS_FAILURE,
                    server_response=str(e)
                )
                attempts_to_create.append(attempt)

        if attempts_to_create:
            SendAttempt.objects.bulk_create(attempts_to_create)

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
