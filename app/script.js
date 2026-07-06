/**
 * AgriGuard - Secure AI Agricultural Advisor
 * Dashboard Logic & Data Visualization
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- UI Elements ---
    const form = document.getElementById('agri-form');
    const resultsPanel = document.getElementById('results-panel');
    const resultContent = document.getElementById('result-content');
    const emptyState = document.getElementById('empty-state');
    const loadingState = document.getElementById('loading-state');
    const submitBtn = document.getElementById('submit-btn');
    
    // Result Text Elements
    const reportText = document.getElementById('report-text');
    const sigHash = document.getElementById('sig-hash');
    const certSig = document.getElementById('cert-sig');
    const piiList = document.getElementById('pii-list');
    const piiBadge = document.getElementById('pii-count-badge');

    // Chart instances (stored in an object to manage destruction/re-rendering)
    let charts = {
        nutrient: null,
        water: null,
        fert: null
    };

    /**
     * 1. STAT COUNTER ANIMATION
     * Animates the numbers in the top stat strip on page load
     */
    const animateCounters = () => {
        document.querySelectorAll('.stat-n').forEach(counter => {
            const target = +counter.getAttribute('data-target');
            const duration = 1500; 
            const increment = target / (duration / 16); 

            const updateCount = () => {
                const count = +counter.innerText.replace('%', '');
                if (count < target) {
                    counter.innerText = Math.ceil(count + increment) + (target === 100 ? "%" : "");
                    setTimeout(updateCount, 16);
                } else {
                    counter.innerText = target + (target === 100 ? "%" : "");
                }
            };
            updateCount();
        });
    };
    animateCounters();

    /**
     * 2. TAB NAVIGATION
     */
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            
            tab.classList.add('active');
            const target = tab.getAttribute('data-tab');
            document.getElementById(`tab-${target}`).classList.add('active');
        });
    });

    /**
     * 3. DYNAMIC SLIDER DISPLAYS
     * Updates labels as user moves NPK and pH sliders
     */
    const sliderInputs = [
        { id: 'current_n', display: 'n-val' },
        { id: 'current_p', display: 'p-val' },
        { id: 'current_k', display: 'k-val' },
        { id: 'current_ph', display: 'ph-display' }
    ];

    sliderInputs.forEach(item => {
        const input = document.getElementById(item.id);
        const display = document.getElementById(item.display);
        
        if (input && display) {
            input.addEventListener('input', (e) => {
                const val = e.target.value;
                if (item.id === 'current_ph') {
                    display.innerText = `pH = ${val}`;
                    const badge = document.getElementById('ph-badge');
                    if (val < 6) badge.innerText = "Acidic";
                    else if (val > 8) badge.innerText = "Alkaline";
                    else badge.innerText = "Optimal Range";
                } else {
                    display.innerText = val;
                }
            });
        }
    });

    /**
     * 4. FORM SUBMISSION & API CALL
     */
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Show Loading State
        emptyState.classList.add('hidden');
        resultContent.classList.add('hidden');
        loadingState.classList.remove('hidden');
        submitBtn.disabled = true;

        const payload = {
            user_query: document.getElementById('user_query').value,
            crop_name: document.getElementById('crop_name').value,
            current_n: parseFloat(document.getElementById('current_n').value),
            current_p: parseFloat(document.getElementById('current_p').value),
            current_k: parseFloat(document.getElementById('current_k').value),
            current_ph: parseFloat(document.getElementById('current_ph').value),
            region_id: document.getElementById('region_id').value || null
        };

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error("API Connection Error");

            const data = await response.json();

            // Populate Report
            reportText.innerText = data.advisory_report;
            sigHash.innerText = data.digital_signature;
            certSig.innerText = data.digital_signature;
            piiBadge.innerText = `${data.redacted_pii?.length || 0} items secured`;

            // Populate KPI Cards
            document.getElementById('kpi-cost').innerText = `$${data.fertilizer_plan?.total_cost_estimate || '0.00'}`;
            document.getElementById('kpi-water').innerText = data.irrigation_plan?.net_irrigation_depth_mm?.toFixed(1) || '—';
            document.getElementById('kpi-zone').innerText = data.metadata?.resolved_region || 'Detected';
            document.getElementById('kpi-suit').innerText = (payload.current_ph > 6 && payload.current_ph < 7.5) ? "High" : "Moderate";

            // Security Logs
            piiList.innerHTML = '';
            if (data.redacted_pii && data.redacted_pii.length > 0) {
                data.redacted_pii.forEach(item => {
                    const li = document.createElement('li');
                    li.style.display = "flex";
                    li.style.justifyContent = "space-between";
                    li.style.marginBottom = "8px";
                    li.innerHTML = `<span>Scoured sensitive ${item[0]}</span><code style="color:#2e7d32">[REDACTED]</code>`;
                    piiList.appendChild(li);
                });
            } else {
                piiList.innerHTML = '<li style="color:#2e7d32">✅ No sensitive personal data detected.</li>';
            }

            // Render All Charts
            renderCharts(payload, data);

            // Show Results
            loadingState.classList.add('hidden');
            resultContent.classList.remove('hidden');

        } catch (error) {
            console.error(error);
            alert("Analysis failed. Ensure your backend is running.");
            loadingState.classList.add('hidden');
            emptyState.classList.remove('hidden');
        } finally {
            submitBtn.disabled = false;
        }
    });

    /**
     * 5. CHART.JS RENDERING LOGIC
     */
    function renderCharts(input, output) {
        
        // --- 5a. Nutrient Radar ---
        const ctxNutrient = document.getElementById('nutrientChart').getContext('2d');
        if (charts.nutrient) charts.nutrient.destroy();

        const nGain = (output.fertilizer_plan?.urea_kg * 0.46) + (output.fertilizer_plan?.dap_kg * 0.18) || 0;
        const pGain = (output.fertilizer_plan?.dap_kg * 0.46) || 0;
        const kGain = (output.fertilizer_plan?.mop_kg * 0.60) || 0;

        charts.nutrient = new Chart(ctxNutrient, {
            type: 'radar',
            data: {
                labels: ['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)'],
                datasets: [{
                    label: 'Current Soil',
                    data: [input.current_n, input.current_p, input.current_k],
                    backgroundColor: 'rgba(244, 67, 54, 0.2)',
                    borderColor: '#f44336',
                    pointBackgroundColor: '#f44336'
                }, {
                    label: 'Target (Post-Fertilizer)',
                    data: [input.current_n + nGain, input.current_p + pGain, input.current_k + kGain],
                    backgroundColor: 'rgba(46, 125, 50, 0.2)',
                    borderColor: '#2e7d32',
                    pointBackgroundColor: '#2e7d32'
                }]
            },
            options: { scales: { r: { beginAtZero: true } }, plugins: { legend: { position: 'bottom' } } }
        });

        // --- 5b. Water Line Chart ---
        const ctxWater = document.getElementById('waterChart').getContext('2d');
        if (charts.water) charts.water.destroy();

        const et0 = output.irrigation_plan?.et0_mm_day || 5;
        const etc = output.irrigation_plan?.etc_mm_day || 6;

        charts.water = new Chart(ctxWater, {
            type: 'line',
            data: {
                labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
                datasets: [{
                    label: 'Crop Need (mm)',
                    data: Array(7).fill(etc),
                    borderColor: '#00bcd4',
                    backgroundColor: 'rgba(0, 188, 212, 0.1)',
                    fill: true,
                    tension: 0.3
                }, {
                    label: 'Reference ET0',
                    data: Array(7).fill(et0),
                    borderColor: '#9e9e9e',
                    borderDash: [5, 5],
                    tension: 0.3
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
        });

        // --- 5c. Fertilizer Mix (Horizontal Bar) ---
        const ctxFert = document.getElementById('fertChart').getContext('2d');
        if (charts.fert) charts.fert.destroy();

        charts.fert = new Chart(ctxFert, {
            type: 'bar',
            data: {
                labels: ['Urea (N)', 'DAP (N-P)', 'MOP (K)'],
                datasets: [{
                    label: 'kg per Hectare',
                    data: [
                        output.fertilizer_plan?.urea_kg || 0,
                        output.fertilizer_plan?.dap_kg || 0,
                        output.fertilizer_plan?.mop_kg || 0
                    ],
                    backgroundColor: ['#4caf50', '#ff9800', '#2196f3'],
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true } }
            }
        });
    }
});
