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
    Service class that acts as a client for the AI model deployed on Render.
    It adapts the Render response to the internal format expected by the middleware.
    """

    def __init__(self):
        self.api_url = settings.MODEL_PATH
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD

        self.model_ready = bool(self.api_url)

        if not self.model_ready:
            logger.warning("MODEL_PATH no está configurada.")

    def process_event_images(self, image_paths: List[str]) -> Dict:

        try:

            if not self.model_ready:
                raise ValueError("Remote AI Service URL is missing.")

            files = []
            opened_files = []

            for path in image_paths:
                f = open(path, "rb")
                opened_files.append(f)

                files.append(
                    (
                        "images",
                        (
                            os.path.basename(path),
                            f,
                            "image/jpeg",
                        ),
                    )
                )

            logger.info(
                f"Enviando {len(image_paths)} imágenes a Render: {self.api_url}"
            )

            response = requests.post(
                self.api_url,
                files=files,
                timeout=60,
            )

            for f in opened_files:
                f.close()

            response.raise_for_status()

            render_result = response.json()

            logger.info(f"Respuesta Render: {render_result}")

            ##############################################
            # Adaptar respuesta de Render al Middleware
            ##############################################

            silent = render_result.get("silent", True)

            should_save_event = not silent

            best_classification = None

            if should_save_event:

                best_classification = {
                    "class": render_result.get("status", "UNKNOWN"),
                    "confidence": render_result.get("similarity", 0),
                    "matched_identity": render_result.get("matched_identity"),
                    "top5": render_result.get("top5", []),
                }

            return {

                "success": True,

                "should_save_event": should_save_event,

                "save_reason": (
                    render_result.get("status")
                    if should_save_event
                    else "No se detectó un rostro autorizado"
                ),

                "best_classification": best_classification,

                "classifications": (
                    [best_classification]
                    if best_classification
                    else []
                ),

                "images_to_save": (
                    image_paths
                    if should_save_event
                    else []
                ),

                # Respuesta original de Render
                "raw_response": render_result,
            }

        except Exception as e:

            logger.exception("Error en inferencia remota")

            return {

                "success": False,

                "should_save_event": False,

                "save_reason": f"Remote Inference Failed: {str(e)}",

                "classifications": [],

                "best_classification": None,

                "images_to_save": [],

                "raw_response": None,
            }
