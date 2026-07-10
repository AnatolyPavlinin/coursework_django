from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import redirect, reverse
from .models import Recipient, Message, Campaign
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError


User = get_user_model()


class ManagerDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Страница администратора/менеджера: управление пользователями сервиса."""
    model = User
    template_name = 'mailer/manager_dashboard.html'
    context_object_name = 'users_list'

    def test_func(self):
        """Проверка роли: доступ только для менеджеров."""
        return self.request.user.is_manager

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        users_qs = self.get_queryset()

        # Проверяем, есть ли статистика в кеше
        if 'manager_stats' not in context:
            stats = {
                'total': users_qs.count(),
                'active': users_qs.filter(is_active=True).count(),
                'blocked': users_qs.filter(is_active=False).count(),
                'managers': users_qs.filter(is_manager=True).count(),
            }
            # Сохраняем словарь статистики в кеш под ключом manager_dashboard_stats на 60 секунд
            cache.set('manager_dashboard_stats', stats, 60)
            context.update(stats)
        else:
            context.update(cache.get('manager_dashboard_stats'))

        return context

    def post(self, request, *args, **kwargs):
        """Обработка нажатия кнопок блокировки прямо из списка."""
        if not self.test_func():
            return redirect('main-page')

        user_id = request.POST.get('user_id')
        action = request.POST.get('action')

        try:
            target_user = User.objects.get(pk=user_id)

            # Менеджер не может заблокировать сам себя или другого менеджера
            if target_user == request.user or target_user.is_manager:
                messages.error(request, "Нельзя изменить права этого пользователя.")
                return redirect(reverse('mailer:manager-dashboard'))

            if action == 'block':
                target_user.is_active = False
                messages.success(request, f"Пользователь {target_user.email} заблокирован.")
            elif action == 'unblock':
                target_user.is_active = True
                messages.success(request, f"Пользователь {target_user.email} разблокирован.")

            target_user.save()

        except User.DoesNotExist:
            messages.error(request, "Пользователь не найден.")

        return redirect(reverse('mailer:manager-dashboard'))


class IsOwnerFilterMixin(UserPassesTestMixin):
    """
    Миксин для фильтрации объектов текущего пользователя.
    Наследники должны определить self.model.
    """

    def get_queryset(self):
        # Берем стандартный queryset от наследника и фильтруем его
        qs = super().get_queryset()

        # Если менеджер - показываем всё
        if self.request.user.is_manager:
            return qs

        # Для обычного пользователя - только его объекты
        return qs.filter(owner=self.request.user)

    def form_valid(self, form):
        """Автоматически присваиваем владельца при создании."""
        if not form.instance.owner_id:
            form.instance.owner = self.request.user
        return super().form_valid(form)

    def test_func(self):
        """Проверка для удаления/редактирования конкретного объекта."""
        obj = self.get_object()

        if self.request.user.is_manager:
            return True
        return obj.owner == self.request.user

class RecipientListView(ListView):
    model = Recipient
    template_name = 'mailer/recipient_list.html'
    context_object_name = 'recipients'

class RecipientCreateView(CreateView):
    model = Recipient
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailer/recipient_form.html'
    success_url = reverse_lazy('mailer:recipient-list')

class RecipientUpdateView(UpdateView):
    model = Recipient
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailer/recipient_form.html'
    success_url = reverse_lazy('mailer:recipient-list')

class RecipientDeleteView(DeleteView):
    model = Recipient
    template_name = 'mailer/recipient_confirm_delete.html'
    success_url = reverse_lazy('mailer:recipient-list')


class MessageListView(ListView):
    model = Message
    template_name = 'mailer/message_list.html'
    context_object_name = 'messages'

class MessageCreateView(CreateView):
    model = Message
    fields = ['subject', 'body_text']
    template_name = 'mailer/message_form.html' #
    success_url = reverse_lazy('mailer:message-list')

class MessageUpdateView(UpdateView):
    model = Message
    fields = ['subject', 'body_text']
    template_name = 'mailer/message_form.html'
    success_url = reverse_lazy('mailer:message-list')

class MessageDeleteView(DeleteView):
    model = Message
    template_name = 'mailer/message_confirm_delete.html'
    success_url = reverse_lazy('mailer:message-list')


class MainPageView(TemplateView):
    """Главная страница"""
    template_name = 'mailer/main_page.html'

    @method_decorator(cache_page(60 * 5))
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if request.user.is_authenticated:
            user_campaigns_qs = Campaign.objects.filter(owner=request.user)

            context['total_campaigns'] = user_campaigns_qs.count()
            context['active_campaigns'] = user_campaigns_qs.filter(
                status=Campaign.STATUS_LAUNCHED
            ).count()
            context['unique_recipients'] = Recipient.objects.filter(owner=request.user).count()
        else:
            context['total_campaigns'] = 0
            context['active_campaigns'] = 0
            context['unique_recipients'] = 0

        return self.render_to_response(context)


class CampaignListView(LoginRequiredMixin, IsOwnerFilterMixin, ListView):
    model = Campaign
    template_name = 'mailer/campaign_list.html'
    context_object_name = 'campaigns'

class BaseCampaignFormMixin:
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time > end_time:
                raise ValidationError("Дата начала не может быть позже даты окончания.")
            if start_time < timezone.now():
                raise ValidationError("Дата начала не может быть в прошлом.")
        return cleaned_data

class CampaignCreateView(BaseCampaignFormMixin, LoginRequiredMixin, IsOwnerFilterMixin, CreateView):
    model = Campaign
    fields = ['message', 'recipients', 'start_time', 'end_time']
    template_name = 'mailer/campaign_form.html'
    success_url = reverse_lazy('mailer:campaign-list')

class CampaignUpdateView(BaseCampaignFormMixin, LoginRequiredMixin, IsOwnerFilterMixin, UpdateView):
    model = Campaign
    fields = ['message', 'recipients', 'start_time', 'end_time']
    template_name = 'mailer/campaign_form.html'
    success_url = reverse_lazy('mailer:campaign-list')

class CampaignDeleteView(LoginRequiredMixin, IsOwnerFilterMixin, DeleteView):
    model = Campaign
    template_name = 'mailer/campaign_confirm_delete.html'
    success_url = reverse_lazy('mailer:campaign-list')

class CampaignDetailView(LoginRequiredMixin, IsOwnerFilterMixin, DetailView):
    model = Campaign
    template_name = 'mailer/campaign_detail.html'
    context_object_name = 'campaign'
