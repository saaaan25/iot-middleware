"""
Serializers for IoT Middleware API
"""
from rest_framework import serializers
from .models import CustomUser, Device, Sensor, Event, Alert, ImageCapture


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model"""
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'name', 'last_name', 'phone', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for Device model"""
    class Meta:
        model = Device
        fields = ['id', 'name', 'address', 'ubication', 'status', 'user', 'created_at']
        read_only_fields = ['id', 'created_at']


class SensorSerializer(serializers.ModelSerializer):
    """Serializer for Sensor model"""
    class Meta:
        model = Sensor
        fields = ['id', 'name', 'type', 'pin', 'status', 'device', 'created_at']
        read_only_fields = ['id', 'created_at']


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model"""
    sensor_name = serializers.CharField(source='sensor.name', read_only=True)
    device_name = serializers.CharField(source='sensor.device.name', read_only=True)
    
    class Meta:
        model = Event
        fields = ['id', 'type', 'value', 'sensor', 'sensor_name', 'device_name', 'event_date']
        read_only_fields = ['id', 'event_date']


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model"""
    event_type = serializers.CharField(source='event.type', read_only=True)
    event_date = serializers.DateTimeField(source='event.event_date', read_only=True)
    
    class Meta:
        model = Alert
        fields = ['id', 'event', 'event_type', 'event_date', 'message', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']


class ImageCaptureSerializer(serializers.ModelSerializer):
    """Serializer for ImageCapture model"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ImageCapture
        fields = ['id', 'event', 'image', 'image_url', 'supabase_path', 'is_saved', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_image_url(self, obj):
        """Get the full URL for the image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class EventDetailSerializer(serializers.ModelSerializer):
    """Serializer for Event with related images"""
    images = ImageCaptureSerializer(many=True, read_only=True)
    sensor_name = serializers.CharField(source='sensor.name', read_only=True)
    
    class Meta:
        model = Event
        fields = ['id', 'type', 'value', 'sensor', 'sensor_name', 'event_date', 'images']
        read_only_fields = ['id', 'event_date']