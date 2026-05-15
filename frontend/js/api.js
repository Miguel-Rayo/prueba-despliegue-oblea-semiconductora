// ============================================================
// API CLIENT — Wrapper de fetch con manejo de errores
// ============================================================

async function apiGet(endpoint) {
    try {
        const res = await fetch(endpoint);
        if (!res.ok) {
            const err = await res.json().catch(() => ({ error: 'Error desconocido' }));
            throw new Error(err.error || err.detail || `HTTP ${res.status}`);
        }
        return await res.json();
    } catch (e) {
        console.error(`API GET ${endpoint} error:`, e);
        throw e;
    }
}

async function apiPost(endpoint, data) {
    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ error: 'Error desconocido' }));
            throw new Error(err.error || err.detail || `HTTP ${res.status}`);
        }
        return await res.json();
    } catch (e) {
        console.error(`API POST ${endpoint} error:`, e);
        throw e;
    }
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
