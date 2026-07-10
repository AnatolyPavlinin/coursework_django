from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.urls import reverse


class CustomUser(AbstractUser):
    """Кастомная модель пользователя с ролью менеджера."""
    is_manager = models.BooleanField(
        default=False,
        verbose_name='Является менеджером'
    )

    def __str__(self):
        return self.email or self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'



class Recipient(models.Model):
    """Модель получателя рассылки"""
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=150, verbose_name="Ф.И.О")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipients',
        verbose_name='Владелец получателя'
    )

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

    start_time = models.DateTimeField(
        verbose_name="Дата и время начала отправки",
        help_text="Рассылка не начнется раньше этого времени."
    )

    end_time = models.DateTimeField(verbose_name="Дата и время окончания отправки")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name="Статус")

    message = models.ForeignKey(Message, on_delete=models.PROTECT, verbose_name="Сообщение")
    recipients = models.ManyToManyField(Recipient, verbose_name="Получатели")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='campaigns',
                              verbose_name='Владелец рассылки')

    first_send_datetime = models.DateTimeField(
        verbose_name="Дата и время первой отправки",
        null=True,
        blank=True,
        editable=False
    )

    def __str__(self):
        return f"Рассылка #{self.pk} - {self.status}"

    # --- ДОБАВЛЯЕМ ДИНАМИЧЕСКИЙ СТАТУС ---
    def update_status(self):
        now = timezone.now()

        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.STATUS_LAUNCHED
        else:
            new_status = self.STATUS_COMPLETED

        if self.status != new_status:
            self.status = new_status
            # Сохраняем только поле статуса, чтобы не сбивать дату первой отправки
            self.save(update_fields=['status'])

    def send(self):
        """Метод для запуска рассылки."""
        now = timezone.now()

        # Проверка окна отправки (валидация)
        if not (self.start_time <= now <= self.end_time):
            raise ValidationError("Отправка возможна только в период между датой начала и окончания.")

        if self.status == self.STATUS_COMPLETED:
            raise ValueError(f"Нельзя отправить завершенную рассылку.")

        updated_fields = []

        # Фиксируем момент первого старта
        if self.first_send_datetime is None:
            self.first_send_datetime = now
            updated_fields.append('first_send_datetime')

        if self.status != self.STATUS_LAUNCHED:
            self.status = self.STATUS_LAUNCHED
            updated_fields.append('status')

        if updated_fields:
            self.save(update_fields=updated_fields)

        subject = self.message.subject
        body = self.message.body_text
        recipient_list = list(self.recipients.values_list('email', flat=True))

        attempts_to_create = []
        for email in recipient_list:
            try:
                send_mail(subject, body, None, [email], fail_silently=False)
                attempts_to_create.append(
                    SendAttempt(campaign=self, status=SendAttempt.STATUS_SUCCESS, server_response=f'OK'))
            except Exception as e:
                attempts_to_create.append(
                    SendAttempt(campaign=self, status=SendAttempt.STATUS_FAILURE, server_response=str(e)))

        SendAttempt.objects.bulk_create(attempts_to_create)

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"