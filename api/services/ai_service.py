"""
AI Service Wrapper for Remote Inference on Render
Sends images to the external Render API instead of processing locally.
"""
import os
import requests
import logging
from django.conf import settings
from typing import Dict, List

logger = logging.getLogger(__name__)

class AIService:
    """
    Service class that acts as a client for the AI model deployed on Render
    """
    def __init__(self):
        self.api_url = settings.MODEL_PATH
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
        # El modelo vive en Render, así que solo verificamos si la URL está configurada
        self.model_ready = bool(self.api_url)
        if not self.model_ready:
            logger.warning("MODEL_PATH no está configurada en los settings.")

    def process_event_images(self, image_paths: List[str]) -> Dict:
        """
        Envía un lote (batch) de imágenes al servicio en Render para su clasificación.
        """
        try:
            if not self.model_ready:
                raise ValueError("Remote AI Service URL is missing.")

            # Preparar los archivos para enviarlos en un formato multipart/form-data idéntico
            files = []
            opened_files = []
            for path in image_paths:
                f = open(path, 'rb')
                opened_files.append(f)
                # 'images' es el nombre que esperará el endpoint en Render para el array de archivos
                files.append(('images', (os.path.basename(path), f, 'image/jpeg')))

            logger.info(f"Enviando {len(image_paths)} imágenes a la API de Render: {self.api_url}")
            
            # Petición HTTP POST al microservicio de Render
            response = requests.post(self.api_url, files=files, timeout=30)
            
            # Cerrar los archivos abiertos de inmediato
            for f in opened_files:
                f.close()

            response.raise_for_status()
            ai_result = response.json() # Esperamos que Render devuelva el JSON estructurado con el resultado

            return ai_result

        except Exception as e:
            logger.error(f"Error en la inferencia remota con Render: {str(e)}")
            # Devolvemos una estructura de fallback segura para que el flujo de views no rompa
            return {
                'success': False,
                'should_save_event': False,
                'save_reason': f"Remote Inference Failed: {str(e)}",
                'classifications': [],
                'best_classification': None,
                'images_to_save': []
            }
