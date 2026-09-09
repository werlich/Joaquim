(function () {
  var root = document.querySelector('.journey');
  if (!root) return;

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var items = root.querySelectorAll('.journey-item');
  var fill = root.querySelector('.journey-line-fill');
  var track = root.querySelector('.journey-track');

  if (!reduce && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible', 'is-seen');
        }
      });
    }, { threshold: 0.22, rootMargin: '0px 0px -8% 0px' });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add('is-visible', 'is-seen'); });
  }

  function updateProgress() {
    if (fill && track) {
      var rect = track.getBoundingClientRect();
      var start = window.scrollY + rect.top;
      var h = Math.max(1, track.offsetHeight);
      var marker = window.scrollY + window.innerHeight * 0.38;
      var progress = (marker - start) / h;
      if (progress < 0) progress = 0;
      if (progress > 1) progress = 1;
      fill.style.height = (progress * 100) + '%';
    }

    var active = null;
    items.forEach(function (el) {
      el.classList.remove('is-active');
      if (el.getBoundingClientRect().top < window.innerHeight * 0.55) active = el;
    });
    if (active) active.classList.add('is-active');
  }

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      updateProgress();
      ticking = false;
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  updateProgress();
})();
