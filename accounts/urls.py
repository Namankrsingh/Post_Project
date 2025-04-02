from django.contrib import admin
from django.urls import path
from accounts.views import RegisterView, LoginView

urlpatterns = [
    path('register/',RegisterView.as_view()),
    path('login/',LoginView.as_view())
]
