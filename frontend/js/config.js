// ============================================================
// CONFIGURACIÓN FRONTEND
// ============================================================

const CONFIG = {
    // Como FastAPI sirve el frontend como estático,
    // las llamadas a la API van a rutas relativas /api/*
    API_BASE: '',
    ENDPOINTS: {
        HEALTH:   '/api/health',
        RANGOS:   '/api/rangos',
        METRICAS: '/api/metricas',
        PREDECIR: '/api/predecir',
        IMPORTANCIA: '/api/importancia'
    },
    // Rangos válidos (fallback si la API no responde)
    RANGOS: {
        temperature_c:    { min: 380, max: 520, unit: '°C', typical: 450 },
        pressure_torr:    { min: 600, max: 900, unit: 'Torr', typical: 760 },
        gas_flow_sccm:    { min: 80,  max: 160, unit: 'sccm', typical: 115 },
        etch_rate_nm_min: { min: 60,  max: 130, unit: 'nm/min', typical: 95 },
        voltage_v:        { min: 3.5, max: 6.5, unit: 'V', typical: 5.0 },
        current_ma:       { min: 12,  max: 28,  unit: 'mA', typical: 20 },
    },
    ETAPAS: ['CMP', 'Deposition', 'Etching', 'Lithography', 'Oxidation'],
    IMPORTANCIA_FALLBACK: [
        { variable: "pressure_torr", rank: 1, descripcion: "Presión del proceso", importance: 1227,
          explicacion: "Imagina que estás inflando un globo: si soplas muy fuerte o muy débil, la forma no queda uniforme. En la fabricación de chips, la presión dentro de la cámara controla cómo se depositan las capas. Es la variable más poderosa porque un pequeño cambio altera toda la estructura del circuito." },
        { variable: "anomaly_score", rank: 2, descripcion: "Score de anomalía combinado", importance: 680,
          explicacion: "Este es como un 'termómetro grupal' que resume qué tan extraños se ven todos los parámetros juntos. Si varias mediciones se salen de lo normal al mismo tiempo, esta puntuación dispara la alerta de defecto." },
        { variable: "etch_rate_nm_min", rank: 3, descripcion: "Tasa de grabado", importance: 205,
          explicacion: "El grabado es como tallar madera con láser: la velocidad determina qué tan profundo y preciso queda el canal. Si va muy rápido, se come material de más; si va lento, deja residuos que estropean el chip." },
        { variable: "temperature_c", rank: 4, descripcion: "Temperatura de la cámara", importance: 166,
          explicacion: "Piensa en hornear un pastel: la temperatura define si queda crudo o quemado. En semiconductores, cada material necesita una temperatura exacta para cristalizar correctamente. Unos pocos grados de diferencia pueden arruinar millones de transistores." },
        { variable: "step_Deposition", rank: 5, descripcion: "Etapa: Deposición", importance: 53,
          explicacion: "La deposición es como pintar capas ultrafinas sobre la oblea. Es una de las etapas más delicadas porque cada capa debe tener el grosor exacto de unos pocos átomos para que el chip funcione." },
        { variable: "current_ma", rank: 6, descripcion: "Corriente eléctrica", importance: 51,
          explicacion: "La corriente es la cantidad de electrones circulando por el equipo. Es como el caudal de agua en una tubería: si es muy alta, puede dañar componentes; si es muy baja, los procesos no se activan correctamente." },
        { variable: "step_Lithography", rank: 7, descripcion: "Etapa: Litografía", importance: 49,
          explicacion: "La litografía es como usar un proyector de luz para dibujar circuitos diminutos. Usa luz ultravioleta para transferir patrones. Si la temperatura o la luz varían, los dibujos salen borrosos y los chips fallan." },
        { variable: "step_CMP", rank: 8, descripcion: "Etapa: CMP", importance: 47,
          explicacion: "CMP (Planarización Químico-Mecánica) es como lijar y pulir una mesa hasta dejarla perfectamente plana. En chips, la superficie debe ser tan lisa que no haya desniveles mayores que unos pocos nanómetros." },
        { variable: "step_Oxidation", rank: 9, descripcion: "Etapa: Oxidación", importance: 42,
          explicacion: "La oxidación crea una capa protectora de 'cristal' sobre el silicio, similar a cómo el óxido protege el acero inoxidable. Esta capa aísla eléctricamente las partes del circuito para que no se interfieran entre sí." },
        { variable: "voltage_v", rank: 10, descripcion: "Voltaje de operación", importance: 39,
          explicacion: "El voltaje es la 'fuerza' que empuja a los electrones. Es como la presión del agua en una manguera: suficiente para que fluya, pero no tanta que reviente. En semiconductores, un voltaje inestable provoca cortocircuitos invisibles." },
        { variable: "gas_flow_sccm", rank: 11, descripcion: "Flujo de gas", importance: 34,
          explicacion: "Los gases especiales (como silano o cloro) se inyectan para depositar o grabar materiales. Es como regular el oxígeno de una soldadura: la cantidad exacta determina si la reacción es limpia o deja impurezas." },
        { variable: "step_Etching", rank: 12, descripcion: "Etapa: Grabado", importance: 32,
          explicacion: "El grabado elimina material con precisión atómica usando plasma o ácidos. Es como esculpir en piedra con un hilo de agua: la técnica es brutalmente precisa, y cualquier variación destruye el patrón del circuito." },
        { variable: "potencia_w", rank: 13, descripcion: "Potencia eléctrica derivada", importance: 31,
          explicacion: "La potencia (voltaje × corriente) indica cuánta energía total consume el proceso. Es como la potencia de una estufa: demasiada quema el material, muy poca no logra la reacción. Se calcula automáticamente del voltaje y la corriente." },
    ]
};
