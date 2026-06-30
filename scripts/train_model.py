#!/usr/bin/env python3
"""
Script de entrenamiento del modelo de IA para clasificación de imágenes
Entrena un modelo PyTorch para detectar personas, animales, vehículos, etc.
"""
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
import argparse
from pathlib import Path
import json
from datetime import datetime

# Configuración
BATCH_SIZE = 32
EPOCHS = 20
LEARNING_RATE = 0.001
IMAGE_SIZE = 224
MODEL_SAVE_PATH = Path(__file__).parent.parent / 'models' / 'best_model.pth'
CLASSES_JSON_PATH = Path(__file__).parent.parent / 'models' / 'classes.json'


class ImageClassifier:
    """Clasificador de imágenes basado en ResNet"""
    
    def __init__(self, num_classes, device=None):
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.num_classes = num_classes
        
        # Cargar modelo pre-entrenado (ResNet50)
        self.model = models.resnet50(pretrained=True)
        
        # Reemplazar la última capa para nuestro número de clases
        num_features = self.model.fc.in_features
        self.model.fc = nn.Linear(num_features, num_classes)
        
        # Mover modelo a dispositivo
        self.model = self.model.to(self.device)
        
        # Definir criterio y optimizador
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=LEARNING_RATE)
        
        print(f"Modelo creado en dispositivo: {self.device}")
    
    def train_epoch(self, train_loader):
        """Entrena una época"""
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (images, labels) in enumerate(train_loader):
            images, labels = images.to(self.device), labels.to(self.device)
            
            # Zero gradients
            self.optimizer.zero_grad()
            
            # Forward pass
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            # Estadísticas
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            if (batch_idx + 1) % 10 == 0:
                print(f'  Batch [{batch_idx+1}/{len(train_loader)}], '
                      f'Loss: {loss.item():.4f}, '
                      f'Acc: {100 * correct / total:.2f}%')
        
        epoch_loss = running_loss / len(train_loader)
        epoch_acc = 100 * correct / total
        return epoch_loss, epoch_acc
    
    def validate(self, val_loader):
        """Valida el modelo"""
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(self.device), labels.to(self.device)
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                
                running_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        val_loss = running_loss / len(val_loader)
        val_acc = 100 * correct / total
        return val_loss, val_acc
    
    def train(self, train_loader, val_loader, epochs):
        """Entrena el modelo"""
        best_val_acc = 0.0
        history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': []
        }
        
        print(f"\nIniciando entrenamiento por {epochs} épocas...")
        print("=" * 60)
        
        for epoch in range(epochs):
            print(f"\nÉpoca {epoch+1}/{epochs}")
            print("-" * 60)
            
            # Entrenar
            train_loss, train_acc = self.train_epoch(train_loader)
            print(f"Entrenamiento - Loss: {train_loss:.4f}, Acc: {train_acc:.2f}%")
            
            # Validar
            val_loss, val_acc = self.validate(val_loader)
            print(f"Validación  - Loss: {val_loss:.4f}, Acc: {val_acc:.2f}%")
            
            # Guardar historial
            history['train_loss'].append(train_loss)
            history['train_acc'].append(train_acc)
            history['val_loss'].append(val_loss)
            history['val_acc'].append(val_acc)
            
            # Guardar mejor modelo
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                self.save_model(MODEL_SAVE_PATH)
                print(f"✓ Mejor modelo guardado (Val Acc: {val_acc:.2f}%)")
        
        print("\n" + "=" * 60)
        print(f"Entrenamiento completado. Mejor accuracy: {best_val_acc:.2f}%")
        print("=" * 60)
        
        return history
    
    def save_model(self, path):
        """Guarda el modelo"""
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'num_classes': self.num_classes,
            'model_type': 'resnet50'
        }, path)
        print(f"Modelo guardado en: {path}")


def prepare_datasets(data_dir):
    """
    Prepara los datasets de entrenamiento y validación
    
    Estructura esperada:
    data_dir/
    ├── train/
    │   ├── person/
    │   ├── animal/
    │   ├── vehicle/
    │   └── other/
    └── val/
        ├── person/
        ├── animal/
        ├── vehicle/
        └── other/
    """
    data_dir = Path(data_dir)
    
    # Transformaciones
    train_transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE + 32, IMAGE_SIZE + 32)),
        transforms.RandomCrop(IMAGE_SIZE),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    # Cargar datasets
    train_dataset = datasets.ImageFolder(
        root=data_dir / 'train',
        transform=train_transform
    )
    
    val_dataset = datasets.ImageFolder(
        root=data_dir / 'val',
        transform=val_transform
    )
    
    # Crear data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=4
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=4
    )
    
    print(f"Dataset de entrenamiento: {len(train_dataset)} imágenes")
    print(f"Dataset de validación: {len(val_dataset)} imágenes")
    print(f"Clases: {train_dataset.classes}")
    
    return train_loader, val_loader, train_dataset.classes


def save_classes(classes, path):
    """Guarda las clases en un archivo JSON"""
    class_mapping = {i: class_name for i, class_name in enumerate(classes)}
    with open(path, 'w') as f:
        json.dump(class_mapping, f, indent=2)
    print(f"Clases guardadas en: {path}")


def main():
    parser = argparse.ArgumentParser(description='Entrenar modelo de clasificación de imágenes')
    parser.add_argument('--data-dir', type=str, required=True,
                       help='Directorio con datos de entrenamiento (train/ y val/)')
    parser.add_argument('--epochs', type=int, default=EPOCHS,
                       help=f'Número de épocas (default: {EPOCHS})')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                       help=f'Tamaño del batch (default: {BATCH_SIZE})')
    parser.add_argument('--lr', type=float, default=LEARNING_RATE,
                       help=f'Tasa de aprendizaje (default: {LEARNING_RATE})')
    parser.add_argument('--output', type=str, default=str(MODEL_SAVE_PATH),
                       help=f'Ruta para guardar el modelo (default: {MODEL_SAVE_PATH})')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Entrenamiento de Modelo de Clasificación de Imágenes")
    print("=" * 60)
    print(f"\nConfiguración:")
    print(f"  Directorio de datos: {args.data_dir}")
    print(f"  Épocas: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Learning rate: {args.lr}")
    print(f"  Modelo guardado en: {args.output}")
    print()
    
    # Preparar datasets
    train_loader, val_loader, classes = prepare_datasets(args.data_dir)
    
    # Guardar clases
    save_classes(classes, CLASSES_JSON_PATH)
    
    # Crear y entrenar modelo
    classifier = ImageClassifier(num_classes=len(classes))
    history = classifier.train(train_loader, val_loader, args.epochs)
    
    # Guardar historial
    history_path = Path(__file__).parent.parent / 'models' / 'training_history.json'
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"\n✓ Entrenamiento completado exitosamente")
    print(f"✓ Modelo guardado en: {args.output}")
    print(f"✓ Clases guardadas en: {CLASSES_JSON_PATH}")
    print(f"✓ Historial guardado en: {history_path}")


if __name__ == '__main__':
    main()