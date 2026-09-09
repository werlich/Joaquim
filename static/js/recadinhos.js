(function () {
  var textarea = document.querySelector('.recado-form textarea');
  var count = document.querySelector('[data-recado-count]');
  if (textarea && count) {
    function updateCount() {
      count.textContent = String(textarea.value.length);
    }
    textarea.addEventListener('input', updateCount);
    updateCount();
  }

  var cards = document.querySelectorAll('.recado-card');
  if (!cards.length) return;

  var reduce = false;
  try {
    reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (err) {}

  if (reduce || !('IntersectionObserver' in window)) {
    cards.forEach(function (el) { el.classList.add('is-visible'); });
    return;
  }

  cards.forEach(function (el) { el.classList.add('will-animate'); });

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

  cards.forEach(function (el) { io.observe(el); });
})();
