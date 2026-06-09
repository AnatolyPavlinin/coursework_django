from django.urls import path
from .views import (
    RecipientListView,
    RecipientCreateView,
    RecipientUpdateView,
    RecipientDeleteView,
)

app_name = "mailer"

urlpatterns = [
    path('', RecipientListView.as_view(), name='recipient-list'),
    path('create/', RecipientCreateView.as_view(), name='recipient-create'),
    path('<int:pk>/update/', RecipientUpdateView.as_view(), name='recipient-update'),
    path('<int:pk>/delete/', RecipientDeleteView.as_view(), name='recipient-delete'),
]