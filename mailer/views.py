from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from .models import Recipient, Message, Campaign


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
    template_name = 'mailer/main_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_campaigns'] = Campaign.objects.count()
        context['active_campaigns'] = Campaign.objects.filter(status=Campaign.STATUS_LAUNCHED).count()
        context['unique_recipients'] = Recipient.objects.count()

        return context


class CampaignListView(ListView):
    model = Campaign
    template_name = 'mailer/campaign_list.html'
    context_object_name = 'mailer:campaigns'