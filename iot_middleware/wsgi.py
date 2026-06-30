"""
WSGI config for iot_middleware project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_middleware.settings')

application = get_wsgi_application()