(function () {
  var INSTALL_KEY = 'joaquim-pwa-install-dismissed';
  var NEWS_KEY = 'joaquim-news-seen';
  var deferredPrompt = null;

  function isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches
      || window.navigator.standalone === true;
  }

  function isIosSafari() {
    var ua = navigator.userAgent || '';
    var ios = /iPhone|iPad|iPod/i.test(ua);
    var safari = /Safari/i.test(ua) && !/CriOS|FxiOS|EdgiOS|OPiOS|Android/i.test(ua);
    return ios && safari;
  }

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

  function setAppBadge(count) {
    if (typeof navigator.setAppBadge === 'function') {
      if (count) navigator.setAppBadge(count).catch(function () {});
      else if (typeof navigator.clearAppBadge === 'function') {
        navigator.clearAppBadge().catch(function () {});
      }
    }
  }

  function markNewsSeen(revision) {
    if (revision) localStorage.setItem(NEWS_KEY, revision);
    var toast = $('pwa-news-toast');
    if (toast) toast.hidden = true;
    var btn = $('pwa-install-btn');
    if (btn) btn.classList.remove('has-news');
    setAppBadge(0);
  }

  function applyNewsBadge() {
    var toast = $('pwa-news-toast');
    if (!toast || toast.hidden) return;
    var btn = $('pwa-install-btn');
    if (btn && !btn.hidden) btn.classList.add('has-news');
  }

  function initNews() {
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

    var open = toast.querySelector('[data-pwa-news-open]');
    if (open) open.setAttribute('href', newsDestination(parseNews(revision), parseNews(seen)));
    toast.hidden = false;
    applyNewsBadge();
    if (isStandalone()) setAppBadge(1);
  }

  function hideInstall() {
    var btn = $('pwa-install-btn');
    var hint = $('pwa-ios-hint');
    var dismiss = $('pwa-install-dismiss');
    if (btn) {
      btn.hidden = true;
      btn.classList.remove('has-news');
    }
    if (hint) hint.hidden = true;
    if (dismiss) dismiss.hidden = true;
  }

  function showDismiss() {
    var dismiss = $('pwa-install-dismiss');
    if (dismiss) dismiss.hidden = false;
  }

  initNews();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js', { scope: '/' }).then(function (reg) {
      if (reg.waiting) showUpdate(reg);
      reg.addEventListener('updatefound', function () {
        var installing = reg.installing;
        if (!installing) return;
        installing.addEventListener('statechange', function () {
          if (installing.state === 'installed' && navigator.serviceWorker.controller) {
            showUpdate(reg);
          }
        });
      });
    }).catch(function () {});

    navigator.serviceWorker.addEventListener('controllerchange', function () {
      if (refreshing) return;
      var active = document.activeElement;
      if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable)) {
        return;
      }
      refreshing = true;
      window.location.reload();
    });
  }

  function showUpdate(reg) {
    var toast = $('pwa-update-toast');
    if (!toast) return;
    toast.hidden = false;
    var btn = toast.querySelector('[data-pwa-update]');
    if (!btn) return;
    btn.onclick = function () {
      if (reg.waiting) {
        reg.waiting.postMessage({ type: 'SKIP_WAITING' });
      }
    };
  }

  var refreshing = false;

  window.addEventListener('beforeinstallprompt', function (event) {
    event.preventDefault();
    if (isStandalone() || localStorage.getItem(INSTALL_KEY)) return;
    deferredPrompt = event;
    var btn = $('pwa-install-btn');
    if (btn) btn.hidden = false;
    applyNewsBadge();
    showDismiss();
  });

  if (isIosSafari() && !isStandalone() && !localStorage.getItem(INSTALL_KEY)) {
    var hint = $('pwa-ios-hint');
    if (hint) hint.hidden = false;
    showDismiss();
  }

  if (isStandalone()) {
    hideInstall();
  }

  document.addEventListener('click', function (event) {
    if (event.target.closest('#pwa-install-btn')) {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      deferredPrompt.userChoice.finally(function () {
        deferredPrompt = null;
        hideInstall();
      });
      return;
    }
    if (event.target.closest('#pwa-install-dismiss')) {
      localStorage.setItem(INSTALL_KEY, '1');
      hideInstall();
      return;
    }
    var newsToast = $('pwa-news-toast');
    var revision = newsToast ? (newsToast.getAttribute('data-news-revision') || '') : '';
    if (event.target.closest('[data-pwa-news-dismiss]')) {
      markNewsSeen(revision);
      return;
    }
    if (event.target.closest('[data-pwa-news-open]')) {
      markNewsSeen(revision);
    }
  });

  var net = $('pwa-net-toast');
  var netTimer;
  function flashNet(online) {
    if (!net) return;
    net.textContent = online ? 'Você está online de novo' : 'Você está offline';
    net.hidden = false;
    net.dataset.state = online ? 'online' : 'offline';
    clearTimeout(netTimer);
    netTimer = setTimeout(function () {
      net.hidden = true;
    }, 2800);
  }
  window.addEventListener('offline', function () { flashNet(false); });
  window.addEventListener('online', function () { flashNet(true); });
})();
