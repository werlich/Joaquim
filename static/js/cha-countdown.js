(function () {
  var root = document.getElementById('cha-countdown');
  if (!root) return;

  var startsAt = Date.parse(root.getAttribute('data-starts-at') || '');
  var endsAt = Date.parse(root.getAttribute('data-ends-at') || '');
  var eventDate = root.getAttribute('data-event-date') || '';
  var tz = root.getAttribute('data-tz') || 'America/Sao_Paulo';
  if (!isFinite(startsAt) || !isFinite(endsAt)) return;

  var copy = {};
  var copyEl = document.getElementById('cha-countdown-copy');
  if (copyEl) {
    try { copy = JSON.parse(copyEl.textContent || '{}'); } catch (err) { copy = {}; }
  }

  var msgEl = root.querySelector('[data-role="live-msg"]');
  var endedTitle = root.querySelector('[data-role="ended-title"]');
  var unitsEl = root.querySelector('[data-role="units"]');
  var srEl = document.querySelector('[data-countdown-sr]');
  var numEls = {
    days: root.querySelector('[data-unit="days"]'),
    hours: root.querySelector('[data-unit="hours"]'),
    minutes: root.querySelector('[data-unit="minutes"]'),
    seconds: root.querySelector('[data-unit="seconds"]')
  };

  var reduceMotion = false;
  try {
    reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (err) {}

  function pad2(n) {
    n = String(Math.max(0, n | 0));
    return n.length < 2 ? '0' + n : n;
  }

  function ymdInTz(ms) {
    try {
      return new Intl.DateTimeFormat('en-CA', {
        timeZone: tz,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      }).format(new Date(ms));
    } catch (err) {
      var d = new Date(ms);
      return d.toISOString().slice(0, 10);
    }
  }

  function remainingParts(ms) {
    var total = Math.max(0, Math.floor(ms / 1000));
    var days = Math.floor(total / 86400);
    var hours = Math.floor((total % 86400) / 3600);
    var minutes = Math.floor((total % 3600) / 60);
    var seconds = total % 60;
    return { days: days, hours: hours, minutes: minutes, seconds: seconds };
  }

  function phaseFor(nowMs) {
    if (nowMs >= endsAt) return 'ended';
    if (ymdInTz(nowMs) === eventDate) return 'today';
    var remaining = startsAt - nowMs;
    if (remaining <= 0) return 'today';
    if (remaining < 48 * 3600 * 1000) return 'soon';
    if (remaining < 7 * 86400 * 1000) return 'week';
    if (remaining <= 30 * 86400 * 1000) return 'month';
    return 'far';
  }

  function setText(el, value) {
    if (!el || el.textContent === value) return;
    el.textContent = value;
    if (!reduceMotion && el.classList.contains('cha-countdown-num')) {
      el.classList.remove('is-tick');
      void el.offsetWidth;
      el.classList.add('is-tick');
    }
  }

  var lastSrDays = null;
  var lastPhase = null;

  function tick() {
    var nowMs = Date.now();
    var phase = phaseFor(nowMs);
    var parts = remainingParts(startsAt - nowMs);
    var ended = phase === 'ended';

    root.setAttribute('data-phase', phase);
    root.classList.toggle('is-ended', ended);

    if (unitsEl) unitsEl.hidden = ended;
    if (endedTitle) endedTitle.hidden = !ended;
    if (msgEl) setText(msgEl, copy[phase] || msgEl.textContent);

    if (!ended) {
      if (numEls.days) setText(numEls.days, String(parts.days));
      if (numEls.hours) setText(numEls.hours, pad2(parts.hours));
      if (numEls.minutes) setText(numEls.minutes, pad2(parts.minutes));
      if (numEls.seconds) setText(numEls.seconds, pad2(parts.seconds));
    }

    if (srEl && (phase !== lastPhase || parts.days !== lastSrDays)) {
      lastPhase = phase;
      lastSrDays = parts.days;
      if (ended) {
        srEl.textContent = (endedTitle ? endedTitle.textContent + ' ' : '') + (copy.ended || '');
      } else {
        srEl.textContent = 'Faltam ' + parts.days + ' dias para o Chá de Bebê do Joaquim.';
      }
    }

    if (ended && timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  var timer = setInterval(tick, 1000);
  tick();
})();
