(function () {
  var root = document.getElementById('joaquimetro');
  if (!root) return;

  var fill = root.querySelector('[data-joaquimetro-fill]');
  if (!fill) return;

  var reduce = false;
  try {
    reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (err) {}

  function show() {
    root.classList.add('is-inview');
  }

  if (reduce || !('IntersectionObserver' in window)) {
    show();
    return;
  }

  root.classList.add('js-ready');
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        show();
        io.disconnect();
      }
    });
  }, { threshold: 0.28 });
  io.observe(root);
})();
