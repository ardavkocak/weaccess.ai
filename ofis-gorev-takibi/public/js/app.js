
/*
 * Arayüz etkileşimleri.
 *
 * Uygulama sunucu tarafında render edilir; burada yalnızca ilerici geliştirme
 * (progressive enhancement) niteliğinde küçük davranışlar vardır. JavaScript
 * çalışmasa bile tüm formlar ve bağlantılar çalışmaya devam eder.
 */

(function () {
  'use strict';

  /* ---------- Mobil menü ---------- */
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const toggle = document.getElementById('sidebar-toggle');

  function openSidebar() {
    sidebar.classList.remove('-translate-x-full');
    overlay.classList.remove('hidden');
    toggle.setAttribute('aria-expanded', 'true');
    // Menü açıkken arka planın kaymasını engelle.
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar.classList.add('-translate-x-full');
    overlay.classList.add('hidden');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  if (sidebar && overlay && toggle) {
    toggle.addEventListener('click', () => {
      const isOpen = toggle.getAttribute('aria-expanded') === 'true';
      if (isOpen) closeSidebar();
      else openSidebar();
    });

    overlay.addEventListener('click', closeSidebar);

    // Esc ile kapat.
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        closeSidebar();
      }
    });

    // Masaüstü genişliğine geçildiğinde mobil durumu sıfırla.
    window.matchMedia('(min-width: 1024px)').addEventListener('change', (event) => {
      if (event.matches) {
        overlay.classList.add('hidden');
        document.body.style.overflow = '';
        toggle.setAttribute('aria-expanded', 'false');
        // Masaüstünde menü lg:translate-x-0 ile zaten görünür.
        sidebar.classList.add('-translate-x-full');
      }
    });
  }

  /* ---------- Onay gerektiren formlar ---------- */
  // data-confirm="..." taşıyan formlar gönderilmeden önce kullanıcıya sorar.
  // Böylece "sil" veya "sırayı geç" gibi işlemler yanlışlıkla tetiklenmez.
  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!window.confirm(form.dataset.confirm)) {
        event.preventDefault();
      }
    });
  });

  /* ---------- Çift gönderim koruması ---------- */
  // Discord'a mesaj gönderme gibi işlemler birkaç saniye sürebilir; kullanıcı
  // sabırsızlanıp ikinci kez tıklamasın.
  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      // data-confirm iptal edilmişse buraya gelinmez (submit olayı engellenir).
      const button = form.querySelector('button[type="submit"]');
      if (!button || button.disabled) return;

      // Sunucu yanıtı gelmezse buton sonsuza dek kilitli kalmasın.
      setTimeout(() => {
        button.disabled = true;
        button.classList.add('opacity-60', 'cursor-wait');
      }, 0);
    });
  });

  /* ---------- Görev sırası: sürükle-bırak ---------- */
  /*
   * İlerici geliştirme: JavaScript yoksa bu blok hiç çalışmaz ve sıralama
   * satırlardaki yukarı/aşağı okları ile sıra numarası kutusundan yapılmaya
   * devam eder (ikisi de normal form gönderimidir).
   *
   * Pointer Events kullanılır; böylece aynı kod hem fare hem dokunmatik için
   * çalışır (HTML5 drag-and-drop dokunmatikte çalışmaz).
   */
  const queueList = document.getElementById('queue-list');
  const reorderBar = document.getElementById('reorder-bar');
  const reorderInput = document.getElementById('reorder-input');
  const reorderSave = document.getElementById('reorder-save');

  if (queueList && reorderBar && reorderInput && reorderSave) {
    const rowsOf = () => Array.from(queueList.querySelectorAll('.queue-row'));
    const currentOrder = () => rowsOf().map((row) => row.dataset.employeeId);
    const initialOrder = currentOrder().join(',');

    // Sürükleme arayüzünü görünür kıl (sunucu tarafında gizli geliyor).
    reorderBar.classList.remove('hidden');
    reorderBar.classList.add('flex');
    queueList.querySelectorAll('.drag-handle').forEach((handle) => {
      handle.classList.remove('hidden');
      handle.classList.add('block');
    });

    // Satır numaralarını ve numara kutularını ekrandaki sıraya göre tazele.
    function refreshRanks() {
      rowsOf().forEach((row, index) => {
        const rank = row.querySelector('.queue-rank');
        if (rank) rank.textContent = String(index + 1);
        const input = row.querySelector('.queue-position');
        if (input) input.value = String(index + 1);
      });

      const order = currentOrder();
      reorderInput.value = order.join(',');

      // Sıra başlangıçtakiyle aynıysa kaydedilecek bir şey yok.
      const isDirty = order.join(',') !== initialOrder;
      reorderSave.disabled = !isDirty;

      // Kaydedilmemiş sürükleme varken ekrandaki sıra ile sunucudaki sıra
      // farklıdır; numara kutusu ve oklar sunucudaki sıraya göre çalıştığı için
      // beklenmedik sonuç verirdi. Kaydedilene kadar kapalı tutulurlar.
      rowsOf().forEach((row) => {
        const input = row.querySelector('.queue-position');
        if (input) {
          input.disabled = isDirty;
          input.title = isDirty
            ? 'Önce sıralamayı kaydedin'
            : "Sıra numarasını değiştirip Enter'a basın";
        }
        row.querySelectorAll('.move-button').forEach((button) => {
          // Uçtaki oklar zaten sunucu tarafından devre dışı bırakılmış olabilir.
          if (isDirty) button.disabled = true;
          else if (button.dataset.edge !== '1') button.disabled = false;
        });
      });
    }

    let draggedRow = null;

    function onPointerMove(event) {
      if (!draggedRow) return;
      event.preventDefault(); // Dokunmatikte sayfanın kaymasını engelle.

      const y = event.clientY;
      for (const row of rowsOf()) {
        if (row === draggedRow) continue;
        const box = row.getBoundingClientRect();
        if (y < box.top || y > box.bottom) continue;

        // İmleç komşunun orta çizgisini geçtiyse yer değiştir.
        if (y > box.top + box.height / 2) row.after(draggedRow);
        else row.before(draggedRow);
        break;
      }
    }

    function endDrag() {
      if (!draggedRow) return;
      draggedRow.classList.remove('is-dragging');
      document.body.classList.remove('queue-reordering');
      draggedRow = null;
      refreshRanks();
    }

    queueList.querySelectorAll('.drag-handle').forEach((handle) => {
      handle.addEventListener('pointerdown', (event) => {
        // Yalnızca birincil düğme/dokunuş sürüklemeyi başlatsın.
        if (event.button !== 0) return;
        event.preventDefault();

        draggedRow = handle.closest('.queue-row');
        if (!draggedRow) return;

        draggedRow.classList.add('is-dragging');
        document.body.classList.add('queue-reordering');
        // Yakalama: imleç satırdan çıksa bile olaylar bu tutamağa gelir.
        handle.setPointerCapture(event.pointerId);
      });

      handle.addEventListener('pointermove', onPointerMove);
      handle.addEventListener('pointerup', endDrag);
      handle.addEventListener('pointercancel', endDrag);
    });

    // Sürükleme sonrası sayfadan ayrılırken kaydedilmemiş sıra uyarısı.
    window.addEventListener('beforeunload', (event) => {
      if (reorderSave.disabled || reorderSave.dataset.saving === '1') return;
      event.preventDefault();
      event.returnValue = '';
    });

    document.getElementById('reorder-form').addEventListener('submit', () => {
      reorderSave.dataset.saving = '1'; // Kaydediliyor: uyarı çıkmasın.
    });
  }

  /* ---------- Flash mesajlarını kapatma ---------- */
  document.querySelectorAll('.flash-close').forEach((button) => {
    button.addEventListener('click', () => {
      const message = button.closest('.flash-message');
      message.classList.add('is-closing');
      setTimeout(() => message.remove(), 200);
    });
  });
})();
