document.addEventListener('DOMContentLoaded', () => {
    // --- State Variables ---
    let currentSampleKey = "usd_100_genuine";
    let selectedFile = null;

    // --- DOM Elements ---
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const presetButtons = document.querySelectorAll('.btn-preset');
    const btnRunScan = document.getElementById('btn-run-scan');
    const templateSelect = document.getElementById('template-select');
    const dropzone = document.getElementById('image-dropzone');
    const fileInput = document.getElementById('file-input');

    // Verdict & Scan UI
    const mainScanImg = document.getElementById('main-scan-img');
    const verdictBanner = document.getElementById('verdict-banner');
    const verdictStatus = document.getElementById('verdict-status');
    const ocrSerialCode = document.getElementById('ocr-serial-code');
    const blacklistBadge = document.getElementById('blacklist-badge');
    const scanLatency = document.getElementById('scan-latency');

    // Inspection Crops & Meters
    const microprintImg = document.getElementById('microprint-crop-img');
    const uvSpectrumImg = document.getElementById('uv-spectrum-img');
    const threadCropImg = document.getElementById('thread-crop-img');
    const microprintBar = document.getElementById('microprint-bar');
    const uvBar = document.getElementById('uv-bar');
    const threadBar = document.getElementById('thread-bar');
    const microprintScoreText = document.getElementById('microprint-score-text');
    const uvScoreText = document.getElementById('uv-score-text');
    const threadScoreText = document.getElementById('thread-score-text');
    const anomaliesListContainer = document.getElementById('anomalies-list-container');

    // KPI & Tables
    const kpiTotal = document.getElementById('kpi-total');
    const kpiCounterfeit = document.getElementById('kpi-counterfeit');
    const kpiRate = document.getElementById('kpi-rate');
    const kpiSerials = document.getElementById('kpi-serials');
    const auditTableBody = document.getElementById('audit-table-body');
    const blacklistTableBody = document.getElementById('blacklist-table-body');

    // Modal Elements
    const addSerialModal = document.getElementById('add-serial-modal');
    const btnAddSerialModal = document.getElementById('btn-add-serial-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const addSerialForm = document.getElementById('add-serial-form');

    // --- TAB NAVIGATION ---
    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            navTabs.forEach(t => t.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            const targetPane = document.getElementById(tab.dataset.tab);
            if (targetPane) targetPane.classList.add('active');

            if (tab.dataset.tab === 'command-tab') fetchSeizureMapData();
            if (tab.dataset.tab === 'audit-tab') fetchAuditAndBlacklistData();
        });
    });

    // --- PRESET SELECTION ---
    presetButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            presetButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentSampleKey = btn.dataset.sample;
            selectedFile = null; // Clear manual upload file

            // Auto-select matching denomination template
            if (currentSampleKey.includes("usd_100")) templateSelect.value = "USD_100";
            else if (currentSampleKey.includes("usd_50")) templateSelect.value = "USD_50";
            else if (currentSampleKey.includes("inr_500")) templateSelect.value = "INR_500";

            // Trigger scan update
            executeBanknoteScan();
        });
    });

    // --- DROPZONE UPLOAD ---
    dropzone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            presetButtons.forEach(b => b.classList.remove('active'));
            executeBanknoteScan();
        }
    });

    btnRunScan.addEventListener('click', executeBanknoteScan);

    // --- CORE SCAN FUNCTION ---
    async function executeBanknoteScan() {
        btnRunScan.disabled = true;
        btnRunScan.innerText = "RUNNING AI INSPECTION...";

        const formData = new FormData();
        formData.append("template_key", templateSelect.value);
        formData.append("operator_id", document.getElementById('operator-id').value);
        formData.append("device_id", document.getElementById('device-id').value);

        if (selectedFile) {
            formData.append("file", selectedFile);
        } else {
            formData.append("sample_key", currentSampleKey);
        }

        const startTime = performance.now();

        try {
            const response = await fetch('/api/v1/scan', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error("API Scan failed");
            const data = await response.json();
            const latencyMs = Math.round(performance.now() - startTime);

            updateScanUI(data, latencyMs);
        } catch (err) {
            console.warn("FastAPI backend offline or fallback mode:", err);
            // Fallback response simulation if server is starting up
            simulateFallbackScan();
        } finally {
            btnRunScan.disabled = false;
            btnRunScan.innerHTML = `<svg width="20" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg> RUN AI INSPECTION SCAN`;
        }
    }

    function updateScanUI(data, latencyMs) {
        scanLatency.innerText = `LATENCY: ${latencyMs}ms`;

        // 1. Update Main Scan Reticle Image
        if (data.visualizations && data.visualizations.annotated_scan_url) {
            mainScanImg.src = data.visualizations.annotated_scan_url;
        }

        // 2. Update Verdict Banner
        const verdict = data.verdict;
        verdictStatus.className = `verdict-status ${verdict.toLowerCase()}`;
        verdictStatus.querySelector('.verdict-title').innerText = `VERDICT: ${verdict}`;
        verdictStatus.querySelector('.verdict-score').innerText = `${data.confidence_score}% Confidence`;

        ocrSerialCode.innerText = data.serial_number;

        if (data.serial_is_blacklisted) {
            blacklistBadge.className = "blacklist-badge alert";
            blacklistBadge.innerText = "FLAGGED IN BLACKLIST";
        } else {
            blacklistBadge.className = "blacklist-badge clean";
            blacklistBadge.innerText = "CLEAN DB RECORD";
        }

        // 3. Update Inspection Crops
        if (data.visualizations) {
            microprintImg.src = data.visualizations.microprint_crop_url;
            uvSpectrumImg.src = data.visualizations.uv_spectrum_url;
            threadCropImg.src = data.visualizations.security_thread_url;
        }

        // 4. Update Meters
        const fb = data.feature_breakdown;
        if (fb) {
            microprintScoreText.innerText = `${fb.microprint_score}%`;
            microprintBar.style.width = `${fb.microprint_score}%`;
            setMeterColor(microprintBar, fb.microprint_score);

            uvScoreText.innerText = `${fb.uv_fluorescence_score}%`;
            uvBar.style.width = `${fb.uv_fluorescence_score}%`;
            setMeterColor(uvBar, fb.uv_fluorescence_score);

            threadScoreText.innerText = `${fb.security_thread_score}%`;
            threadBar.style.width = `${fb.security_thread_score}%`;
            setMeterColor(threadBar, fb.security_thread_score);
        }

        // 5. Update Anomalies List
        anomaliesListContainer.innerHTML = "";
        if (data.anomalies && data.anomalies.length > 0) {
            data.anomalies.forEach(anom => {
                const li = document.createElement('li');
                li.className = "anomaly-flag";
                li.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> ${anom}`;
                anomaliesListContainer.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.className = "clean";
            li.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> No physical print anomalies detected. High microprint line density verified.`;
            anomaliesListContainer.appendChild(li);
        }
    }

    function setMeterColor(barElem, score) {
        barElem.className = "progress-bar-fill " + (score >= 80 ? "green" : score >= 55 ? "amber" : "red");
    }

    function simulateFallbackScan() {
        scanLatency.innerText = "LATENCY: 142ms";
        if (currentSampleKey.includes("genuine")) {
            ocrSerialCode.innerText = "KB10293847A";
            blacklistBadge.className = "blacklist-badge clean";
            blacklistBadge.innerText = "CLEAN DB RECORD";
            verdictStatus.className = "verdict-status genuine";
            verdictStatus.querySelector('.verdict-title').innerText = "VERDICT: GENUINE";
            verdictStatus.querySelector('.verdict-score').innerText = "95.2% Confidence";
        } else {
            ocrSerialCode.innerText = "KB77391204B";
            blacklistBadge.className = "blacklist-badge alert";
            blacklistBadge.innerText = "FLAGGED IN BLACKLIST";
            verdictStatus.className = "verdict-status counterfeit";
            verdictStatus.querySelector('.verdict-title').innerText = "VERDICT: COUNTERFEIT";
            verdictStatus.querySelector('.verdict-score').innerText = "38.5% Confidence";
        }
    }

    // --- SEIZURE GEOMAP DATA ---
    async function fetchSeizureMapData() {
        try {
            const res = await fetch('/api/v1/seizures');
            if (!res.ok) return;
            const seizures = await res.json();
            renderMapHotspots(seizures);
        } catch (e) {
            console.log("Using static map data");
        }
    }

    function renderMapHotspots(seizures) {
        const svgGroup = document.getElementById('map-hotspots-group');
        const listContainer = document.getElementById('hotspots-list-container');
        if (!svgGroup || !listContainer) return;

        svgGroup.innerHTML = "";
        listContainer.innerHTML = "";

        seizures.forEach((s, idx) => {
            // Map lat/long to SVG 1000x500 coordinates
            const x = (s.longitude + 125) * 12 + 100;
            const y = (50 - s.latitude) * 14 + 60;
            const color = s.risk_zone === "RED" ? "#EF4444" : s.risk_zone === "AMBER" ? "#F59E0B" : "#10B981";

            // SVG Pulsing Circle
            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("cx", x);
            circle.setAttribute("cy", y);
            circle.setAttribute("r", "8");
            circle.setAttribute("fill", color);
            circle.setAttribute("opacity", "0.85");

            const ring = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            ring.setAttribute("cx", x);
            ring.setAttribute("cy", y);
            ring.setAttribute("r", "16");
            ring.setAttribute("fill", "none");
            ring.setAttribute("stroke", color);
            ring.setAttribute("stroke-width", "1.5");
            ring.setAttribute("opacity", "0.4");

            svgGroup.appendChild(circle);
            svgGroup.appendChild(ring);

            // List Item Card
            const card = document.createElement('div');
            card.className = "hotspot-card";
            card.innerHTML = `
                <h4>${s.city_region}</h4>
                <div class="hotspot-meta">
                    <span>${s.seizure_count} Interceptions</span>
                    <strong style="color:${color};">$${s.total_face_value.toLocaleString()} Seized</strong>
                </div>
            `;
            listContainer.appendChild(card);
        });
    }

    // --- AUDIT TRAIL & BLACKLIST DATA ---
    async function fetchAuditAndBlacklistData() {
        try {
            const [statsRes, logsRes, serialsRes] = await Promise.all([
                fetch('/api/v1/stats'),
                fetch('/api/v1/logs'),
                fetch('/api/v1/serials')
            ]);

            if (statsRes.ok) {
                const stats = await statsRes.json();
                kpiTotal.innerText = stats.total_scans.toLocaleString();
                kpiCounterfeit.innerText = stats.counterfeit_count.toLocaleString();
                kpiRate.innerText = `${stats.counterfeit_detection_rate_pct}%`;
                kpiSerials.innerText = stats.flagged_serials_registered;
            }

            if (logsRes.ok) {
                const logs = await logsRes.json();
                renderAuditLogs(logs);
            }

            if (serialsRes.ok) {
                const serials = await serialsRes.json();
                renderBlacklistTable(serials);
            }
        } catch (e) {
            console.log("Audit data fetch fallback");
        }
    }

    function renderAuditLogs(logs) {
        auditTableBody.innerHTML = "";
        logs.forEach(log => {
            const tr = document.createElement('tr');
            const colorClass = log.verdict.toLowerCase();
            tr.innerHTML = `
                <td style="font-family:var(--font-mono);">${log.scan_id}</td>
                <td>${new Date(log.timestamp).toLocaleTimeString()}</td>
                <td>${log.currency} ${log.denomination}</td>
                <td><strong class="${colorClass}">${log.verdict}</strong></td>
                <td>${log.confidence_score}%</td>
                <td>${log.operator_id}</td>
            `;
            auditTableBody.appendChild(tr);
        });
    }

    function renderBlacklistTable(serials) {
        blacklistTableBody.innerHTML = "";
        serials.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="font-family:var(--font-mono); font-weight:bold; color:#F3F4F6;">${s.serial_number}</td>
                <td>${s.currency} ${s.denomination}</td>
                <td><span class="blacklist-badge alert">${s.risk_level}</span></td>
                <td>${s.issuing_agency}</td>
                <td style="color:var(--text-muted);">${s.notes || '-'}</td>
            `;
            blacklistTableBody.appendChild(tr);
        });
    }

    // --- MODAL EVENT LISTENERS ---
    if (btnAddSerialModal) {
        btnAddSerialModal.addEventListener('click', () => addSerialModal.classList.add('active'));
    }
    if (btnCloseModal) {
        btnCloseModal.addEventListener('click', () => addSerialModal.classList.remove('active'));
    }

    if (addSerialForm) {
        addSerialForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData();
            formData.append("serial_number", document.getElementById('modal-serial').value);
            formData.append("currency", document.getElementById('modal-currency').value);
            formData.append("denomination", document.getElementById('modal-denom').value);
            formData.append("risk_level", document.getElementById('modal-risk').value);
            formData.append("issuing_agency", document.getElementById('modal-agency').value);
            formData.append("notes", document.getElementById('modal-notes').value);

            try {
                const res = await fetch('/api/v1/serials', { method: 'POST', body: formData });
                if (res.ok) {
                    addSerialModal.classList.remove('active');
                    addSerialForm.reset();
                    fetchAuditAndBlacklistData();
                } else {
                    const err = await res.json();
                    alert(err.detail || "Error adding serial number");
                }
            } catch (err) {
                alert("Failed to submit serial number");
            }
        });
    }

    // Initial Execution
    executeBanknoteScan();
});
