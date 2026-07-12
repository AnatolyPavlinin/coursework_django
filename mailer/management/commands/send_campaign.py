from django.core.management.base import BaseCommand, CommandError
from mailer.models import Campaign
from mailer.tasks import task_send_campaign


class Command(BaseCommand):
    help = 'Запускает рассылку по ID из командной строки.'

    def add_arguments(self, parser):
        parser.add_argument('campaign_id', type=int, help='ID рассылки')

    def handle(self, *args, **options):
        campaign_id = options['campaign_id']

        try:
            campaign = Campaign.objects.get(pk=campaign_id)

            if campaign.status == 'Завершена':
                raise CommandError(f"Рассылка #{campaign_id} уже завершена.")

            campaign.update_status()
            campaign.first_send_datetime = campaign.first_send_datetime or self._get_now()
            campaign.save(update_fields=['first_send_datetime'])

            task_send_campaign.delay(campaign.id)

            self.stdout.write(
                self.style.SUCCESS(f"Успешно поставлено в очередь: Рассылка #{campaign_id}")
            )

        except Campaign.DoesNotExist:
            raise CommandError(f"Рассылка с ID {campaign_id} не найдена.")

    def _get_now(self):
        from django.utils import timezone
        return timezone.now()
