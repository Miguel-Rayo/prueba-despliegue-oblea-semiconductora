// ============================================================
// MAIN — Orquestación
// ============================================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('SWAL Semiconductors Web Service iniciado');

    UI.init();
    WaferViz.init();
    inicializarValidacion();
    inicializarStepSelector();
    inicializarParticulas();

    // Asegurar estado limpio del botón al cargar
    UI.setLoading(false);

    // Cargar datos del backend
    try {
        const health = await fetchHealth();
        console.log('Health:', health);
        if (health.modelo_cargado) {
            console.log('Modelo PMML cargado y listo');
        } else {
            console.warn('Modelo no cargado:', health.mensaje);
        }
    } catch (e) {
        console.warn('No se pudo conectar con el backend. Verifique que el servidor esté corriendo.');
    }

    // Cargar importancia de variables para el gráfico
    try {
        const vars = await fetchImportancia();
        UI.renderVariablesCarousel(vars);
    } catch (e) {
        // Fallback estático
        UI.renderVariablesCarousel(CONFIG.IMPORTANCIA_FALLBACK || []);
    }

    // Handler de formulario
    const form = document.getElementById('prediction-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await handlePrediccion();
        });
    }
});

function inicializarStepSelector() {
    const selector = document.getElementById('step-selector');
    const hidden = document.getElementById('process_step');
    if (!selector) return;

    const chips = selector.querySelectorAll('.step-chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            chips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            if (hidden) hidden.value = chip.dataset.value;
            actualizarFlowTimeline(chip.dataset.value);
        });
    });

    // Inicializar timeline con el valor por defecto
    const activeChip = selector.querySelector('.step-chip.active');
    if (activeChip) actualizarFlowTimeline(activeChip.dataset.value);
}

function actualizarFlowTimeline(stepValue) {
    const flow = document.getElementById('process-flow');
    if (!flow) return;

    const steps = ['CMP', 'Deposition', 'Lithography', 'Etching', 'Oxidation'];
    const idx = steps.indexOf(stepValue);

    flow.querySelectorAll('.flow-step').forEach((el, i) => {
        el.classList.remove('active', 'completed');
        if (i === idx) {
            el.classList.add('active');
        } else if (i < idx) {
            el.classList.add('completed');
        }
    });
}

async function handlePrediccion() {
    Validador.limpiarErrores();

    const datos = {
        temperature_c:    parseFloat(document.getElementById('temperature_c').value),
        pressure_torr:    parseFloat(document.getElementById('pressure_torr').value),
        gas_flow_sccm:    parseFloat(document.getElementById('gas_flow_sccm').value),
        etch_rate_nm_min: parseFloat(document.getElementById('etch_rate_nm_min').value),
        voltage_v:        parseFloat(document.getElementById('voltage_v').value),
        current_ma:       parseFloat(document.getElementById('current_ma').value),
        process_step:     document.getElementById('process_step').value,
    };

    if (!Validador.validarTodo(datos)) {
        Validador.mostrarErroresActuales();
        UI.mostrarErrorGlobal('Corrija los errores en el formulario antes de continuar.');
        return;
    }

    UI.setLoading(true);
    UI.hideResults();
    WaferViz.setAnalizando();

    // Feedback temprano si el servidor está en cold start (Render Free)
    let wakingToastTimer = setTimeout(() => {
        UI.mostrarInfoGlobal('El servidor está despertando, reintentando conexión...', 0);
    }, 2500);

    try {
        const resultado = await enviarPrediccion(datos);
        clearTimeout(wakingToastTimer);
        UI.ocultarInfoGlobal();
        console.log('Resultado:', resultado);

        WaferViz[resultado.es_defectuosa ? 'setDefectuosa' : 'setNormal'](resultado.probabilidad);
        UI.showResults(resultado);
    } catch (e) {
        clearTimeout(wakingToastTimer);
        UI.ocultarInfoGlobal();
        console.error('Error en predicción:', e);
        UI.mostrarErrorGlobal(`Error: ${e.message}`);
        WaferViz.reset();
    } finally {
        UI.setLoading(false);
    }
}

// Partículas canvas sutiles (fotones / polvo cleanroom)
function inicializarParticulas() {
    const canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let width, height;
    const particulas = [];
    const N = 60;

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    for (let i = 0; i < N; i++) {
        particulas.push({
            x: Math.random() * width,
            y: Math.random() * height,
            r: Math.random() * 1.5 + 0.5,
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
            alpha: Math.random() * 0.5 + 0.1,
            color: Math.random() > 0.5 ? '157,78,221' : '0,180,216'
        });
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);
        for (const p of particulas) {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0) p.x = width;
            if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            if (p.y > height) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${p.color}, ${p.alpha})`;
            ctx.fill();
        }
        requestAnimationFrame(animate);
    }
    animate();
}
