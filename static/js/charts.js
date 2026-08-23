// ==========================================
// INTERACTIVE CHARTS
// ==========================================

function initCharts() {
    if (typeof Chart === 'undefined') {
        console.log('⚠️ Chart.js not loaded. Please include it.');
        return;
    }

    const riskCtx = document.getElementById('riskChart');
    if (riskCtx) {
        const riskData = JSON.parse(riskCtx.dataset.risk || '{"high":0,"medium":0,"low":0}');
        new Chart(riskCtx, {
            type: 'doughnut',
            data: {
                labels: ['🔴 High Risk', '🟡 Medium Risk', '🟢 Low Risk'],
                datasets: [{
                    data: [riskData.high || 0, riskData.medium || 0, riskData.low || 0],
                    backgroundColor: ['#ef4444', '#f59e0b', '#10b981'],
                    borderColor: ['#ffffff', '#ffffff', '#ffffff'],
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: { size: 14 },
                            padding: 20
                        }
                    }
                }
            }
        });
    }

    const deptCtx = document.getElementById('deptChart');
    if (deptCtx) {
        const deptData = JSON.parse(deptCtx.dataset.dept || '{"labels":[],"values":[]}');
        new Chart(deptCtx, {
            type: 'bar',
            data: {
                labels: deptData.labels || [],
                datasets: [{
                    label: 'Students per Department',
                    data: deptData.values || [],
                    backgroundColor: ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899'],
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {
        const trendData = JSON.parse(trendCtx.dataset.trend || '{"labels":[],"values":[]}');
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: trendData.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Average Attendance %',
                    data: trendData.values || [0, 0, 0, 0, 0, 0],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#6366f1',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    const cgpaCtx = document.getElementById('cgpaChart');
    if (cgpaCtx) {
        const cgpaData = JSON.parse(cgpaCtx.dataset.cgpa || '{"labels":[],"values":[]}');
        new Chart(cgpaCtx, {
            type: 'bar',
            data: {
                labels: cgpaData.labels || ['<5', '5-6', '6-7', '7-8', '8-9', '9-10'],
                datasets: [{
                    label: 'Students by CGPA Range',
                    data: cgpaData.values || [0, 0, 0, 0, 0, 0],
                    backgroundColor: ['#ef4444', '#f59e0b', '#eab308', '#22c55e', '#06b6d4', '#8b5cf6'],
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    if (typeof Chart !== 'undefined') {
        initCharts();
    } else {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = initCharts;
        document.head.appendChild(script);
    }
});