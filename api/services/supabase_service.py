"""
Supabase Service for IoT Middleware
Handles communication with Supabase Storage and Database
"""
import os
import uuid
from pathlib import Path
from supabase import create_client, Client
from django.conf import settings
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


class SupabaseService:
    """
    Service class for Supabase operations
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.service_key = settings.SUPABASE_SERVICE_KEY
        
        if not self.url or not self.key:
            logger.warning("Supabase credentials not configured")
            self.client = None
            self.service_client = None
        else:
            self.client = create_client(self.url, self.key)
            self.service_client = create_client(self.url, self.service_key) if self.service_key else None

    def _write_client(self):
        """Return service role client for writes when available."""
        return self.service_client or self.client

    def get_or_create_sensor(self, device_label: str, sensor_pin: int, sensor_type: str = 'pir') -> dict:
        """
        Resolve a sensor id by logical name/pin, creating it if missing.

        Returns:
            dict: {'success': bool, 'sensor_id': str|None, 'error': str|None}
        """
        try:
            write_client = self._write_client()
            if not write_client:
                return {'success': False, 'sensor_id': None, 'error': 'Supabase not configured'}

            sensor_name = f"{sensor_type.upper()}_{device_label}_{sensor_pin}"

            # 1) Try by exact name first.
            lookup = write_client.table('sensors').select('id').eq('name', sensor_name).limit(1).execute()
            if lookup.data:
                return {'success': True, 'sensor_id': lookup.data[0]['id'], 'error': None}

            # 2) Create minimal sensor row compatible with current schema.
            sensor_row = {
                'name': sensor_name,
                'type': sensor_type,
                'pin': sensor_pin,
                'status': True,
                'device_id': None,
            }

            created = write_client.table('sensors').insert(sensor_row).execute()
            if created.data:
                return {'success': True, 'sensor_id': created.data[0]['id'], 'error': None}

            return {'success': False, 'sensor_id': None, 'error': 'Could not create sensor row'}
        except Exception as e:
            logger.error(f"Error resolving/creating sensor: {str(e)}")
            return {'success': False, 'sensor_id': None, 'error': str(e)}
    
    def upload_image(self, image_file, bucket_name='event-images', folder_path='events/') -> dict:
        """
        Upload an image to Supabase Storage
        
        Args:
            image_file: Django file object
            bucket_name: Name of the Supabase storage bucket
            folder_path: Folder path within the bucket
            
        Returns:
            dict: Contains 'success', 'path', 'url', and 'error' keys
        """
        try:
            if not self.service_client:
                return {'success': False, 'error': 'Supabase not configured'}
            
            # Generate unique filename
            file_extension = Path(image_file.name).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            full_path = f"{folder_path}{unique_filename}"
            
            # Read file content
            file_content = image_file.read()
            
            # Upload to Supabase
            response = self.service_client.storage.from_(bucket_name).upload(
                path=full_path,
                file=file_content,
                file_options={"content-type": image_file.content_type}
            )
            
            # Get public URL
            public_url = self.service_client.storage.from_(bucket_name).get_public_url(full_path)
            
            logger.info(f"Image uploaded successfully to Supabase: {full_path}")
            
            return {
                'success': True,
                'path': full_path,
                'url': public_url,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error uploading image to Supabase: {str(e)}")
            return {
                'success': False,
                'path': None,
                'url': None,
                'error': str(e)
            }
    
    def delete_image(self, path, bucket_name='event-images') -> bool:
        """
        Delete an image from Supabase Storage
        
        Args:
            path: Path to the file in the bucket
            bucket_name: Name of the Supabase storage bucket
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service_client:
                return False
            
            self.service_client.storage.from_(bucket_name).remove([path])
            logger.info(f"Image deleted from Supabase: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting image from Supabase: {str(e)}")
            return False
    
    def save_event_to_db(self, event_data: dict) -> dict:
        """
        Save event data to Supabase database
        
        Args:
            event_data: Dictionary with event information
            
        Returns:
            dict: Contains 'success' and 'data' or 'error' keys
        """
        try:
            write_client = self._write_client()
            if not write_client:
                return {'success': False, 'error': 'Supabase not configured'}
            
            # Insert event into Supabase
            response = write_client.table('events').insert(event_data).execute()
            
            return {
                'success': True,
                'data': response.data[0] if response.data else None,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error saving event to Supabase: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def save_alert_to_db(self, alert_data: dict) -> dict:
        """
        Save alert data to Supabase database
        
        Args:
            alert_data: Dictionary with alert information
            
        Returns:
            dict: Contains 'success' and 'data' or 'error' keys
        """
        try:
            write_client = self._write_client()
            if not write_client:
                return {'success': False, 'error': 'Supabase not configured'}
            
            # Insert alert into Supabase
            response = write_client.table('alerts').insert(alert_data).execute()
            
            return {
                'success': True,
                'data': response.data[0] if response.data else None,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error saving alert to Supabase: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def get_events(self, limit=100, offset=0, event_type=None) -> dict:
        """
        Retrieve events from Supabase
        
        Args:
            limit: Maximum number of events to retrieve
            offset: Offset for pagination
            event_type: Filter by event type (optional)
            
        Returns:
            dict: Contains 'success', 'data', and 'error' keys
        """
        try:
            if not self.client:
                return {'success': False, 'data': None, 'error': 'Supabase not configured'}
            
            query = self.client.table('events').select('*').order('event_date', desc=True).limit(limit).offset(offset)
            
            if event_type:
                query = query.eq('type', event_type)
            
            response = query.execute()
            
            return {
                'success': True,
                'data': response.data,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error retrieving events from Supabase: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def get_alerts(self, limit=100, offset=0, status=None) -> dict:
        """
        Retrieve alerts from Supabase
        
        Args:
            limit: Maximum number of alerts to retrieve
            offset: Offset for pagination
            status: Filter by status (optional)
            
        Returns:
            dict: Contains 'success', 'data', and 'error' keys
        """
        try:
            if not self.client:
                return {'success': False, 'data': None, 'error': 'Supabase not configured'}
            
            query = self.client.table('alerts').select('*').order('created_at', desc=True).limit(limit).offset(offset)
            
            if status:
                query = query.eq('status', status)
            
            response = query.execute()
            
            return {
                'success': True,
                'data': response.data,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error retrieving alerts from Supabase: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
