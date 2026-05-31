// static/js/premium.js
// Initialise Particles.js and AOS, plus helper for parallax effect
/* global particlesJS, AOS */

document.addEventListener('DOMContentLoaded', function () {
  // Particles background
  if (window.particlesJS) {
    particlesJS('particles-bg', {
      particles: {
        number: { value: 70, density: { enable: true, value_area: 900 } },
        color: { value: ['#00b4d8', '#90e0ef', '#0077b6'] },
        shape: { type: 'circle' },
        opacity: { value: 0.35, random: true },
        size: { value: 3, random: true },
        move: { enable: true, speed: 0.6, direction: 'none', out_mode: 'out' }
      },
      interactivity: { detect_on: 'canvas', events: { resize: true } },
      retina_detect: true
    });
  }

  // Initialise AOS (Animate On Scroll)
  if (window.AOS) {
    AOS.init({
      duration: 800,
      once: true,
      easing: 'ease-out-cubic'
    });
  }

  // Optional light parallax on scroll for elements with .parallax class
  const parallaxElems = document.querySelectorAll('.parallax');
  window.addEventListener('scroll', function () {
    const scrollY = window.scrollY;
    parallaxElems.forEach(el => {
      const speed = parseFloat(el.dataset.speed || '0.3');
      el.style.transform = `translateY(${scrollY * speed}px)`;
    });
  });

  // Scroll‑to‑top button handling (reuse from theme.js if exists)
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
