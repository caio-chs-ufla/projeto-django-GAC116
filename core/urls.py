from django.urls import path
from . import views

urlpatterns = [
    path('academia/<int:pk>/checkin/', views.checkin_verificar, name='checkin_verificar'),
]
