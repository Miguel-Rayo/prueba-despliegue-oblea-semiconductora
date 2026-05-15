// ============================================================
// WAFER VISUALIZATION (Real Images)
// Controla el estado visual de la oblea con imágenes reales
// ============================================================

const WaferViz = {
    img: null,
    frame: null,
    statusText: null,
    container: null,

    // Rutas de imágenes (ajustar si cambian las carpetas)
    IMAGES: {
        perfecta:     'assets/variaciones-oblea/oblea-perfecta.png',
        parcial:      'assets/variaciones-oblea/oblea-destruida-parcialmente.png',
        medio:        'assets/variaciones-oblea/oblea-destruida-termino-medio.png',
        critica:      'assets/variaciones-oblea/oblea-destruida-rota-carbonizada.png',
    },

    init() {
        this.img = document.getElementById('wafer-img');
        this.frame = document.getElementById('wafer-img-frame');
        this.statusText = document.getElementById('wafer-status-text');
        this.container = document.querySelector('.wafer-image-wrap');
        this.reset();
    },

    reset() {
        this._clearStates();
        this._setImage(this.IMAGES.perfecta);
        if (this.statusText) this.statusText.textContent = 'ESPERANDO PARÁMETROS';
    },

    setAnalizando() {
        this._clearStates();
        if (this.statusText) {
            this.statusText.textContent = 'ANALIZANDO...';
            this.statusText.className = 'wafer-status-text';
        }
    },

    setNormal(confianza) {
        this._clearStates();
        this._addState('state-normal');
        this._setImage(this.IMAGES.perfecta);
        if (this.statusText) {
            this.statusText.textContent = `OBLEA NORMAL — ${(confianza * 100).toFixed(1)}%`;
            this.statusText.className = 'wafer-status-text state-normal';
        }
    },

    setDefectuosa(confianza) {
        this._clearStates();
        let imgPath = this.IMAGES.parcial;
        let stateClass = 'state-defect-light';

        if (confianza > 0.90) {
            imgPath = this.IMAGES.critica;
            stateClass = 'state-defect-critical';
        } else if (confianza > 0.70) {
            imgPath = this.IMAGES.medio;
            stateClass = 'state-defect-medium';
        } else if (confianza > 0.50) {
            imgPath = this.IMAGES.parcial;
            stateClass = 'state-defect-light';
        }

        this._addState(stateClass);
        this._setImage(imgPath);
        if (this.statusText) {
            this.statusText.textContent = `DEFECTO DETECTADO — ${(confianza * 100).toFixed(1)}%`;
            this.statusText.className = 'wafer-status-text state-defect';
        }
    },

    // Internos
    _clearStates() {
        if (!this.container) return;
        this.container.classList.remove(
            'state-normal', 'state-defect-light',
            'state-defect-medium', 'state-defect-critical'
        );
    },

    _addState(cls) {
        if (this.container) this.container.classList.add(cls);
    },

    _setImage(src) {
        if (!this.img) return;
        // Precarga suave: fade-out, cambio, fade-in
        this.img.style.opacity = '0.7';
        setTimeout(() => {
            this.img.src = src;
            this.img.onload = () => { this.img.style.opacity = '1'; };
            // Fallback si ya está cacheada
            if (this.img.complete) this.img.style.opacity = '1';
        }, 150);
    }
};
