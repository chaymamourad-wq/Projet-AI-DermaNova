/* ============================================================
   DermaNova — Premium Dashboard & Drag-and-Drop (dashboard.js)
============================================================ */

window.initDashboardCharts = function(stats) {
  const mainChartCanvas = document.getElementById('mainChart');
  const donutChartCanvas = document.getElementById('donutChart');

  const getThemeColors = () => {
    return {
      text: '#d1d5db', // light gray
      grid: 'rgba(0, 242, 254, 0.08)', // subtle cyan grid
      mal: '#f43f5e', // premium alarm red
      ben: '#10b981', // premium green
      cyan: '#00f2fe',
      blue: '#0072ff',
      purple: '#7f00ff',
      bg: 'rgba(11, 17, 38, 0.95)'
    };
  };

  let mainChart = null;
  let donutChart = null;

  const renderCharts = () => {
    const colors = getThemeColors();

    // 1. Donut Chart (Global Reapportionment)
    if (donutChartCanvas && stats) {
      if (donutChart) donutChart.destroy();
      donutChart = new Chart(donutChartCanvas, {
        type: 'doughnut',
        data: {
          labels: ['Bénin', 'Malin'],
          datasets: [{
            data: [stats.benign, stats.malignant],
            backgroundColor: [colors.ben, colors.mal],
            borderWidth: 0,
            hoverOffset: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '72%',
          plugins: {
            legend: {
              position: 'bottom',
              labels: { 
                color: colors.text, 
                padding: 18, 
                usePointStyle: true,
                font: { family: 'Outfit', size: 12 }
              }
            }
          }
        }
      });
    }

    // 2. Bar/Line Chart (Temporal Trends)
    if (mainChartCanvas) {
      fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
          if (mainChart) mainChart.destroy();
          
          if (data && data.length > 0) {
            const dates = [...new Set(data.map(item => item.d))].sort().slice(-7); // Last 7 days
            const malData = dates.map(d => {
              const entry = data.find(i => i.d === d && i.result === 'Malignant');
              return entry ? entry.n : 0;
            });
            const benData = dates.map(d => {
              const entry = data.find(i => i.d === d && i.result === 'Benign');
              return entry ? entry.n : 0;
            });

            const ctx = mainChartCanvas.getContext('2d');

            // Generate premium linear gradients
            const benGradient = ctx.createLinearGradient(0, 0, 0, 240);
            benGradient.addColorStop(0, 'rgba(16, 185, 129, 0.4)');
            benGradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

            const malGradient = ctx.createLinearGradient(0, 0, 0, 240);
            malGradient.addColorStop(0, 'rgba(244, 63, 94, 0.4)');
            malGradient.addColorStop(1, 'rgba(244, 63, 94, 0.0)');

            mainChart = new Chart(mainChartCanvas, {
              type: 'line',
              data: {
                labels: dates.map(d => d.slice(5)), // MM-DD
                datasets: [
                  { 
                    label: 'Bénin', 
                    data: benData, 
                    borderColor: colors.ben,
                    backgroundColor: benGradient,
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointBackgroundColor: colors.ben,
                    pointHoverRadius: 6
                  },
                  { 
                    label: 'Malin', 
                    data: malData, 
                    borderColor: colors.mal,
                    backgroundColor: malGradient,
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointBackgroundColor: colors.mal,
                    pointHoverRadius: 6
                  }
                ]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: true,
                    position: 'top',
                    labels: {
                      color: colors.text,
                      usePointStyle: true,
                      font: { family: 'Outfit', size: 12 }
                    }
                  }
                },
                scales: {
                  x: { 
                    ticks: { color: colors.text, font: { family: 'Outfit' } }, 
                    grid: { display: false } 
                  },
                  y: { 
                    ticks: { color: colors.text, font: { family: 'Outfit' }, stepSize: 1 }, 
                    grid: { color: colors.grid } 
                  }
                }
              }
            });
          } else {
            const ctx = mainChartCanvas.getContext('2d');
            ctx.font = "14px Outfit";
            ctx.fillStyle = colors.text;
            ctx.textAlign = "center";
            ctx.fillText("Aucun diagnostic enregistré pour modéliser le graphe.", mainChartCanvas.width / 2, mainChartCanvas.height / 2);
          }
        })
        .catch(err => console.error("Erreur API stats:", err));
    }
  };

  renderCharts();

  // Reload charts on theme changes
  document.getElementById('themeToggle')?.addEventListener('click', () => {
    setTimeout(renderCharts, 150);
  });

  window.refreshChart = renderCharts;
};

// --- Drag & Drop for Diagnostic Upload Bay ---
document.addEventListener('DOMContentLoaded', () => {
  const uploadArea = document.getElementById('uploadArea');
  const fileInput = document.getElementById('imageInput');
  const imagePreview = document.getElementById('imagePreview');
  const uploadText = document.getElementById('uploadText');
  const previewContainer = document.getElementById('previewContainer');

  if (uploadArea && fileInput) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

    ['dragenter', 'dragover'].forEach(eventName => {
      uploadArea.addEventListener(eventName, () => uploadArea.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      uploadArea.addEventListener(eventName, () => uploadArea.classList.remove('dragover'), false);
    });

    uploadArea.addEventListener('drop', (e) => {
      let files = e.dataTransfer.files;
      if (files.length > 0) {
        fileInput.files = files;
        handleFiles(files[0]);
      }
    }, false);

    fileInput.addEventListener('change', function() {
      if (this.files.length > 0) handleFiles(this.files[0]);
    });

    function handleFiles(file) {
      if (!file.type.startsWith('image/')) return alert("Format d'image non supporté.");
      let reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onloadend = function() {
        if (imagePreview) {
          imagePreview.src = reader.result;
          imagePreview.style.display = 'block';
        }
        if (previewContainer) {
          previewContainer.classList.remove('d-none');
        }
        if (uploadText) {
          uploadText.innerHTML = `<i class="fa-solid fa-file-circle-check text-success me-2"></i> ${file.name}`;
        }
      }
    }
  }
});
