# SWAL Semiconductors — Web Service

Servicio web de predicción de defectos en obleas semiconductoras usando un modelo Random Forest entrenado en R y exportado a PMML.

## Requisitos

- Python 3.14.3 (o compatible)
- Java JDK 21 o 26 (para evaluar el modelo PMML)

## Instalación

```powershell
cd web-service/backend
python -m venv venv
```

## Ejecución

```powershell
.\run.ps1
```

El script detectará automáticamente Java, activará el entorno virtual e iniciará el servidor en `http://localhost:8000`.

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/` | Bienvenida |
| GET | `/api/health` | Estado del sistema |
| GET | `/api/rangos` | Rangos válidos de variables |
| GET | `/api/metricas` | Métricas del modelo |
| GET | `/api/importancia` | Ranking de variables |
| POST | `/api/predecir` | Predicción de defecto |

## Estructura

```
backend/
  app/           # Código fuente FastAPI
  data/          # Modelo PMML y parámetros
  tests/         # Tests unitarios
  venv/          # Entorno virtual (tú lo creas)
  run.ps1        # Script de lanzamiento
frontend/
  index.html     # Single Page Application
  css/           # Estilos premium
  js/            # Lógica cliente
```

## Stack

- Backend: Python 3.14, FastAPI, Pydantic v1, pypmml, Uvicorn
- Frontend: HTML5, CSS3, Vanilla JS
- Modelo: Random Forest (R) → PMML → Java (JPMML)
