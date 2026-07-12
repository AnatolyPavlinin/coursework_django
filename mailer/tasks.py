from __future__ import absolute_import
from celery import shared_task
from django.core.mail import send_mail
from .models import SendAttempt
from django.utils import timezone


@shared_task(bind=True)
def task_send_campaign(self, campaign_id):
    """Фоновая задача для отправки рассылки."""
    from .models import Campaign

    try:
        campaign = Campaign.objects.get(id=campaign_id)

        subject = campaign.message.subject
        body = campaign.message.body_text
        recipient_list = list(campaign.recipients.values_list('email', flat=True))

        attempts_to_create = []

        for email in recipient_list:
            try:
                send_mail(subject, body, None, [email], fail_silently=False)
                status = SendAttempt.STATUS_SUCCESS
                response = f'OK'
            except Exception as e:
                status = SendAttempt.STATUS_FAILURE
                response = str(e)

            attempts_to_create.append(
                SendAttempt(
                    campaign=campaign,
                    attempt_datetime=timezone.now(),
                    status=status,
                    server_response=response
                )
            )

        if attempts_to_create:
            SendAttempt.objects.bulk_create(attempts_to_create)

        return {'status': 'ok', 'sent': len(attempts_to_create)}

    except Campaign.DoesNotExist:
        return {'status': 'error', 'message': 'Campaign not found'}
