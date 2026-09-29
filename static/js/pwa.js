(function () {
  var INSTALL_KEY = 'joaquim-pwa-install-dismissed';
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

  function applyNewsBadge() {
    if (typeof window.joaquimApplyNewsBadge === 'function') {
      window.joaquimApplyNewsBadge();
    }
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
