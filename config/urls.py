from django.contrib import admin
from django.urls import path, include
from mailer.views import MainPageView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path("mailing/", include('mailer.urls', namespace='mailer')),
    path("", MainPageView.as_view(), name="main-page"),
]
