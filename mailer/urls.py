from django.urls import path
from .views import (
    RecipientListView,
    RecipientCreateView,
    RecipientUpdateView,
    RecipientDeleteView,
    MessageListView,
    MessageCreateView,
    MessageDeleteView,
    MessageUpdateView,
    CampaignListView,
    ManagerDashboardView,
    CampaignCreateView,
    CampaignDetailView,
    CampaignDeleteView,
    CampaignUpdateView,
    BaseCampaignFormMixin,
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

    path('campaign/', CampaignListView.as_view(), name='campaign-list'),
    path("campaign/create/", CampaignCreateView.as_view(), name="campaign-create"),
    path("campaign/<int:pk>/", CampaignDetailView.as_view(), name="campaign-detail"),
    path("campaign/<int:pk>/update/", CampaignUpdateView.as_view(), name="campaign-update"),
    path("campaign/<int:pk>/delete/", CampaignDeleteView.as_view(), name="campaign-delete"),

    path("manager/", ManagerDashboardView.as_view(), name="manager-dashboard"),

]
