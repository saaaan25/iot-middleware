"""
Modelos de Referencia - NO se usan en el middleware
Estos modelos están alineados con la estructura de Supabase
para documentación y referencia del esquema de datos.
"""
from django.db import models

# NOTA: Estos modelos NO están registrados en INSTALLED_APPS
# Solo sirven como referencia de la estructura de Supabase


class Profile(models.Model):
    """Perfil de usuario (Supabase auth.users)"""
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=20, default='user')


class Device(models.Model):
    """Dispositivo ESP32"""
    id = models.UUIDField(primary_key=True, default=models.UUIDField().default)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=50)
    ubication = models.CharField(max_length=200)
    status = models.BooleanField(default=True)
    user_id = models.UUIDField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Sensor(models.Model):
    """Sensor del dispositivo (PIR, Cámara, etc.)"""
    id = models.UUIDField(primary_key=True, default=models.UUIDField().default)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    pin = models.BigIntegerField()
    status = models.BooleanField(default=True)
    device_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)


class Event(models.Model):
    """Evento detectado"""
    id = models.UUIDField(primary_key=True, default=models.UUIDField().default)
    type = models.CharField(max_length=50)
    value = models.TextField(null=True, blank=True)
    sensor_id = models.UUIDField()
    event_date = models.DateTimeField(auto_now_add=True)


class Alert(models.Model):
    """Alerta generada"""
    id = models.UUIDField(primary_key=True, default=models.UUIDField().default)
    event_id = models.UUIDField()
    message = models.TextField()
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)