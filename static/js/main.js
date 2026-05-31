/* ============================================================
   DermaNova — Premium Global Logic (main.js)
============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  // --- 1. Preloader dismissal ---
  const loader = document.getElementById('page-loader');
  if (loader) {
    setTimeout(() => {
      loader.style.opacity = '0';
      setTimeout(() => {
        loader.style.visibility = 'hidden';
      }, 600);
    }, 1000); // Premium diagnostic delay
  }

  // --- 2. Theme Toggling (Immersive high-tech dark theme is standard) ---
  document.documentElement.setAttribute('data-theme', 'dark');

  // --- 3. Scroll to Top Button ---
  const scrollBtn = document.getElementById('scrollTop');
  if (scrollBtn) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 300) {
        scrollBtn.classList.add('show');
      } else {
        scrollBtn.classList.remove('show');
      }
    });

    scrollBtn.addEventListener('click', () => {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }

  // --- 4. Auto-dismiss Flash Alerts ---
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    setTimeout(() => {
      if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
        const bsAlert = bootstrap.Alert.getInstance(alert) || new bootstrap.Alert(alert);
        if (bsAlert) {
          bsAlert.close();
        }
      } else {
        alert.style.display = 'none';
      }
    }, 6000); // 6 seconds
  });

  // --- 5. Custom Sidebar Toggle for Mobile ---
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.querySelector('.sidebar-overlay');

  if (sidebarToggle && sidebar) {
    // Inject overlay if not present
    let overlayEl = overlay;
    if (!overlayEl) {
      overlayEl = document.createElement('div');
      overlayEl.className = 'sidebar-overlay';
      document.body.appendChild(overlayEl);
    }

    sidebarToggle.addEventListener('click', (e) => {
      e.preventDefault();
      sidebar.classList.toggle('open');
      overlayEl.classList.toggle('visible');
    });

    overlayEl.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlayEl.classList.remove('visible');
    });
  }

  // --- 6. Particles.js Neural Network Configuration ---
  if (typeof particlesJS !== 'undefined' && document.getElementById('particles-js')) {
    particlesJS('particles-js', {
      "particles": {
        "number": {
          "value": 45,
          "density": {
            "enable": true,
            "value_area": 900
          }
        },
        "color": {
          "value": "#00f2fe"
        },
        "shape": {
          "type": "circle",
          "stroke": {
            "width": 0,
            "color": "#000000"
          }
        },
        "opacity": {
          "value": 0.25,
          "random": true,
          "anim": {
            "enable": true,
            "speed": 1,
            "opacity_min": 0.1,
            "sync": false
          }
        },
        "size": {
          "value": 3,
          "random": true,
          "anim": {
            "enable": true,
            "speed": 2,
            "size_min": 0.5,
            "sync": false
          }
        },
        "line_linked": {
          "enable": true,
          "distance": 180,
          "color": "#00f2fe",
          "opacity": 0.15,
          "width": 1.2
        },
        "move": {
          "enable": true,
          "speed": 1.6,
          "direction": "none",
          "random": true,
          "straight": false,
          "out_mode": "out",
          "bounce": false,
          "attract": {
            "enable": true,
            "rotateX": 600,
            "rotateY": 1200
          }
        }
      },
      "interactivity": {
        "detect_on": "window",
        "events": {
          "onhover": {
            "enable": true,
            "mode": "grab"
          },
          "onclick": {
            "enable": true,
            "mode": "push"
          },
          "resize": true
        },
        "modes": {
          "grab": {
            "distance": 200,
            "line_linked": {
              "opacity": 0.4
            }
          },
          "push": {
            "particles_nb": 3
          }
        }
      },
      "retina_detect": true
    });
  }
});
