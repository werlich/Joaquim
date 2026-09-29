(function () {
  var toggle = document.getElementById('nav-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      nav.classList.toggle('open');
    });
  }

  function csrfToken() {
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  function openModal(id) {
    var m = document.getElementById(id);
    if (m) m.hidden = false;
  }
  function closeModals() {
    document.querySelectorAll('.modal').forEach(function (m) { m.hidden = true; });
  }
  document.querySelectorAll('[data-close]').forEach(function (el) {
    el.addEventListener('click', closeModals);
  });

  function insertEmoji(textarea, emoji) {
    if (!textarea || !emoji) return;
    var max = parseInt(textarea.getAttribute('maxlength') || '0', 10);
    var start = typeof textarea.selectionStart === 'number' ? textarea.selectionStart : textarea.value.length;
    var end = typeof textarea.selectionEnd === 'number' ? textarea.selectionEnd : start;
    var next = textarea.value.slice(0, start) + emoji + textarea.value.slice(end);
    if (max > 0 && next.length > max) return;
    textarea.value = next;
    var caret = start + emoji.length;
    textarea.focus();
    try { textarea.setSelectionRange(caret, caret); } catch (err) {}
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
  }

  document.addEventListener('click', function (event) {
    var btn = event.target.closest('.emoji-btn');
    if (!btn) return;
    var picker = btn.closest('.emoji-picker');
    if (!picker) return;
    event.preventDefault();
    var targetId = picker.getAttribute('data-emoji-for');
    var textarea = targetId ? document.getElementById(targetId) : null;
    if (!textarea) {
      var field = picker.closest('.field') || picker.parentElement;
      textarea = field && field.querySelector('textarea');
    }
    if (!textarea) {
      var form = picker.closest('form');
      textarea = form && form.querySelector('textarea[name="message"], textarea[name="mensagem"], textarea');
    }
    insertEmoji(textarea, btn.getAttribute('data-emoji') || btn.textContent.trim());
  });

  var giftUrl = null;
  var giftId = null;
  var giftQtyMode = false;
  var giftOpenChoice = false;
  document.querySelectorAll('.js-open-gift').forEach(function (btn) {
    btn.addEventListener('click', function () {
      giftUrl = btn.dataset.url;
      giftId = btn.dataset.giftId;
      giftQtyMode = btn.dataset.qtyMode === '1';
      giftOpenChoice = btn.dataset.openChoice === '1';
      document.getElementById('gift-confirm-name').textContent = btn.dataset.giftName;
      document.getElementById('gift-error').hidden = true;
      document.getElementById('form-gift').reset();
      var qtyWrap = document.getElementById('gift-qty-wrap');
      var qtyInput = document.getElementById('gift-quantity');
      var itemWrap = document.getElementById('gift-item-wrap');
      var itemInput = document.getElementById('gift-item-name');
      if (giftOpenChoice) {
        qtyWrap.hidden = true;
        qtyInput.required = false;
        qtyInput.value = '1';
        if (itemWrap) itemWrap.hidden = false;
        if (itemInput) itemInput.required = true;
      } else if (giftQtyMode) {
        qtyWrap.hidden = false;
        qtyInput.required = true;
        qtyInput.max = btn.dataset.available;
        qtyInput.value = '1';
        document.getElementById('gift-available').textContent = btn.dataset.available;
        if (itemWrap) itemWrap.hidden = true;
        if (itemInput) itemInput.required = false;
      } else {
        qtyWrap.hidden = true;
        qtyInput.required = false;
        qtyInput.value = '1';
        if (itemWrap) itemWrap.hidden = true;
        if (itemInput) itemInput.required = false;
      }
      openModal('modal-gift');
    });
  });

  function renderLike(btn, liked, likes) {
    btn.classList.toggle('is-liked', liked);
    btn.setAttribute('aria-pressed', liked ? 'true' : 'false');
    var icon = btn.querySelector('[aria-hidden]');
    if (icon) icon.textContent = liked ? '💚' : '🤍';
    var count = btn.querySelector('.js-like-count');
    if (count) count.textContent = likes;
  }

  function makeLikeButton(url, likes) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'chooser-like js-like';
    btn.dataset.url = url;
    btn.setAttribute('aria-pressed', 'false');
    btn.setAttribute('aria-label', 'Curtir esta escolha');
    var icon = document.createElement('span');
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = '🤍';
    var count = document.createElement('span');
    count.className = 'chooser-like-count js-like-count';
    count.textContent = typeof likes === 'number' ? likes : 0;
    btn.appendChild(icon);
    btn.appendChild(count);
    return btn;
  }

  document.addEventListener('click', async function (event) {
    var btn = event.target.closest('.js-like');
    if (!btn || !btn.dataset.url || btn.disabled) return;
    event.preventDefault();
    btn.disabled = true;
    try {
      var res = await fetch(btn.dataset.url, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
      });
      var data = await res.json().catch(function () { return {}; });
      if (res.ok && data.ok) {
        renderLike(btn, data.liked, data.likes);
        if (data.likers) btn.title = 'Curtiram: ' + data.likers;
        else btn.removeAttribute('title');
      } else if (data.error) {
        alert(data.error);
      }
    } catch (err) {
      /* offline: mantém o estado atual */
    }
    btn.disabled = false;
  });

  var formGift = document.getElementById('form-gift');
  if (formGift) {
    formGift.addEventListener('submit', async function (e) {
      e.preventDefault();
      var err = document.getElementById('gift-error');
      err.hidden = true;
      var fd = new FormData(formGift);
      if (!fd.get('is_anonymous')) fd.delete('is_anonymous');
      else fd.set('is_anonymous', '1');
      if (!giftQtyMode || giftOpenChoice) fd.set('quantity', '1');
      var res = await fetch(giftUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
        body: fd,
      });
      var data = await res.json().catch(function () { return {}; });
      if (!res.ok || !data.ok) {
        err.textContent = data.error || 'Não foi possível reservar.';
        err.hidden = false;
        return;
      }
      var card = document.querySelector('.gift-card[data-gift-id="' + giftId + '"]');
      if (card) {
        var body = card.querySelector('.card-body');
        if (data.qty_mode) {
          var chosen = body.querySelector('.js-gift-chosen');
          var available = body.querySelector('.js-gift-available');
          if (chosen) chosen.textContent = data.chosen;
          if (available) available.textContent = data.available;
          var fill = body.querySelector('.js-gift-bar-fill');
          var pctLabel = body.querySelector('.js-gift-bar-pct');
          var bar = body.querySelector('.gift-bar');
          var pct = typeof data.progress === 'number' ? data.progress : 0;
          if (fill) fill.style.width = pct + '%';
          if (pctLabel) pctLabel.textContent = pct + '%';
          if (bar) bar.setAttribute('aria-valuenow', String(pct));
          var choosers = body.querySelector('.js-choosers');
          if (choosers && data.chooser) {
            var empty = choosers.querySelector('.choosers-empty');
            if (empty) empty.remove();
            choosers.hidden = false;
            var li = document.createElement('li');
            var name = document.createElement('span');
            name.className = 'chooser-name';
            name.textContent = data.chooser;
            li.appendChild(name);
            if (data.message) {
              var note = document.createElement('span');
              note.className = 'chooser-note';
              note.textContent = data.message;
              li.appendChild(note);
            }
            if (data.like_url) li.appendChild(makeLikeButton(data.like_url, data.likes));
            choosers.appendChild(li);
          }
          var openBtn = body.querySelector('.js-open-gift');
          if (data.meta_reached) {
            if (openBtn) openBtn.remove();
            var p = document.createElement('p');
            p.className = 'status meta-ok';
            p.textContent = 'META ATINGIDA 💚';
            body.appendChild(p);
          } else if (openBtn) {
            openBtn.dataset.available = data.available;
          }
        } else {
          var btn = body.querySelector('.js-open-gift');
          if (btn) btn.remove();
          var wrap = document.createElement('div');
          wrap.className = 'gift-taken';
          var p2 = document.createElement('p');
          p2.className = 'status taken';
          p2.textContent = data.display;
          wrap.appendChild(p2);
          if (data.message) {
            var note2 = document.createElement('p');
            note2.className = 'chooser-note';
            note2.textContent = data.message;
            wrap.appendChild(note2);
          }
          if (data.like_url) wrap.appendChild(makeLikeButton(data.like_url, data.likes));
          body.appendChild(wrap);
        }
      }
      closeModals();
    });
  }

  var diaperUrl = null;
  var sizeId = null;
  document.querySelectorAll('.js-open-diaper').forEach(function (btn) {
    btn.addEventListener('click', function () {
      diaperUrl = btn.dataset.url;
      sizeId = btn.dataset.sizeId;
      document.getElementById('diaper-confirm-label').textContent = btn.dataset.sizeLabel;
      document.getElementById('diaper-available').textContent = btn.dataset.available;
      document.getElementById('diaper-error').hidden = true;
      document.getElementById('form-diaper').reset();
      document.querySelector('#form-diaper [name=quantity]').max = btn.dataset.available;
      openModal('modal-diaper');
    });
  });

  var formDiaper = document.getElementById('form-diaper');
  if (formDiaper) {
    formDiaper.addEventListener('submit', async function (e) {
      e.preventDefault();
      var err = document.getElementById('diaper-error');
      err.hidden = true;
      var fd = new FormData(formDiaper);
      if (!fd.get('is_anonymous')) fd.delete('is_anonymous');
      else fd.set('is_anonymous', '1');
      var res = await fetch(diaperUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
        body: fd,
      });
      var data = await res.json().catch(function () { return {}; });
      if (!res.ok || !data.ok) {
        err.textContent = data.error || 'Não foi possível registrar.';
        err.hidden = false;
        return;
      }
      var card = document.querySelector('.diaper-card[data-size-id="' + sizeId + '"]');
      if (card) {
        card.querySelector('.js-chosen').textContent = data.chosen;
        card.querySelector('.js-available').textContent = data.available;
        var fill = card.querySelector('.js-diaper-bar-fill');
        var pctLabel = card.querySelector('.js-diaper-bar-pct');
        var bar = card.querySelector('.diaper-bar');
        var pct = typeof data.progress === 'number' ? data.progress : 0;
        if (fill) fill.style.width = pct + '%';
        if (pctLabel) pctLabel.textContent = pct + '%';
        if (bar) bar.setAttribute('aria-valuenow', String(pct));
        var openBtn = card.querySelector('.js-open-diaper');
        if (data.meta_reached) {
          if (openBtn) openBtn.remove();
          var p = document.createElement('p');
          p.className = 'status meta-ok';
          p.textContent = 'META ATINGIDA 💚';
          card.querySelector('.card-body').appendChild(p);
        } else if (openBtn) {
          openBtn.dataset.available = data.available;
        }
        var choosers = card.querySelector('.js-choosers');
        if (choosers && data.chooser) {
          choosers.hidden = false;
          var li = document.createElement('li');
          var name = document.createElement('span');
          name.className = 'chooser-name';
          name.textContent = data.quantity > 1
            ? data.chooser + ' · ' + data.quantity + ' pacotes'
            : data.chooser;
          li.appendChild(name);
          if (data.message) {
            var note = document.createElement('span');
            note.className = 'chooser-note';
            note.textContent = data.message;
            li.appendChild(note);
          }
          choosers.appendChild(li);
        }
      }
      closeModals();
    });
  }

  var lb = document.getElementById('lightbox');
  if (lb) {
    var lbImg = document.getElementById('lightbox-img');
    var lbCap = document.getElementById('lightbox-caption');
    var prevBtn = lb.querySelector('[data-lb-prev]');
    var nextBtn = lb.querySelector('[data-lb-next]');
    var lbItems = [];
    var lbIndex = 0;
    var lbFocus = null;
    var swipeX = null;

    function lbGroup(gallery) {
      if (!gallery) return [];
      return Array.prototype.slice.call(
        document.querySelectorAll('.js-lightbox[data-gallery="' + gallery + '"]')
      );
    }

    function lbShow(i) {
      if (!lbItems.length) return;
      lbIndex = (i + lbItems.length) % lbItems.length;
      var btn = lbItems[lbIndex];
      lbImg.src = btn.dataset.src;
      lbImg.alt = btn.dataset.caption || '';
      if (lbCap) lbCap.textContent = btn.dataset.caption || '';
      var multi = lbItems.length > 1;
      if (prevBtn) prevBtn.hidden = !multi;
      if (nextBtn) nextBtn.hidden = !multi;
    }

    function lbOpen(btn) {
      lbFocus = document.activeElement;
      var gallery = btn.dataset.gallery;
      lbItems = gallery ? lbGroup(gallery) : [btn];
      if (lbItems.indexOf(btn) < 0) lbItems = [btn];
      lb.hidden = false;
      lbShow(Math.max(0, lbItems.indexOf(btn)));
      document.body.style.overflow = 'hidden';
      var closeBtn = lb.querySelector('[data-close-lb]');
      if (closeBtn) closeBtn.focus();
    }

    function lbClose() {
      lb.hidden = true;
      lbImg.src = '';
      document.body.style.overflow = '';
      if (prevBtn) prevBtn.hidden = true;
      if (nextBtn) nextBtn.hidden = true;
      if (lbFocus && lbFocus.focus) lbFocus.focus();
    }

    document.querySelectorAll('.js-lightbox').forEach(function (btn) {
      btn.addEventListener('click', function () { lbOpen(btn); });
    });
    document.querySelectorAll('[data-close-lb]').forEach(function (el) {
      el.addEventListener('click', lbClose);
    });
    if (prevBtn) prevBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      lbShow(lbIndex - 1);
    });
    if (nextBtn) nextBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      lbShow(lbIndex + 1);
    });
    lb.addEventListener('click', function (e) {
      if (e.target === lb) lbClose();
    });
    document.addEventListener('keydown', function (e) {
      if (lb.hidden) return;
      if (e.key === 'Escape') lbClose();
      if (e.key === 'ArrowLeft') lbShow(lbIndex - 1);
      if (e.key === 'ArrowRight') lbShow(lbIndex + 1);
    });
    lb.addEventListener('touchstart', function (e) {
      if (e.changedTouches && e.changedTouches[0]) swipeX = e.changedTouches[0].clientX;
    }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (swipeX == null || !e.changedTouches || !e.changedTouches[0]) return;
      var dx = e.changedTouches[0].clientX - swipeX;
      swipeX = null;
      if (Math.abs(dx) < 40) return;
      if (dx > 0) lbShow(lbIndex - 1);
      else lbShow(lbIndex + 1);
    }, { passive: true });
  }
})();
