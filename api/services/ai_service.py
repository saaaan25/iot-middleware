"""
AI Service for IoT Middleware
Handles image processing and classification using PyTorch
"""
import os
import torch
import torch.nn as nn
from torchvision import transforms
import numpy as np
from django.conf import settings
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Intentar importar PIL, si no está disponible usar OpenCV o numpy
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    try:
        import cv2
        HAS_CV2 = True
        logger.warning("PIL no disponible, usando OpenCV para procesamiento de imágenes")
    except ImportError:
        HAS_CV2 = False
        logger.warning("Ni PIL ni OpenCV disponibles. Procesamiento de imágenes limitado.")


class AIService:
    """
    Service class for AI model operations
    Handles image classification and object detection
    """
    
    def __init__(self):
        """Initialize AI model"""
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = settings.MODEL_PATH
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
        self.class_names = ['person', 'animal', 'vehicle', 'other']
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        self._load_model()
    
    def _load_model(self):
        """Load the AI model from disk"""
        try:
            if os.path.exists(self.model_path):
                logger.info(f"Loading AI model from {self.model_path}")
                self.model = torch.load(self.model_path, map_location=self.device)
                self.model.eval()
                logger.info("AI model loaded successfully")
            else:
                logger.warning(f"Model file not found at {self.model_path}. Using dummy classifier.")
                self.model = self._create_dummy_model()
        except Exception as e:
            logger.error(f"Error loading AI model: {str(e)}. Using dummy classifier.")
            self.model = self._create_dummy_model()
    
    def _create_dummy_model(self):
        """
        Create a simple dummy model for testing
        In production, replace with your actual trained model
        """
        logger.info("Creating dummy model for testing purposes")
        
        class DummyModel(nn.Module):
            def __init__(self, num_classes):
                super().__init__()
                self.conv = nn.Conv2d(3, 64, 3, padding=1)
                self.pool = nn.AdaptiveAvgPool2d((1, 1))
                self.fc = nn.Linear(64, num_classes)
            
            def forward(self, x):
                x = torch.relu(self.conv(x))
                x = self.pool(x)
                x = x.view(x.size(0), -1)
                return self.fc(x)
        
        model = DummyModel(num_classes=len(self.class_names))
        model.eval()
        return model
    
    def _load_image(self, image_path: str) -> torch.Tensor:
        """
        Load and preprocess image from path
        Soporta PIL y OpenCV
        """
        try:
            if HAS_PIL:
                # Usar PIL
                image = Image.open(image_path).convert('RGB')
                image_tensor = self.transform(image)
            elif HAS_CV2:
                # Usar OpenCV
                img = cv2.imread(image_path)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (224, 224))
                img = img.astype(np.float32) / 255.0
                img = (img - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
                img = np.transpose(img, (2, 0, 1))
                image_tensor = torch.from_numpy(img).float()
            else:
                raise ImportError("Ni PIL ni OpenCV disponibles para cargar imágenes")
            
            image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
            return image_tensor.to(self.device)
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {str(e)}")
            raise
    
    def classify_image(self, image_path: str) -> Dict:
        """
        Classify a single image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            dict: Classification results with class, confidence, and all probabilities
        """
        try:
            if not self.model:
                return {
                    'success': False,
                    'error': 'Model not loaded',
                    'class': None,
                    'confidence': 0.0,
                    'all_probabilities': {}
                }
            
            # Load and preprocess image
            image_tensor = self._load_image(image_path)
            
            # Inference
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                
                # Get predicted class and confidence
                confidence, predicted_idx = torch.max(probabilities, 0)
                predicted_class = self.class_names[predicted_idx.item()]
                confidence_value = confidence.item()
            
            # Create probabilities dictionary
            all_probs = {
                class_name: prob.item() 
                for class_name, prob in zip(self.class_names, probabilities)
            }
            
            logger.info(f"Image classified as '{predicted_class}' with confidence {confidence_value:.2f}")
            
            return {
                'success': True,
                'class': predicted_class,
                'confidence': confidence_value,
                'all_probabilities': all_probs,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error classifying image: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'class': None,
                'confidence': 0.0,
                'all_probabilities': {}
            }
    
    def classify_batch(self, image_paths: List[str]) -> List[Dict]:
        """
        Classify multiple images
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            list: List of classification results
        """
        results = []
        for image_path in image_paths:
            result = self.classify_image(image_path)
            result['image_path'] = image_path
            results.append(result)
        return results
    
    def should_save_event(self, classification_result: Dict) -> Tuple[bool, str]:
        """
        Determine if an event should be saved based on classification results
        
        Args:
            classification_result: Result from classify_image
            
        Returns:
            tuple: (should_save: bool, reason: str)
        """
        if not classification_result['success']:
            return False, "Classification failed"
        
        predicted_class = classification_result['class']
        confidence = classification_result['confidence']
        
        # Check if confidence is above threshold
        if confidence < self.confidence_threshold:
            return False, f"Low confidence: {confidence:.2f} < {self.confidence_threshold}"
        
        # Define which classes should trigger an event
        event_classes = ['person', 'animal']
        
        if predicted_class in event_classes:
            return True, f"Detected {predicted_class} with confidence {confidence:.2f}"
        
        return False, f"Class '{predicted_class}' does not require event storage"
    
    def get_best_images(self, image_results: List[Dict], max_images: int = 5) -> List[Dict]:
        """
        Select the best images to save based on classification confidence
        
        Args:
            image_results: List of classification results
            max_images: Maximum number of images to select
            
        Returns:
            list: Top images sorted by confidence
        """
        # Filter successful classifications
        valid_results = [r for r in image_results if r['success']]
        
        # Sort by confidence (descending)
        sorted_results = sorted(valid_results, 
                               key=lambda x: x['confidence'], 
                               reverse=True)
        
        # Return top N images
        return sorted_results[:max_images]
    
    def process_event_images(self, image_paths: List[str]) -> Dict:
        """
        Process all images from an event and determine if event should be saved
        
        Args:
            image_paths: List of paths to event images
            
        Returns:
            dict: Processing results including classifications and recommendations
        """
        try:
            # Classify all images
            classifications = self.classify_batch(image_paths)
            
            # Determine if any image triggers an event
            should_save = False
            save_reason = ""
            best_classification = None
            
            for classification in classifications:
                save, reason = self.should_save_event(classification)
                if save:
                    should_save = True
                    save_reason = reason
                    if not best_classification or classification['confidence'] > best_classification['confidence']:
                        best_classification = classification
                    break
            
            # Get best images to save
            best_images = self.get_best_images(classifications, settings.MAX_IMAGES_TO_SAVE)
            
            return {
                'success': True,
                'should_save_event': should_save,
                'save_reason': save_reason,
                'total_images': len(image_paths),
                'classifications': classifications,
                'best_classification': best_classification,
                'images_to_save': [img['image_path'] for img in best_images],
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error processing event images: {str(e)}")
            return {
                'success': False,
                'should_save_event': False,
                'save_reason': str(e),
                'total_images': len(image_paths),
                'classifications': [],
                'best_classification': None,
                'images_to_save': [],
                'error': str(e)
            }