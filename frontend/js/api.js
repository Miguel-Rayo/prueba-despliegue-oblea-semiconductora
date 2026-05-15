// ============================================================
// API CLIENT — Wrapper de fetch con timeout, retry y manejo
// robusto de errores. Diseñado para soportar cold starts de
// servicios gratuitos (Render Free) sin romper la UX.
// ============================================================

const MAX_RETRIES = 3;
const FETCH_TIMEOUT = 20000; // 20s (Render Free puede tardar ~15-30s en despertar)
const RETRY_BASE_DELAY = 1500; // ms

/**
 * Realiza un fetch con timeout, reintentos automáticos y parseo seguro de JSON.
 * Reintenta en:
 *   - Errores de red (TypeError)
 *   - Timeouts (AbortError)
 *   - Respuestas no-JSON (Render a veces devuelve HTML "Starting...")
 *   - HTTP 502/503/504/5xx
 * No reintenta en:
 *   - HTTP 4xx (error del cliente / validación)
 */
async function _fetchWithRetry(url, options = {}, attempt = 0) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);

    try {
        const res = await fetch(url, { ...options, signal: controller.signal });
        clearTimeout(timeoutId);

        if (!res.ok) {
            // Errores de gateway / servidor → reintentables
            const isRetryableHttp = (res.status >= 500 && res.status <= 599) || res.status === 502 || res.status === 503 || res.status === 504;
            if (isRetryableHttp && attempt < MAX_RETRIES) {
                throw new Error(`RETRYABLE_HTTP_${res.status}`);
            }
            // Errores cliente → no reintentar, extraer mensaje si existe
            const errBody = await res.json().catch(() => ({}));
            throw new Error(errBody.detail || errBody.error || `Error del servidor (HTTP ${res.status})`);
        }

        // Parseo seguro de JSON
        const data = await res.json().catch(() => {
            throw new Error('RETRYABLE_JSON_PARSE');
        });
        return data;

    } catch (e) {
        clearTimeout(timeoutId);

        const isRetryable =
            e.name === 'AbortError' ||
            e.message === 'RETRYABLE_JSON_PARSE' ||
            e.message.startsWith('RETRYABLE_HTTP_') ||
            (e instanceof TypeError);

        if (isRetryable && attempt < MAX_RETRIES) {
            const delay = RETRY_BASE_DELAY * (attempt + 1);
            await new Promise(r => setTimeout(r, delay));
            return _fetchWithRetry(url, options, attempt + 1);
        }

        // Agotados los reintentos o error no reintentable
        if (e.name === 'AbortError') {
            throw new Error('El servidor no respondió a tiempo. Puede estar despertando tras inactividad. Intente de nuevo.');
        }
        if (e.message === 'RETRYABLE_JSON_PARSE') {
            throw new Error('Respuesta inesperada del servidor (posiblemente aún iniciando). Intente de nuevo en unos segundos.');
        }
        if (e.message.startsWith('RETRYABLE_HTTP_')) {
            const code = e.message.split('_')[2];
            throw new Error(`El servidor respondió con error ${code} tras varios intentos. Espere un momento e intente de nuevo.`);
        }
        throw e;
    }
}

async function apiGet(endpoint) {
    return _fetchWithRetry(endpoint, { method: 'GET' });
}

async function apiPost(endpoint, data) {
    return _fetchWithRetry(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
}

async function fetchHealth() {
    return apiGet(CONFIG.ENDPOINTS.HEALTH);
}

async function fetchRangos() {
    return apiGet(CONFIG.ENDPOINTS.RANGOS);
}

async function fetchMetricas() {
    return apiGet(CONFIG.ENDPOINTS.METRICAS);
}

async function fetchImportancia() {
    return apiGet(CONFIG.ENDPOINTS.IMPORTANCIA);
}

async function enviarPrediccion(datos) {
    return apiPost(CONFIG.ENDPOINTS.PREDECIR, datos);
}
