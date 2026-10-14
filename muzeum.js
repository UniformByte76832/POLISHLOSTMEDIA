/**
 * Muzeum Archeologii Cyfrowej: Logika Aplikacji
 * Obsługa emulatora Ruffle, szafy grającej MIDI, galerii z lightboxem oraz katalogu zbiorów.
 */

document.addEventListener("DOMContentLoaded", () => {
  const data = window.MUSEUM_DATA || [];
  console.log(`Załadowano ${data.length} artefaktów do Muzeum.`);

  // Inicjalizacja statystyk w nagłówku
  const totalCount = data.length;
  const swfCount = data.filter(d => d.format === 'SWF').length;
  const midiCount = data.filter(d => d.format === 'MIDI').length;
  const imgCount = data.filter(d => ['GIF', 'JPEG', 'BMP'].includes(d.format)).length;

  document.getElementById("stat-total").textContent = totalCount;
  document.getElementById("stat-swf").textContent = swfCount;
  document.getElementById("stat-midi").textContent = midiCount;
  document.getElementById("stat-img").textContent = imgCount;

  // 1. Obsługa Zakładek (Nawigacja)
  const navBtns = document.querySelectorAll(".nav-btn");
  const sections = document.querySelectorAll(".museum-section");

  navBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.tab;
      navBtns.forEach(b => b.classList.remove("active"));
      sections.forEach(s => s.classList.remove("active"));

      btn.classList.add("active");
      const targetSec = document.getElementById(targetId);
      if (targetSec) targetSec.classList.add("active");
    });
  });

  // 2. Obsługa Ruffle (Salon Gier & Kino Flash)
  let rufflePlayer = null;
  const ruffleContainer = document.getElementById("ruffle-container");
  const currentTitleEl = document.getElementById("current-stage-title");
  const currentDescEl = document.getElementById("current-stage-desc");

  function initRuffle(initialSwfPath, title, desc) {
    if (!ruffleContainer) return;
    ruffleContainer.innerHTML = "";

    try {
      if (window.RufflePlayer) {
        const ruffle = window.RufflePlayer.newest();
        rufflePlayer = ruffle.createPlayer();
        ruffleContainer.appendChild(rufflePlayer);
        rufflePlayer.load(initialSwfPath);
        if (currentTitleEl) currentTitleEl.textContent = title;
        if (currentDescEl) currentDescEl.textContent = desc;
      } else {
        // Fallback gdy Ruffle CDN nie załaduje się
        ruffleContainer.innerHTML = `
          <div style="text-align: center; padding: 40px; color: #8b9bb4;">
            <p style="font-size: 1.1rem; color: #00f0ff; margin-bottom: 12px;">⚡ Plik Flash: ${title}</p>
            <p style="margin-bottom: 20px;">Lokalizacja: <code>${initialSwfPath}</code></p>
            <a href="${initialSwfPath}" download class="btn-action btn-primary">Pobierz plik SWF</a>
            <p style="font-size: 0.8rem; margin-top: 15px;">Wskazówka: Możesz uruchomić ten plik za pomocą <code>flashplayer_32_sa.exe</code> znajdującego się w folderze znalezisk.</p>
          </div>
        `;
      }
    } catch (err) {
      console.warn("Błąd ładowania Ruffle:", err);
    }
  }

  // Załaduj domyślnie najstarszą polską grę Flash: Batyskaf (Czerwiec 2002)
  const defaultGame = data.find(d => d.filename.includes("batyskaf")) || data.find(d => d.filename.includes("snakearena")) || data.find(d => d.format === "SWF");
  if (defaultGame) {
    initRuffle(defaultGame.rel_path, defaultGame.title, defaultGame.desc);
  }

  // Przyciski kontroli odtwarzacza
  document.getElementById("btn-restart-swf")?.addEventListener("click", () => {
    if (rufflePlayer && rufflePlayer.reload) rufflePlayer.reload();
  });
  document.getElementById("btn-fullscreen-swf")?.addEventListener("click", () => {
    if (rufflePlayer && rufflePlayer.enterFullscreen) rufflePlayer.enterFullscreen();
  });

  // Lista gier w panelu bocznym salonu gier (uporządkowana chronologicznie)
  const arcadeList = document.getElementById("arcade-playlist");
  const arcadeGames = data.filter(d => d.wing === 'arcade').sort((a, b) => (a.year || '2000').localeCompare(b.year || '2000'));
  const otherSwfs = data.filter(d => d.format === 'SWF' && d.wing !== 'arcade');
  const arcadeItems = [...arcadeGames, ...otherSwfs.slice(0, 15)].filter(Boolean);

  if (arcadeList) {
    arcadeList.innerHTML = "";
    arcadeItems.forEach((item, idx) => {
      const card = document.createElement("div");
      card.className = `list-card ${idx === 0 ? 'active' : ''}`;
      card.innerHTML = `
        <div class="list-card-title">${item.title}</div>
        <div class="list-card-meta">
          <span>${item.domain}</span>
          <span>${item.size_str}</span>
        </div>
      `;
      card.addEventListener("click", () => {
        document.querySelectorAll("#arcade-playlist .list-card").forEach(c => c.classList.remove("active"));
        card.classList.add("active");
        initRuffle(item.rel_path, item.title, item.desc);
      });
      arcadeList.appendChild(card);
    });
  }

  // Kino Flash: Lista animacji
  const cinemaList = document.getElementById("cinema-playlist");
  const cinemaItems = data.filter(d => d.format === 'SWF' && d.wing === 'cinema');
  if (cinemaList) {
    cinemaList.innerHTML = "";
    cinemaItems.forEach((item, idx) => {
      const card = document.createElement("div");
      card.className = "list-card";
      card.innerHTML = `
        <div class="list-card-title">${item.title || item.filename}</div>
        <div class="list-card-meta">
          <span>${item.domain}</span>
          <span>${item.size_str}</span>
        </div>
      `;
      card.addEventListener("click", () => {
        // Przełącz widok do sceny i odtwórz
        document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".museum-section").forEach(s => s.classList.remove("active"));
        document.querySelector('[data-tab="tab-arcade"]').classList.add("active");
        document.getElementById("tab-arcade").classList.add("active");
        initRuffle(item.rel_path, item.title || `Animacja: ${item.filename}`, item.desc);
      });
      cinemaList.appendChild(card);
    });
  }

  // 3. Szafa Grająca MIDI (Jukebox)
  const midiItems = data.filter(d => d.format === 'MIDI');
  const jukeboxList = document.getElementById("jukebox-playlist");
  const currentMidiTitle = document.getElementById("current-midi-title");
  const currentMidiMeta = document.getElementById("current-midi-meta");
  const btnPlayMidi = document.getElementById("btn-play-midi");
  const reels = document.querySelectorAll(".reel");
  const vuBars = document.querySelectorAll(".vu-bar");

  let isPlayingMidi = false;
  let activeMidiItem = midiItems[0] || null;
  let vuInterval = null;

  function updateMidiTrack(item) {
    activeMidiItem = item;
    if (currentMidiTitle) currentMidiTitle.textContent = item.title;
    if (currentMidiMeta) currentMidiMeta.textContent = `${item.domain} • ${item.date_str} • ${item.size_str}`;
    const directLink = document.getElementById("btn-download-midi");
    if (directLink) directLink.href = item.rel_path;
  }

  function startVuAnimation() {
    if (vuInterval) clearInterval(vuInterval);
    reels.forEach(r => r.classList.add("spinning"));
    vuInterval = setInterval(() => {
      vuBars.forEach(bar => {
        const h = Math.floor(Math.random() * 85) + 15;
        bar.style.height = `${h}%`;
        if (h > 60) bar.classList.add("active");
        else bar.classList.remove("active");
      });
    }, 120);
  }

  function stopVuAnimation() {
    if (vuInterval) clearInterval(vuInterval);
    reels.forEach(r => r.classList.remove("spinning"));
    vuBars.forEach(bar => {
      bar.style.height = '15%';
      bar.classList.remove("active");
    });
  }

  if (btnPlayMidi) {
    btnPlayMidi.addEventListener("click", () => {
      isPlayingMidi = !isPlayingMidi;
      if (isPlayingMidi) {
        btnPlayMidi.textContent = "⏸";
        startVuAnimation();
        // Sprawdź czy dostępny jest natywny midi-player
        const playerTag = document.getElementById("embedded-midi-player");
        if (playerTag && activeMidiItem) {
          playerTag.src = activeMidiItem.rel_path;
          playerTag.start && playerTag.start();
        }
      } else {
        btnPlayMidi.textContent = "▶";
        stopVuAnimation();
        const playerTag = document.getElementById("embedded-midi-player");
        if (playerTag && playerTag.stop) playerTag.stop();
      }
    });
  }

  if (jukeboxList) {
    jukeboxList.innerHTML = "";
    midiItems.forEach((item, idx) => {
      const card = document.createElement("div");
      card.className = `list-card ${idx === 0 ? 'active' : ''}`;
      card.innerHTML = `
        <div class="list-card-title">${item.title}</div>
        <div class="list-card-meta">
          <span>${item.domain}</span>
          <span>${item.size_str}</span>
        </div>
      `;
      card.addEventListener("click", () => {
        document.querySelectorAll("#jukebox-playlist .list-card").forEach(c => c.classList.remove("active"));
        card.classList.add("active");
        updateMidiTrack(item);
        if (isPlayingMidi) {
          startVuAnimation();
          const playerTag = document.getElementById("embedded-midi-player");
          if (playerTag) {
            playerTag.src = item.rel_path;
            playerTag.start && playerTag.start();
          }
        }
      });
      jukeboxList.appendChild(card);
    });
    if (activeMidiItem) updateMidiTrack(activeMidiItem);
  }

  // 4. Wystawa Grafik (Galeria i Lightbox)
  const galleryGrid = document.getElementById("gallery-grid");
  const lightbox = document.getElementById("lightbox-modal");
  const lightboxImg = document.getElementById("lightbox-img");
  const lightboxTitle = document.getElementById("lightbox-title");
  const lightboxMeta = document.getElementById("lightbox-meta");
  const lightboxClose = document.getElementById("lightbox-close");
  const lightboxOrig = document.getElementById("lightbox-orig");

  const imageItems = data.filter(d => ['GIF', 'JPEG', 'BMP'].includes(d.format));

  if (galleryGrid) {
    galleryGrid.innerHTML = "";
    imageItems.forEach(item => {
      const card = document.createElement("div");
      card.className = "gallery-card";
      card.innerHTML = `
        <div class="gallery-thumb-wrap">
          <img src="${item.rel_path}" alt="${item.filename}" loading="lazy">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">${item.filename}</div>
          <div class="gallery-meta">
            <span>${item.domain}</span>
            <span>${item.size_str}</span>
          </div>
        </div>
      `;
      card.addEventListener("click", () => {
        if (lightbox && lightboxImg) {
          lightboxImg.src = item.rel_path;
          lightboxTitle.textContent = item.filename;
          lightboxMeta.textContent = `${item.details} • ${item.date_str} • ${item.size_str}`;
          if (lightboxOrig) lightboxOrig.href = item.original_url;
          lightbox.classList.add("active");
        }
      });
      galleryGrid.appendChild(card);
    });
  }

  if (lightboxClose) {
    lightboxClose.addEventListener("click", () => lightbox.classList.remove("active"));
    lightbox.addEventListener("click", (e) => {
      if (e.target === lightbox) lightbox.classList.remove("active");
    });
  }

  // 5. Główny Katalog (Tabela z Wyszukiwarką i Filtrami)
  const tableBody = document.getElementById("catalog-table-body");
  const searchInput = document.getElementById("catalog-search");
  const filterFormat = document.getElementById("filter-format");
  const filterDomain = document.getElementById("filter-domain");

  function renderTable(filteredData) {
    if (!tableBody) return;
    tableBody.innerHTML = "";

    const rows = filteredData.slice(0, 100); // Pierwsze 100 wyników dla optymalizacji
    rows.forEach(item => {
      const tr = document.createElement("tr");
      const fmtColor = item.format === 'SWF' ? 'var(--neon-cyan)' :
                       item.format === 'MIDI' ? 'var(--neon-magenta)' : 'var(--neon-amber)';

      tr.innerHTML = `
        <td style="font-family: var(--font-mono); font-weight: bold; color: ${fmtColor};">${item.format}</td>
        <td>
          <a href="${item.rel_path}" target="_blank" style="color: var(--text-main); font-weight: 600; text-decoration: none;">
            ${item.filename}
          </a>
          <div style="font-size: 0.78rem; color: var(--text-muted);">${item.details}</div>
        </td>
        <td style="font-family: var(--font-mono); font-size: 0.8rem;">${item.size_str}</td>
        <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted);">${item.date_str}</td>
        <td><span class="badge">${item.domain}</span></td>
        <td>
          <a href="${item.archive_url}" target="_blank" class="btn-action" style="padding: 4px 8px; font-size: 0.75rem;">
            Wayback ↗
          </a>
        </td>
      `;
      tableBody.appendChild(tr);
    });

    const countEl = document.getElementById("catalog-count");
    if (countEl) countEl.textContent = `Wyświetlono ${rows.length} z ${filteredData.length} znalezionych`;
  }

  function applyFilters() {
    const q = (searchInput?.value || "").toLowerCase();
    const fmt = filterFormat?.value || "all";
    const dom = filterDomain?.value || "all";

    const filtered = data.filter(it => {
      const matchQ = it.filename.toLowerCase().includes(q) ||
                     it.title.toLowerCase().includes(q) ||
                     it.desc.toLowerCase().includes(q) ||
                     it.domain.toLowerCase().includes(q);
      const matchFmt = fmt === 'all' || it.format === fmt;
      const matchDom = dom === 'all' || it.domain === dom;
      return matchQ && matchFmt && matchDom;
    });

    renderTable(filtered);
  }

  searchInput?.addEventListener("input", applyFilters);
  filterFormat?.addEventListener("change", applyFilters);
  filterDomain?.addEventListener("change", applyFilters);

  // Pierwsze renderowanie tabeli
  renderTable(data);
});
