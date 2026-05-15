// ============================================================
// UI MANAGER — Dashboard Premium de Resultados
// ============================================================

const UI = {
    form: null,
    btnLaunch: null,
    btnText: null,
    btnLoader: null,
    resultsPanel: null,
    systemStatus: null,

    init() {
        this.form = document.getElementById('prediction-form');
        this.btnLaunch = document.getElementById('btn-launch');
        this.btnText = this.btnLaunch?.querySelector('.btn-text');
        this.btnLoader = this.btnLaunch?.querySelector('.btn-loader');
        this.resultsPanel = document.getElementById('results-panel');
        this.systemStatus = document.getElementById('system-status');
    },

    setLoading(loading) {
        if (!this.btnLaunch) return;
        this.btnLaunch.disabled = loading;
        if (this.btnText) this.btnText.hidden = loading;
        if (this.btnLoader) this.btnLoader.hidden = !loading;
        if (this.systemStatus) {
            this.systemStatus.innerHTML = loading
                ? '<span style="color:#c77dff">● Analizando...</span>'
                : '<span style="color:#2ec4b6">● Sistema Listo</span>';
        }
    },

    showResults(data) {
        if (!this.resultsPanel) return;
        this.resultsPanel.hidden = false;
        this.resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        const esDefecto = data.es_defectuosa;
        const conf = (data.probabilidad * 100).toFixed(1);

        // Header
        const badgeLabel = document.getElementById('badge-label');
        const badgeConfidence = document.getElementById('badge-confidence');
        const headerIcon = document.getElementById('dash-header-icon');
        const dashHeader = document.getElementById('dash-header');

        if (badgeLabel) {
            badgeLabel.textContent = esDefecto ? 'DEFECTUOSA' : 'NORMAL';
            badgeLabel.className = 'dash-header-badge ' + (esDefecto ? 'defect' : 'normal');
        }
        if (badgeConfidence) {
            badgeConfidence.textContent = `${conf}% confianza del modelo`;
        }
        if (headerIcon) {
            headerIcon.textContent = esDefecto ? '!' : '✓';
            headerIcon.className = 'dash-header-icon ' + (esDefecto ? 'defect' : 'normal');
        }
        if (dashHeader) {
            dashHeader.className = 'dash-header ' + (esDefecto ? 'defect' : 'normal');
        }

        // Anillos de probabilidad
        const ringNormal = document.getElementById('ring-normal');
        const ringDefect = document.getElementById('ring-defect');
        const ringNormalVal = document.getElementById('ring-normal-value');
        const ringDefectVal = document.getElementById('ring-defect-value');

        const pNormal = data.prob_normal * 100;
        const pDefect = data.prob_defectuosa * 100;
        const circ = 263.89;

        if (ringNormal) {
            const off = circ * (1 - pNormal / 100);
            ringNormal.style.strokeDashoffset = off;
            ringNormal.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.22,1,0.36,1)';
        }
        if (ringDefect) {
            const off = circ * (1 - pDefect / 100);
            ringDefect.style.strokeDashoffset = off;
            ringDefect.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.22,1,0.36,1)';
        }
        if (ringNormalVal) this._animateNumber(ringNormalVal, 0, pNormal, 1000, '%');
        if (ringDefectVal) this._animateNumber(ringDefectVal, 0, pDefect, 1000, '%');

        // Z-Scores — Grid de medidores
        const zList = document.getElementById('zscore-list');
        if (zList) {
            zList.innerHTML = '';
            const vars = [
                ['temperature_c', 'Temperatura', '°C'],
                ['pressure_torr', 'Presión', 'Torr'],
                ['gas_flow_sccm', 'Flujo de Gas', 'sccm'],
                ['etch_rate_nm_min', 'Tasa de Grabado', 'nm/min'],
                ['voltage_v', 'Voltaje', 'V'],
                ['current_ma', 'Corriente', 'mA'],
                ['potencia_w', 'Potencia', 'W'],
                ['anomaly_score', 'Anomalía', 'score'],
            ];
            for (const [key, label, unit] of vars) {
                const z = data.z_scores[key] || 0;
                const absZ = Math.abs(z);
                const isCritical = absZ >= 2.0;
                const isWarning = absZ >= 1.0 && !isCritical;
                const isPositive = z >= 0;

                const item = document.createElement('div');
                item.className = 'dash-zscore-item';

                let severityClass = 'ok';
                if (isCritical) severityClass = 'critical';
                else if (isWarning) severityClass = 'warning';

                const barWidth = Math.min(absZ / 3 * 100, 100);
                const barSide = isPositive ? 'right' : 'left';

                item.innerHTML = `
                    <div class="dash-zscore-info">
                        <span class="dash-zscore-name">${label}</span>
                        <span class="dash-zscore-unit">${unit}</span>
                    </div>
                    <div class="dash-zscore-meter">
                        <div class="dash-zscore-track">
                            <div class="dash-zscore-fill ${severityClass}" style="width:${barWidth}%;${barSide==='left'?'right:auto;left:0;':''}"></div>
                        </div>
                        <span class="dash-zscore-value ${severityClass}">${z > 0 ? '+' : ''}${z.toFixed(2)}</span>
                    </div>
                `;
                zList.appendChild(item);
            }
        }

        // Feedback — Terminal
        const feedbackText = document.getElementById('feedback-text');
        if (feedbackText) {
            feedbackText.innerHTML = data.retroalimentacion
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br>');
        }
    },

    hideResults() {
        if (this.resultsPanel) this.resultsPanel.hidden = true;
    },

    // Carrusel de variables (Sección 4) — 4 cards por slide
    renderVariablesCarousel(variables) {
        const container = document.getElementById('variables-chart');
        if (!container || !variables) return;

        const sorted = [...variables].sort((a, b) => (a.rank || 0) - (b.rank || 0));
        const maxImportance = sorted[0]?.importance || 1;

        container.innerHTML = '';

        // Wrapper principal
        const wrapper = document.createElement('div');
        wrapper.className = 'var-carousel-wrapper';

        // Track con slides
        const track = document.createElement('div');
        track.className = 'var-carousel-track';
        track.id = 'var-carousel-track';

        // Agrupar en slides de 4
        const slides = [];
        for (let i = 0; i < sorted.length; i += 4) {
            slides.push(sorted.slice(i, i + 4));
        }

        slides.forEach((group, slideIdx) => {
            const slide = document.createElement('div');
            slide.className = 'var-carousel-slide';

            group.forEach((v, idx) => {
                const pct = ((v.importance || 0) / maxImportance * 100).toFixed(1);
                const card = document.createElement('div');
                card.className = 'var-carousel-card';
                card.style.animationDelay = `${idx * 0.1}s`;
                card.innerHTML = `
                    <div class="var-carousel-rank">#${v.rank}</div>
                    <div class="var-carousel-body">
                        <h5 class="var-carousel-name">${v.descripcion || v.variable}</h5>
                        <p class="var-carousel-desc">${v.explicacion || ''}</p>
                        <div class="var-carousel-bar-track">
                            <div class="var-carousel-bar-fill" style="width:${pct}%"></div>
                        </div>
                        <span class="var-carousel-value">Importancia: ${(v.importance || 0).toFixed(0)}</span>
                    </div>
                `;
                slide.appendChild(card);
            });

            track.appendChild(slide);
        });

        wrapper.appendChild(track);

        // Dots de navegación
        const dotsNav = document.createElement('div');
        dotsNav.className = 'var-carousel-dots';
        slides.forEach((_, i) => {
            const dot = document.createElement('button');
            dot.className = 'var-carousel-dot' + (i === 0 ? ' active' : '');
            dot.onclick = () => this._goToSlide(track, dotsNav, i);
            dotsNav.appendChild(dot);
        });

        // Flechas
        const leftBtn = document.createElement('button');
        leftBtn.className = 'var-carousel-btn prev';
        leftBtn.innerHTML = '‹';
        leftBtn.onclick = () => this._changeSlide(track, dotsNav, -1);

        const rightBtn = document.createElement('button');
        rightBtn.className = 'var-carousel-btn next';
        rightBtn.innerHTML = '›';
        rightBtn.onclick = () => this._changeSlide(track, dotsNav, 1);

        container.appendChild(leftBtn);
        container.appendChild(wrapper);
        container.appendChild(rightBtn);
        container.appendChild(dotsNav);

        // Guardar estado
        this._carouselState = { track, dotsNav, current: 0, total: slides.length };

        // Touch/swipe support
        let startX = 0;
        track.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, { passive: true });
        track.addEventListener('touchend', e => {
            const dx = e.changedTouches[0].clientX - startX;
            if (Math.abs(dx) > 50) this._changeSlide(track, dotsNav, dx < 0 ? 1 : -1);
        }, { passive: true });
    },

    _changeSlide(track, dotsNav, direction) {
        if (!this._carouselState) return;
        const s = this._carouselState;
        s.current = Math.max(0, Math.min(s.total - 1, s.current + direction));
        this._goToSlide(track, dotsNav, s.current);
    },

    _goToSlide(track, dotsNav, index) {
        if (!this._carouselState) return;
        this._carouselState.current = index;
        const slideWidth = track.querySelector('.var-carousel-slide')?.offsetWidth || track.offsetWidth;
        track.scrollTo({ left: index * slideWidth, behavior: 'smooth' });

        // Actualizar dots
        dotsNav.querySelectorAll('.var-carousel-dot').forEach((d, i) => {
            d.classList.toggle('active', i === index);
        });
    },

    _animateNumber(el, from, to, duration, suffix = '') {
        const start = performance.now();
        const step = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const ease = 1 - Math.pow(1 - progress, 3);
            const val = from + (to - from) * ease;
            el.textContent = val.toFixed(1) + suffix;
            if (progress < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    },

    mostrarErrorGlobal(mensaje) {
        const existing = document.querySelector('.toast-error');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = 'toast-error';
        toast.textContent = mensaje;
        toast.style.cssText = `
            position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
            background: var(--alert-laser); color: #fff; padding: 1rem 2rem;
            border-radius: var(--radius-md); font-weight: 600; z-index: 9999;
            box-shadow: 0 10px 30px rgba(255,0,85,0.3); animation: fadeInUp 0.3s ease;
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    }
};
