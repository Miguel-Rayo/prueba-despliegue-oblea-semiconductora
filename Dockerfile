# ============================================================
# SWAL Semiconductors — Imagen de Producción
# Render Web Service (Docker Runtime)
# ============================================================

FROM python:3.11-slim

# Evitar buffering de Python en logs (crítico para Render)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ------------------------------------------------------------------
# JAVA (requerido por pypmml)
# ------------------------------------------------------------------
# En Debian Bookworm (base de python:3.11-slim) OpenJDK 21 se instala en:
#   /usr/lib/jvm/java-21-openjdk-amd64
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Límite de memoria JVM CRÍTICO para Render Free (512 MB RAM total).
# Sin esto la JVM intenta reservar ~1/4 de la RAM del host (puede ser >2 GB
# en el nodo de Docker) y el contenedor muere por OOM antes de arrancar.
ENV _JAVA_OPTIONS="-Xmx256m -XX:+UseContainerSupport -XX:MaxRAMPercentage=50.0"

WORKDIR /app

# ------------------------------------------------------------------
# 1. Dependencias del sistema
# ------------------------------------------------------------------
# openjdk-21-jdk  → JVM para pypmml
# gcc             → compilación de wheels nativos (por seguridad)
# libgomp1        → OpenMP, requerido por algunas librerías numéricas
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openjdk-21-jdk \
        gcc \
        libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verificar que Java está presente y accesible (falla el build si no)
RUN java -version && echo "Java OK"

# ------------------------------------------------------------------
# 2. Dependencias Python
# ------------------------------------------------------------------
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# ------------------------------------------------------------------
# 3. Código fuente
# ------------------------------------------------------------------
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

WORKDIR /app/backend

# ------------------------------------------------------------------
# 4. Healthcheck
# ------------------------------------------------------------------
# Render usa esto para saber si el contenedor está sano.
# start-period=60s da tiempo a que la JVM cargue el modelo PMML (~16 MB).
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# ------------------------------------------------------------------
# 5. Puerto y comando de arranque
# ------------------------------------------------------------------
# Render inyecta la variable $PORT automáticamente.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
