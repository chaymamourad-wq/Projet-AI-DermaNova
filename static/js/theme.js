// static/js/theme.js
// Initialise Particles.js with a subtle dark‑pink particle field
/* global particlesJS */
document.addEventListener('DOMContentLoaded', function () {
  if (window.particlesJS) {
    particlesJS('particles-js', {
      "particles": {
        "number": { "value": 60, "density": { "enable": true, "value_area": 800 } },
        "color": { "value": ["#00b4d8", "#90e0ef", "#0077b6"] },
        "shape": { "type": "circle" },
        "opacity": { "value": 0.35, "random": true },
        "size": { "value": 3, "random": true },
        "move": { "enable": true, "speed": 0.6, "direction": "none", "out_mode": "out" }
      },
      "interactivity": {
        "detect_on": "canvas",
        "events": { "resize": true }
      },
      "retina_detect": true
    });
  }

  // Scroll‑to‑top button handling
  const scrollBtn = document.getElementById('scrollTop');
  if (scrollBtn) {
    const toggleVisibility = () => {
      if (window.scrollY > 200) { scrollBtn.classList.add('show'); }
      else { scrollBtn.classList.remove('show'); }
    };
    window.addEventListener('scroll', toggleVisibility);
    scrollBtn.addEventListener('click', () => { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  }
});
