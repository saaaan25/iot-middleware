"""
Views - Middleware de Transferencia
NO guarda datos localmente, solo transfiere a Supabase
"""
import os
import json
import logging
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.files.base import ContentFile

from .services.supabase_service import SupabaseService
from .services.ai_service import AIService

logger = logging.getLogger(__name__)

# Initialize services
supabase_service = SupabaseService()
ai_service = AIService()


@api_view(['POST'])
@permission_classes([AllowAny])
def receive_pir_event(request):
    """
    Endpoint para recibir eventos del sensor PIR desde ESP32
    NO guarda en BD local, solo transfiere a Supabase
    
    Expected payload:
    {
        "device_id": "ESP32_CAM_001",
        "sensor_pin": 13,
        "motion_detected": true,
        "timestamp": "2024-01-15T10:30:00Z"
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        device_id = data.get('device_id')
        sensor_pin = data.get('sensor_pin')
        motion_detected = data.get('motion_detected', False)
        
        if not device_id or sensor_pin is None:
            return Response({
                'success': False,
                'error': 'Missing required fields: device_id, sensor_pin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Preparar datos del evento para Supabase
        event_data = {
            'type': 'motion_detected',
            'value': json.dumps({
                'motion_detected': motion_detected,
                'device_id': device_id,
                'sensor_pin': sensor_pin,
                'timestamp': data.get('timestamp', timezone.now().isoformat())
            }),
            'sensor_id': None,  # Se debe obtener del sensor en Supabase
            'event_date': timezone.now().isoformat()
        }
        
        # Guardar evento en Supabase
        supabase_result = supabase_service.save_event_to_db(event_data)
        
        if not supabase_result['success']:
            logger.error(f"Error guardando evento en Supabase: {supabase_result['error']}")
            return Response({
                'success': False,
                'error': f'Error saving to Supabase: {supabase_result["error"]}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        event_id = supabase_result['data']['id'] if supabase_result['data'] else None
        
        logger.info(f"Evento PIR guardado en Supabase: {event_id}")
        
        # Si hay movimiento, indicar capturar imágenes
        if motion_detected:
            return Response({
                'success': True,
                'event_id': event_id,
                'action': 'capture_images',
                'message': 'Motion detected. Please capture images.',
                'images_to_capture': settings.IMAGES_PER_EVENT
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': True,
                'event_id': event_id,
                'action': 'none',
                'message': 'No motion detected'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error processing PIR event: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def receive_images(request):
    """
    Endpoint para recibir imágenes capturadas por el ESP32-CAM
    Procesa con IA y guarda en Supabase (NO guarda localmente)
    
    Expected payload (multipart/form-data):
    - event_id: UUID del evento en Supabase
    - device_id: ID del dispositivo
    - images[]: Array de archivos de imagen (hasta 10)
    """
    try:
        event_id = request.data.get('event_id')
        device_id = request.data.get('device_id')
        images = request.FILES.getlist('images[]')
        
        if not event_id or not device_id:
            return Response({
                'success': False,
                'error': 'Missing required fields: event_id, device_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not images:
            return Response({
                'success': False,
                'error': 'No images provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Limitar a IMAGES_PER_EVENT imágenes
        images = images[:settings.IMAGES_PER_EVENT]
        
        # Guardar temporalmente para procesar con IA
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        image_paths = []
        for idx, image_file in enumerate(images):
            temp_path = os.path.join(temp_dir, f"{event_id}_{idx}.jpg")
            with open(temp_path, 'wb') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            image_paths.append(temp_path)
        
        logger.info(f"Procesando {len(image_paths)} imágenes con IA...")
        
        # Procesar imágenes con IA
        ai_result = ai_service.process_event_images(image_paths)
        
        response_data = {
            'success': True,
            'event_id': event_id,
            'images_received': len(images),
            'images_processed': len(image_paths),
            'ai_processing': {
                'should_save_event': ai_result['should_save_event'],
                'save_reason': ai_result['save_reason'],
                'best_classification': ai_result['best_classification']
            }
        }
        
        # Si IA recomienda guardar, subir a Supabase
        if ai_result['should_save_event'] and ai_result['images_to_save']:
            logger.info("IA recomienda guardar evento. Subiendo a Supabase...")
            
            # Subir mejores imágenes a Supabase Storage
            uploaded_images = []
            for img_path in ai_result['images_to_save']:
                with open(img_path, 'rb') as f:
                    upload_result = supabase_service.upload_image(
                        ContentFile(f.read(), name=os.path.basename(img_path))
                    )
                    
                    if upload_result['success']:
                        uploaded_images.append({
                            'path': upload_result['path'],
                            'url': upload_result['url']
                        })
                        logger.info(f"Imagen subida a Supabase: {upload_result['path']}")
            
            # Actualizar evento en Supabase con resultado de IA
            best_class = ai_result['best_classification']
            event_update = {
                'type': best_class['class'] if best_class else 'unknown',
                'value': json.dumps({
                    'confidence': best_class['confidence'] if best_class else 0,
                    'all_probabilities': best_class['all_probabilities'] if best_class else {},
                    'total_images': len(image_paths),
                    'images_uploaded': len(uploaded_images),
                    'device_id': device_id
                })
            }
            
            # Actualizar evento en Supabase
            supabase_service.client.table('events').update(event_update).eq('id', event_id).execute()
            
            # Crear alerta en Supabase
            alert_data = {
                'event_id': event_id,
                'message': f"Evento detectado: {best_class['class'] if best_class else 'unknown'} "
                          f"con {best_class['confidence']*100:.1f}% de confianza",
                'status': 'completed',
                'created_at': timezone.now().isoformat()
            }
            
            alert_result = supabase_service.save_alert_to_db(alert_data)
            
            response_data['supabase'] = {
                'event_updated': True,
                'alert_created': alert_result['success'],
                'images_uploaded': len(uploaded_images),
                'uploaded_images': uploaded_images
            }
        else:
            response_data['ai_processing']['message'] = ai_result['save_reason']
        
        # Limpiar archivos temporales
        for img_path in image_paths:
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except:
                pass
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error processing images: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'service': 'IoT Middleware',
        'version': '1.0.0',
        'mode': 'transfer_only',
        'supabase_configured': bool(settings.SUPABASE_URL and settings.SUPABASE_KEY),
        'ai_model_loaded': ai_service.model is not None
    })


# ==================== ENDPOINTS DE GESTIÓN (SOLO LECTURA DESDE SUPABASE) ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_events(request):
    """Obtener eventos desde Supabase"""
    try:
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        event_type = request.query_params.get('type')
        
        result = supabase_service.get_events(limit=limit, offset=offset, event_type=event_type)
        
        if result['success']:
            return Response(result['data'], status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_alerts(request):
    """Obtener alertas desde Supabase"""
    try:
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        alert_status = request.query_params.get('status')
        
        result = supabase_service.get_alerts(limit=limit, offset=offset, status=alert_status)
        
        if result['success']:
            return Response(result['data'], status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device(request):
    """
    Registrar dispositivo en Supabase
    (Endpoint para que el ESP32 se registre)
    """
    try:
        data = request.data
        
        device_data = {
            'name': data.get('name'),
            'address': data.get('address'),
            'ubication': data.get('ubication'),
            'status': data.get('status', True),
            'user_id': str(request.user.id) if request.user.is_authenticated else None,
            'created_at': timezone.now().isoformat()
        }
        
        result = supabase_service.client.table('devices').insert(device_data).execute()
        
        if result.data:
            return Response(result.data[0], status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Failed to register device'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_sensor(request):
    """
    Registrar sensor en Supabase
    (Endpoint para que el ESP32 registre sus sensores)
    """
    try:
        data = request.data
        
        sensor_data = {
            'name': data.get('name'),
            'type': data.get('type'),
            'pin': data.get('pin'),
            'status': data.get('status', True),
            'device_id': data.get('device_id'),
            'created_at': timezone.now().isoformat()
        }
        
        result = supabase_service.client.table('sensors').insert(sensor_data).execute()
        
        if result.data:
            return Response(result.data[0], status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Failed to register sensor'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)