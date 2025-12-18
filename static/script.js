/* --- Main + Issue Page + Block Selector (Admin Only) --- */
document.addEventListener("DOMContentLoaded", () => {

  /* 🟢 Hamburger Menu */
  const btn = document.querySelector(".menu-btn");
  const panel = document.getElementById("sidePanel");
  const overlay = document.getElementById("overlay");

  if (btn && panel && overlay) {
    btn.addEventListener("click", () => {
      panel.classList.toggle("open");
      overlay.classList.toggle("show");

      if (panel.classList.contains("open")) {
        panel.querySelectorAll("a").forEach((link, i) => {
          link.style.animation = "none";
          setTimeout(() => { link.style.animation = ""; }, 10);
        });
      }
    });

    overlay.addEventListener("click", () => {
      panel.classList.remove("open");
      overlay.classList.remove("show");
    });
  }

  /* 🟢 Page Viewer System */
  const viewers = {};

  function initViewer(viewerId) {
    const viewer = document.getElementById(viewerId);
    if (!viewer) return;
    const pages = Array.from(viewer.querySelectorAll(".page"));
    if (!pages.length) return;

    viewer.style.position = viewer.style.position || "relative";

    const pageNumberEl = document.getElementById(`${viewerId}-pageNumber`);
    const dotsEl = document.getElementById(`${viewerId}-dots`);
    const leftBtn = viewer.querySelector('.nav-btn.left[data-viewer="' + viewerId + '"]');
    const rightBtn = viewer.querySelector('.nav-btn.right[data-viewer="' + viewerId + '"]');

    let state = { current: 0 };

    function renderPage(idx) {
      idx = (idx + pages.length) % pages.length;
      state.current = idx;
      pages.forEach((p, i) => p.style.display = (i === idx ? "block" : "none"));
      if (pageNumberEl) pageNumberEl.textContent = `Page ${idx + 1} / ${pages.length}`;
      if (dotsEl) updateDots(idx);
    }

    function prev() { renderPage(state.current - 1); }
    function next() { renderPage(state.current + 1); }
    function goTo(i) { renderPage(i); }

    function createDots() {
      if (!dotsEl) return;
      dotsEl.innerHTML = "";
      pages.forEach((_, i) => {
        const d = document.createElement("span");
        d.className = "dot";
        d.dataset.index = i;
        d.addEventListener("click", (e) => { e.stopPropagation(); goTo(i); });
        dotsEl.appendChild(d);
      });
    }

    function updateDots(activeIdx) {
      if (!dotsEl) return;
      Array.from(dotsEl.children).forEach((d, i) => d.classList.toggle("active", i === activeIdx));
    }

    if (leftBtn) leftBtn.addEventListener("click", (e) => { e.stopPropagation(); prev(); });
    if (rightBtn) rightBtn.addEventListener("click", (e) => { e.stopPropagation(); next(); });

    let touchStartX = 0;
    viewer.addEventListener("touchstart", (e) => { touchStartX = e.changedTouches[0].screenX; });
    viewer.addEventListener("touchend", (e) => {
      const diff = e.changedTouches[0].screenX - touchStartX;
      if (Math.abs(diff) > 50) { diff > 0 ? prev() : next(); }
    });

    viewer.addEventListener("click", () => next());

    createDots();
    renderPage(0);
    viewers[viewerId] = { renderPage, prev, next, goTo, pagesCount: pages.length };
  }

  ["pageViewer", "todaysViewer", "tumkurViewer"].forEach(initViewer);

  /* 🟢 Issue Page Navigation */
  document.querySelectorAll('.page-viewer').forEach(viewer => {
    let pages = viewer.querySelectorAll('.page-container');
    let current = 0;

    function showPage(idx) {
      pages.forEach(p => p.style.display = 'none');
      if (pages[idx]) pages[idx].style.display = 'inline-block';
    }

    showPage(current);

    const leftBtn = viewer.querySelector('.nav-btn.left');
    const rightBtn = viewer.querySelector('.nav-btn.right');

    if (leftBtn) {
      leftBtn.addEventListener('click', () => {
        current = (current - 1 + pages.length) % pages.length;
        showPage(current);
      });
    }

    if (rightBtn) {
      rightBtn.addEventListener('click', () => {
        current = (current + 1) % pages.length;
        showPage(current);
      });
    }
  });

  /* 🟢 Highlight effect on mobile tap */
  document.querySelectorAll('.block-overlay').forEach(block => {
    block.addEventListener('touchstart', () => {
      block.style.border = '2px dashed rgba(0,0,0,0.9)';
      block.style.backgroundColor = 'rgba(50,50,50,0.25)';
      setTimeout(() => {
        block.style.border = 'none';
        block.style.backgroundColor = 'transparent';
      }, 400);
    });
  });

  /* 🟢 Block Selector (Only if Admin Page with #blocksForm exists) */
  const form = document.getElementById('blocksForm');
  if (form) {
    const pages = document.querySelectorAll('.page-container');

    pages.forEach(container => {
      let blockCounter = 1;
      let startX, startY, tempBlock;
      let scale = 1;
      let lastTouchDist = null;

      function getCoords(e) {
        const rect = container.getBoundingClientRect();
        let x, y;
        if (e.touches && e.touches.length === 1) {
          x = (e.touches[0].clientX - rect.left) / scale;
          y = (e.touches[0].clientY - rect.top) / scale;
        } else if (!e.touches) {
          x = (e.clientX - rect.left) / scale;
          y = (e.clientY - rect.top) / scale;
        }
        return { x, y };
      }

      function startBlock(e) {
        if (e.touches && e.touches.length > 1) {
          const dx = e.touches[0].clientX - e.touches[1].clientX;
          const dy = e.touches[0].clientY - e.touches[1].clientY;
          lastTouchDist = Math.hypot(dx, dy);
          return;
        }
        e.preventDefault();
        const coords = getCoords(e);
        startX = coords.x;
        startY = coords.y;
        tempBlock = document.createElement('div');
        tempBlock.classList.add('block');
        tempBlock.dataset.block = blockCounter;
        tempBlock.style.left = startX + 'px';
        tempBlock.style.top = startY + 'px';
        tempBlock.style.width = '0px';
        tempBlock.style.height = '0px';
        container.appendChild(tempBlock);
      }

      function moveBlock(e) {
        if (e.touches && e.touches.length > 1 && lastTouchDist !== null) {
          const dx = e.touches[0].clientX - e.touches[1].clientX;
          const dy = e.touches[0].clientY - e.touches[1].clientY;
          const dist = Math.hypot(dx, dy);
          scale *= dist / lastTouchDist;
          scale = Math.min(Math.max(scale, 0.5), 3);
          container.style.transform = `scale(${scale})`;
          lastTouchDist = dist;
          return;
        }
        if (!tempBlock) return;
        const coords = getCoords(e);
        const width = coords.x - startX;
        const height = coords.y - startY;
        tempBlock.style.width = Math.abs(width) + 'px';
        tempBlock.style.height = Math.abs(height) + 'px';
        tempBlock.style.left = (width < 0 ? coords.x : startX) + 'px';
        tempBlock.style.top = (height < 0 ? coords.y : startY) + 'px';
      }

      function endBlock(e) {
        if (e.touches && e.touches.length > 1) {
          lastTouchDist = null;
          return;
        }
        if (!tempBlock) return;
        blockCounter++;
        tempBlock = null;
      }

      container.addEventListener('mousedown', startBlock);
      container.addEventListener('mousemove', moveBlock);
      container.addEventListener('mouseup', endBlock);

      container.addEventListener('wheel', e => {
        e.preventDefault();
        const rect = container.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left) / scale;
        const mouseY = (e.clientY - rect.top) / scale;
        const delta = -e.deltaY * 0.001;
        const newScale = Math.min(Math.max(scale + delta, 0.5), 3);
        const originX = mouseX;
        const originY = mouseY;
        container.style.transformOrigin = `${originX}px ${originY}px`;
        scale = newScale;
        container.style.transform = `scale(${scale})`;
      });

      container.addEventListener('touchstart', startBlock);
      container.addEventListener('touchmove', moveBlock);
      container.addEventListener('touchend', endBlock);
    });

    /* 🟢 Form Submit - Save Blocks */
    form.addEventListener('submit', e => {
      e.preventDefault();
      const blocksData = [];
      pages.forEach(container => {
        const pageId = container.dataset.pageId;
        container.querySelectorAll('.block').forEach(b => {
          blocksData.push({
            page_id: parseInt(pageId),
            x: (b.offsetLeft / container.clientWidth) * 100,
            y: (b.offsetTop / container.clientHeight) * 100,
            width: (b.offsetWidth / container.clientWidth) * 100,
            height: (b.offsetHeight / container.clientHeight) * 100
          });
        });
      });
      let input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'blocks_data';
      input.value = JSON.stringify(blocksData);
      form.appendChild(input);
      form.submit();
    });
  }

});
