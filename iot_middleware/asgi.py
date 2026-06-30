"""
ASGI config for iot_middleware project.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_middleware.settings')

application = get_asgi_application()