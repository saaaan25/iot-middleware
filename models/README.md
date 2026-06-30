# Directorio de Modelos

Este directorio contiene los modelos de IA entrenados para el proyecto.

## Estructura

```
models/
├── best_model.pth          # Modelo entrenado (PyTorch)
├── classes.json            # Mapeo de clases del modelo
└── training_history.json   # Historial de entrenamiento
```

## Cómo obtener un modelo

### Opción 1: Usar el modelo dummy (testing)

El sistema incluye un modelo dummy que se usa automáticamente si no encuentra `best_model.pth`. Útil para testing y desarrollo.

### Opción 2: Entrenar tu propio modelo

1. Prepara tu dataset con la siguiente estructura:

```
dataset/
├── train/
│   ├── person/     # Imágenes de personas
│   ├── animal/     # Imágenes de animales
│   ├── vehicle/    # Imágenes de vehículos
│   └── other/      # Otras imágenes
└── val/
    ├── person/
    ├── animal/
    ├── vehicle/
    └── other/
```

2. Ejecuta el script de entrenamiento:

```bash
python scripts/train_model.py --data-dir ./dataset --epochs 20
```

3. El modelo se guardará automáticamente en `models/best_model.pth`

### Opción 3: Descargar un modelo pre-entrenado

Puedes usar modelos pre-entrenados como:
- YOLO (You Only Look Once)
- MobileNet
- EfficientNet
- ResNet

Asegúrate de que el modelo sea compatible con PyTorch y ajústalo en `api/services/ai_service.py`.

## Configuración

En el archivo `.env`:

```env
MODEL_PATH=models/best_model.pth
CONFIDENCE_THRESHOLD=0.7
```

## Clases soportadas

Por defecto, el modelo clasifica en:
- `person` - Personas
- `animal` - Animales
- `vehicle` - Vehículos
- `other` - Otros

Para cambiar las clases, modifica `class_names` en `api/services/ai_service.py` y reentrena el modelo.