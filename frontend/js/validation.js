// ============================================================
// VALIDACIÓN EN TIEMPO REAL
// ============================================================

const Validador = {
    errores: {},

    validarCampo(nombre, valor) {
        const rango = CONFIG.RANGOS[nombre];
        if (!rango) return true;

        const num = parseFloat(valor);
        if (isNaN(num)) {
            this.errores[nombre] = 'Valor numérico requerido';
            return false;
        }
        if (num < rango.min || num > rango.max) {
            this.errores[nombre] = `Debe estar entre ${rango.min} y ${rango.max} ${rango.unit}`;
            return false;
        }
        delete this.errores[nombre];
        return true;
    },

    validarStep(valor) {
        if (!CONFIG.ETAPAS.includes(valor)) {
            this.errores.process_step = 'Seleccione una etapa válida';
            return false;
        }
        delete this.errores.process_step;
        return true;
    },

    validarTodo(datos) {
        let ok = true;
        for (const key of Object.keys(CONFIG.RANGOS)) {
            if (!this.validarCampo(key, datos[key])) ok = false;
        }
        if (!this.validarStep(datos.process_step)) ok = false;
        return ok;
    },

    mostrarError(campo, mensaje) {
        const el = document.getElementById(`error-${campo}`);
        const input = document.getElementById(campo);
        if (el) el.textContent = mensaje || '';
        if (input) input.classList.toggle('invalid', !!mensaje);
    },

    limpiarErrores() {
        for (const key of Object.keys(CONFIG.RANGOS)) {
            this.mostrarError(key, '');
        }
        this.mostrarError('process_step', '');
        this.errores = {};
    },

    mostrarErroresActuales() {
        for (const [campo, msg] of Object.entries(this.errores)) {
            this.mostrarError(campo, msg);
        }
    }
};

function sincronizarSliderYNumero(numId, rangeId) {
    const num = document.getElementById(numId);
    const range = document.getElementById(rangeId);
    if (!num || !range) return;

    num.addEventListener('input', () => {
        range.value = num.value;
        Validador.validarCampo(numId, num.value);
        Validador.mostrarError(numId, Validador.errores[numId]);
    });
    range.addEventListener('input', () => {
        num.value = range.value;
        Validador.validarCampo(numId, range.value);
        Validador.mostrarError(numId, Validador.errores[numId]);
    });
}

function inicializarValidacion() {
    const campos = Object.keys(CONFIG.RANGOS);
    for (const campo of campos) {
        sincronizarSliderYNumero(campo, `${campo}_range`);
    }
}
