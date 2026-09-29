(function () {
  var NEWS_KEY = 'joaquim-news-seen';
  var PENDING_KEY = 'joaquim-pending-seen';
  var POLL_MS = 45000;
  var originalTitle = document.title;
  var lastAlertedPending = -1;
  var lastAlertedRevision = '';

  function $(id) {
    return document.getElementById(id);
  }

  function parseNews(revision) {
    var match = /^t(\d+)-r(\d+)$/.exec(revision || '');
    return match ? { t: Number(match[1]), r: Number(match[2]) } : { t: 0, r: 0 };
  }

  function newsDestination(current, seen) {
    var timelineNew = current.t > seen.t;
    var recadoNew = current.r > seen.r;
    if (timelineNew && !recadoNew) return '/timeline/';
    if (recadoNew && !timelineNew) return '/recadinhos/';
    return '/';
  }

  function newsLabel(current, seen) {
    var timelineNew = current.t > seen.t;
    var recadoNew = current.r > seen.r;
    if (recadoNew && !timelineNew) return 'Tem recadinho novo para o Joaquim';
    if (timelineNew && !recadoNew) return 'Tem novidade na jornada do Joaquim';
    if (recadoNew && timelineNew) return 'Tem recadinho e novidade no blog do Joaquim';
    return 'Tem novidade no blog do Joaquim';
  }

  function setAppBadge(count) {
    if (typeof navigator.setAppBadge === 'function') {
      if (count) navigator.setAppBadge(count).catch(function () {});
      else if (typeof navigator.clearAppBadge === 'function') {
        navigator.clearAppBadge().catch(function () {});
      }
    }
  }

  function setNavRecadoBadge(on) {
    var links = document.querySelectorAll('a[href="/recadinhos/"], a[href="/recadinhos"]');
    Array.prototype.forEach.call(links, function (link) {
      var dot = link.querySelector('.nav-news-dot');
      if (on) {
        link.classList.add('has-news-link');
        if (!dot) {
          dot = document.createElement('span');
          dot.className = 'nav-news-dot';
          dot.setAttribute('aria-hidden', 'true');
          link.appendChild(dot);
        }
      } else {
        link.classList.remove('has-news-link');
        if (dot) dot.remove();
      }
    });
  }

  function setNewsTitle(on) {
    if (on) {
      if (document.title.indexOf('● ') !== 0) {
        document.title = '● ' + originalTitle;
      }
    } else if (document.title.indexOf('● ') === 0) {
      document.title = originalTitle;
    }
  }

  function notifyBrowser(title, body, url) {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    try {
      var note = new Notification(title, { body: body, tag: 'joaquim-news' });
      note.onclick = function () {
        window.focus();
        if (url) window.location.href = url;
        note.close();
      };
    } catch (err) {}
  }

  function applyNewsBadge() {
    var toast = $('pwa-news-toast');
    if (!toast || toast.hidden) return;
    var btn = $('pwa-install-btn');
    if (btn && !btn.hidden) btn.classList.add('has-news');
  }

  window.joaquimApplyNewsBadge = applyNewsBadge;

  function markNewsSeen(revision) {
    if (revision) localStorage.setItem(NEWS_KEY, revision);
    var toast = $('pwa-news-toast');
    if (toast) toast.hidden = true;
    var btn = $('pwa-install-btn');
    if (btn) btn.classList.remove('has-news');
    setNavRecadoBadge(false);
    setNewsTitle(false);
    setAppBadge(0);
  }

  function showPublicNews(revision, seen) {
    var toast = $('pwa-news-toast');
    if (!toast || !revision) return;
    var current = parseNews(revision);
    var previous = parseNews(seen);
    var recadoNew = current.r > previous.r;
    var dest = newsDestination(current, previous);
    var label = newsLabel(current, previous);
    var text = toast.querySelector('[data-pwa-news-text]');
    if (text) text.textContent = label;
    var open = toast.querySelector('[data-pwa-news-open]');
    if (open) open.setAttribute('href', dest);
    toast.hidden = false;
    applyNewsBadge();
    setNavRecadoBadge(recadoNew);
    setNewsTitle(true);
    setAppBadge(1);
    if (revision !== lastAlertedRevision) {
      lastAlertedRevision = revision;
      notifyBrowser('Joaquim Werlich Galvão', label, dest);
    }
  }

  function initPublicNews() {
    var toast = $('pwa-news-toast');
    if (!toast) return;
    var revision = toast.getAttribute('data-news-revision') || '';
    if (!revision) return;

    var seen = localStorage.getItem(NEWS_KEY);
    if (!seen) {
      localStorage.setItem(NEWS_KEY, revision);
      return;
    }
    if (seen === revision) return;

    var current = parseNews(revision);
    var previous = parseNews(seen);
    if (
      current.r > previous.r &&
      current.t <= previous.t &&
      location.pathname.indexOf('/recadinhos') === 0
    ) {
      markNewsSeen(revision);
      return;
    }
    showPublicNews(revision, seen);
  }

  function markPendingSeen(count) {
    localStorage.setItem(PENDING_KEY, String(count || 0));
    var toast = $('staff-recado-toast');
    if (toast) toast.hidden = true;
  }

  function ensureStaffToast() {
    if ($('staff-recado-toast') || !window.JOAQUIM_STAFF) return;
    var toast = document.createElement('div');
    toast.id = 'staff-recado-toast';
    toast.className = 'pwa-toast pwa-toast-news';
    toast.hidden = true;
    toast.innerHTML =
      '<span data-staff-recado-text></span>' +
      '<span class="pwa-news-actions">' +
      '<button type="button" class="btn" data-staff-recado-dismiss>Agora não</button>' +
      '<a class="btn btn-primary" href="/admin/mensagens/recado/" data-staff-recado-open>Ver recados</a>' +
      '</span>';
    document.body.appendChild(toast);
  }

  function updateStaffPending(count) {
    ensureStaffToast();
    var toast = $('staff-recado-toast');
    if (!toast && !window.JOAQUIM_STAFF) return;
    count = Number(count || 0);
    if (toast) toast.setAttribute('data-pending', String(count));
    var seen = Number(localStorage.getItem(PENDING_KEY) || 0);
    var label = count === 1
      ? 'Há 1 recadinho aguardando aprovação'
      : 'Há ' + count + ' recadinhos aguardando aprovação';
    var text = toast ? toast.querySelector('[data-staff-recado-text]') : null;
    if (text) text.textContent = label;
    if (count > seen) {
      if (toast) toast.hidden = false;
      if (count !== lastAlertedPending) {
        lastAlertedPending = count;
        setNewsTitle(true);
        setAppBadge(count);
        notifyBrowser('Recadinho pendente', label, '/admin/mensagens/recado/');
      }
    } else if (count === 0) {
      lastAlertedPending = 0;
      markPendingSeen(0);
    }
  }

  function applyPayload(data) {
    if (!data) return;
    var toast = $('pwa-news-toast');
    if (toast && data.revision !== undefined) {
      toast.setAttribute('data-news-revision', data.revision || '');
      toast.setAttribute('data-news-timeline', String(data.timeline_id || 0));
      toast.setAttribute('data-news-recado', String(data.recado_id || 0));
      initPublicNews();
    }
    if (data.pending_count !== undefined) {
      updateStaffPending(data.pending_count);
    }
  }

  function pollNews() {
    fetch('/novidades.json', { credentials: 'same-origin', cache: 'no-store' })
      .then(function (res) { return res.json(); })
      .then(applyPayload)
      .catch(function () {});
  }

  initPublicNews();
  ensureStaffToast();
  var staffToast = $('staff-recado-toast');
  if (staffToast) {
    updateStaffPending(Number(staffToast.getAttribute('data-pending') || 0));
  }
  pollNews();

  document.addEventListener('click', function (event) {
    var newsToast = $('pwa-news-toast');
    var revision = newsToast ? (newsToast.getAttribute('data-news-revision') || '') : '';
    if (event.target.closest('[data-pwa-news-dismiss]')) {
      markNewsSeen(revision);
      return;
    }
    if (event.target.closest('[data-pwa-news-open]')) {
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().catch(function () {});
      }
      markNewsSeen(revision);
      return;
    }
    var pendingToast = $('staff-recado-toast');
    var pending = pendingToast ? Number(pendingToast.getAttribute('data-pending') || 0) : 0;
    if (event.target.closest('[data-staff-recado-dismiss]')) {
      markPendingSeen(pending);
      return;
    }
    if (event.target.closest('[data-staff-recado-open]')) {
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().catch(function () {});
      }
      markPendingSeen(pending);
    }
  });

  setInterval(pollNews, POLL_MS);
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) pollNews();
  });
})();
