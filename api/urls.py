"""
URL configuration for API app
Middleware de transferencia - Solo comunicación con Supabase
"""
from django.urls import path
from . import views

urlpatterns = [
    # IoT Endpoints (sin autenticación para ESP32)
    path('pir/event/', views.receive_pir_event, name='receive_pir_event'),
    path('pir/pending/', views.get_pending_motion_event, name='get_pending_motion_event'),
    path('pir/result/', views.get_event_result, name='get_event_result'),
    path('images/upload/', views.receive_images, name='receive_images'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Endpoints de gestión (lectura desde Supabase)
    path('events/', views.get_events, name='get_events'),
    path('alerts/', views.get_alerts, name='get_alerts'),
    
    # Registro de dispositivos (para ESP32)
    path('devices/register/', views.register_device, name='register_device'),
    path('sensors/register/', views.register_sensor, name='register_sensor'),
]
