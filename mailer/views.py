from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Recipient


class RecipientListView(ListView):
    model = Recipient
    template_name = 'mailer/recipient_list.html'
    context_object_name = 'recipients'

class RecipientCreateView(CreateView):
    model = Recipient
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailer/recipient_form.html'
    success_url = reverse_lazy('recipient-list')

class RecipientUpdateView(UpdateView):
    model = Recipient
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailer/recipient_form.html'
    success_url = reverse_lazy('recipient-list')

class RecipientDeleteView(DeleteView):
    model = Recipient
    template_name = 'mailer/recipient_confirm_delete.html'
    success_url = reverse_lazy('recipient-list')
