from django.urls import path
from .views import (
    RecipientListView,
    RecipientCreateView,
    RecipientUpdateView,
    RecipientDeleteView,
    MessageListView,
    MessageCreateView,
    MessageDeleteView,
    MessageUpdateView
)

app_name = "mailer"

urlpatterns = [
    path('', RecipientListView.as_view(), name='recipient-list'),
    path('create/', RecipientCreateView.as_view(), name='recipient-create'),
    path('<int:pk>/update/', RecipientUpdateView.as_view(), name='recipient-update'),
    path('<int:pk>/delete/', RecipientDeleteView.as_view(), name='recipient-delete'),

    path('messages/', MessageListView.as_view(), name='message-list'),
    path('messages/create/', MessageCreateView.as_view(), name='message-create'),
    path('messages/<int:pk>/update/', MessageUpdateView.as_view(), name='message-update'),
    path('messages/<int:pk>/delete/', MessageDeleteView.as_view(), name='message-delete'),
]
