from django.db import models

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
