window.GameStatsUI = (function () {
  const CFG = window.APP_CONFIG || {
    apiBase: "/api",
    gamesEndpoint: "/api/games",
    authRegisterEndpoint: "/api/auth/register",
    authTokenEndpoint: "/api/auth/token",
    storageKeys: { token: "access_token", gameId: "selected_game_id" },
  };

  // -------------------------
  // Storage helpers
  // -------------------------
  function getToken() {
    return localStorage.getItem(CFG.storageKeys.token) || "";
  }
  function setToken(token) {
    if (token) localStorage.setItem(CFG.storageKeys.token, token);
    else localStorage.removeItem(CFG.storageKeys.token);
  }
  function getSelectedGameId() {
    const v = localStorage.getItem(CFG.storageKeys.gameId);
    if (!v) return null;
    const n = parseInt(v, 10);
    return Number.isFinite(n) ? n : null;
  }
  function setSelectedGameId(gameId) {
    if (gameId === null || gameId === undefined || gameId === "") {
      localStorage.removeItem(CFG.storageKeys.gameId);
      return;
    }
    localStorage.setItem(CFG.storageKeys.gameId, String(gameId));
  }

  // -------------------------
  // UI helpers
  // -------------------------
  function $(sel) {
    return document.querySelector(sel);
  }

  function show(el) {
    if (!el) return;
    el.style.display = "";
  }
  function hide(el) {
    if (!el) return;
    el.style.display = "none";
  }

  function setText(el, text) {
    if (!el) return;
    el.textContent = text ?? "";
  }

  function setBadge(game) {
    const badge = $("#selected-game-badge");
    if (!badge) return;

    const gameId = getSelectedGameId();
    if (!gameId || !game) {
      hide(badge);
      return;
    }
    badge.textContent = `Game: ${game.name}`;
    show(badge);
  }

  function showGameRequiredWarningIfNeeded() {
    const warn = $("#game-required-warning");
    if (!warn) return false;
    const gameId = getSelectedGameId();
    if (!gameId) {
      show(warn);
      return true;
    }
    hide(warn);
    return false;
  }

  // -------------------------
  // HTTP helpers
  // -------------------------
  async function apiFetch(path, options = {}) {
    const url = path.startsWith("http") ? path : path;
    const headers = new Headers(options.headers || {});
    headers.set("Accept", "application/json");

    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);

    // Если есть body и это не FormData — ставим JSON
    if (options.body && !(options.body instanceof FormData)) {
      if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    }

    const resp = await fetch(url, { ...options, headers });
    return resp;
  }

  async function apiJson(path, options = {}) {
    const resp = await apiFetch(path, options);
    if (!resp.ok) {
      let details = "";
      try {
        const data = await resp.json();
        details = data?.detail ? `: ${data.detail}` : "";
      } catch (_) {
        // ignore
      }
      throw new Error(`Request failed (${resp.status})${details}`);
    }
    if (resp.status === 204) return null;
    return await resp.json();
  }

  function gameScoped(pathTemplate) {
    // pathTemplate пример: `/api/games/{gameId}/players`
    const gameId = getSelectedGameId();
    if (!gameId) return null;
    return pathTemplate.replace("{gameId}", String(gameId));
  }

  // -------------------------
  // Auth UI
  // -------------------------
function openAuthModal(mode /* 'login' | 'register' */) {
    const modal = $("#authModal");
    const title = $("#authModalTitle");
    const hint = $("#authModalHint");
    const err = $("#authError");
    const submit = $("#authSubmit");

    if (!modal || !title || !hint || !submit) return;

    if (err) { err.style.display = "none"; err.textContent = ""; }

    const u = $("#authUsername");
    const p = $("#authPassword");
    if (u) u.value = "";
    if (p) p.value = "";

    if (mode === "register") {
        title.textContent = "Register";
        hint.textContent = "Create a new account (username + password).";
        submit.dataset.mode = "register";
    } else {
        title.textContent = "Login";
        hint.textContent = "Enter your username and password to get access token.";
        submit.dataset.mode = "login";
    }

    // ✅ ЖЕЛЕЗОБЕТОННО показываем и поднимаем наверх
    modal.style.display = "block";
    modal.style.visibility = "visible";
    modal.style.opacity = "1";
    modal.style.pointerEvents = "auto";
    modal.style.zIndex = "2147483647";
}

function closeAuthModal() {
    const modal = $("#authModal");
    if (!modal) return;
    modal.style.display = "none";
}

  async function doRegister(username, password) {
    const payload = { username, password };
    // POST /api/auth/register
    return await apiJson(CFG.authRegisterEndpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async function doLogin(username, password) {
    // OAuth2PasswordRequestForm: x-www-form-urlencoded
    const form = new URLSearchParams();
    form.set("username", username);
    form.set("password", password);

    const resp = await fetch(CFG.authTokenEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json" },
      body: form.toString(),
    });

    if (!resp.ok) {
      let details = "";
      try {
        const data = await resp.json();
        details = data?.detail ? `: ${data.detail}` : "";
      } catch (_) {}
      throw new Error(`Login failed (${resp.status})${details}`);
    }
    return await resp.json(); // {access_token, token_type}
  }

  function syncAuthButtons() {
    const token = getToken();
    const statusEl = $("#authStatus");
    const btnLogin = $("#btnLogin");
    const btnRegister = $("#btnRegister");
    const btnLogout = $("#btnLogout");

    if (!btnLogin || !btnRegister || !btnLogout) return;

    if (token) {
      setText(statusEl, "Logged in");
      hide(btnLogin);
      hide(btnRegister);
      show(btnLogout);
    } else {
      setText(statusEl, "");
      show(btnLogin);
      show(btnRegister);
      hide(btnLogout);
    }
  }

  function initAuthUI() {
    const btnLogin = $("#btnLogin");
    const btnRegister = $("#btnRegister");
    const btnLogout = $("#btnLogout");
    const modalClose = $("#authModalClose");
    const modal = $("#authModal");
    const submit = $("#authSubmit");

    if (btnLogin) btnLogin.addEventListener("click", () => openAuthModal("login"));
    if (btnRegister) btnRegister.addEventListener("click", () => openAuthModal("register"));

    if (btnLogout) {
      btnLogout.addEventListener("click", () => {
        setToken("");
        syncAuthButtons();
        alert("Logged out");
      });
    }

    if (modalClose) modalClose.addEventListener("click", closeAuthModal);

    // клик по затемнению — закрывает
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) closeAuthModal();
      });
    }

    if (submit) {
      submit.addEventListener("click", async () => {
        const mode = submit.dataset.mode || "login";
        const username = ($("#authUsername").value || "").trim();
        const password = ($("#authPassword").value || "").trim();
        const err = $("#authError");

        if (!username || !password) {
          if (err) {
            err.textContent = "Username and password are required.";
            show(err);
          }
          return;
        }

        try {
          hide(err);

          if (mode === "register") {
            await doRegister(username, password);
            // после регистрации — сразу логинимся
            const tokenResp = await doLogin(username, password);
            setToken(tokenResp.access_token);
          } else {
            const tokenResp = await doLogin(username, password);
            setToken(tokenResp.access_token);
          }

          syncAuthButtons();
          closeAuthModal();
          alert(mode === "register" ? "Registered and logged in" : "Logged in");
        } catch (e) {
          console.error(e);
          if (err) {
            err.textContent = e.message || "Auth error";
            show(err);
          } else {
            alert(e.message);
          }
        }
      });
    }

    syncAuthButtons();
  }

  // -------------------------
  // Games selector
  // -------------------------
  let cachedGames = [];

  async function loadGamesIntoSelector() {
    const selectEl = $("#gameSelect");
    if (!selectEl) return;

    selectEl.innerHTML = `<option value="">Loading…</option>`;

    try {
      const games = await apiJson(CFG.gamesEndpoint);
      cachedGames = Array.isArray(games) ? games : (games.items || []);
      selectEl.innerHTML = `<option value="">— Select game —</option>`;

      cachedGames.forEach((g) => {
        const opt = document.createElement("option");
        opt.value = String(g.id);
        opt.textContent = g.name;
        selectEl.appendChild(opt);
      });

      const saved = getSelectedGameId();
      if (saved) selectEl.value = String(saved);

      // badge
      const selected = cachedGames.find((g) => g.id === saved);
      setBadge(selected || null);
    } catch (e) {
      console.error(e);
      selectEl.innerHTML = `<option value="">(Failed to load games)</option>`;
    }

    selectEl.addEventListener("change", () => {
      const v = selectEl.value;
      setSelectedGameId(v ? parseInt(v, 10) : null);

      const saved = getSelectedGameId();
      const selected = cachedGames.find((g) => g.id === saved);
      setBadge(selected || null);

      // На смену игры: перезагрузка страницы — самый надёжный вариант, чтобы все списки перезапросились
      window.location.reload();
    });
  }

  // -------------------------
  // API (game-scoped)
  // -------------------------
  const api = {
    async getPlayers(offset = 0, limit = 20) {
      const base = gameScoped(`${CFG.apiBase}/games/{gameId}/players`);
      if (!base) throw new Error("Game is not selected");
      const url = `${base}?offset=${offset}&limit=${limit}`;
      return await apiJson(url);
    },

    async getPlayerSummary(playerId) {
      const base = gameScoped(`${CFG.apiBase}/games/{gameId}/players/${playerId}/summary`);
      if (!base) throw new Error("Game is not selected");
      return await apiJson(base);
    },

    async getBattles(params) {
      const base = gameScoped(`${CFG.apiBase}/games/{gameId}/battles`);
      if (!base) throw new Error("Game is not selected");

      const query = new URLSearchParams();
      if (params.player_id) query.set("player_id", params.player_id);
      if (params.is_ranked !== undefined && params.is_ranked !== null) {
        query.set("is_ranked", params.is_ranked ? "true" : "false");
      }
      query.set("offset", params.offset || 0);
      query.set("limit", params.limit || 20);

      const url = `${base}?${query.toString()}`;
      return await apiJson(url);
    },

    async getBattleDetails(battleId) {
      const base = gameScoped(`${CFG.apiBase}/games/{gameId}/battles/${battleId}`);
      if (!base) throw new Error("Game is not selected");
      return await apiJson(base);
    },

    async getPlayerStatsSummary(playerId, rankedOnly) {
      const base = gameScoped(`${CFG.apiBase}/games/{gameId}/stats/players/${playerId}`);
      if (!base) throw new Error("Game is not selected");

      const params = new URLSearchParams();
      if (rankedOnly !== undefined && rankedOnly !== null) {
        params.set("ranked_only", rankedOnly ? "true" : "false");
      }
      return await apiJson(`${base}?${params.toString()}`);
    },

    async getPlayerMapStats(playerId, rankedOnly) {
      const base = gameScoped(`${CFG.apiBase}/games/{gameId}/stats/players/${playerId}/maps`);
      if (!base) throw new Error("Game is not selected");

      const params = new URLSearchParams();
      if (rankedOnly !== undefined && rankedOnly !== null) {
        params.set("ranked_only", rankedOnly ? "true" : "false");
      }
      return await apiJson(`${base}?${params.toString()}`);
    },

    async getPlayerWeaponStats(playerId, rankedOnly) {
      const base = gameScoped(`${CFG.apiBase}/games/{gameId}/stats/players/${playerId}/weapons`);
      if (!base) throw new Error("Game is not selected");

      const params = new URLSearchParams();
      if (rankedOnly !== undefined && rankedOnly !== null) {
        params.set("ranked_only", rankedOnly ? "true" : "false");
      }
      return await apiJson(`${base}?${params.toString()}`);
    },
  };

  // -------------------------
  // Pages
  // -------------------------
  function initPlayersPage() {
    // если игра не выбрана — просто показываем предупреждение и не грузим
    if (showGameRequiredWarningIfNeeded()) return;

    const tableBody = document.querySelector("#players-table tbody");
    const reloadBtn = document.getElementById("reload-players-btn");
    const searchInput = document.getElementById("players-search-input");
    const prevBtn = document.getElementById("players-prev");
    const nextBtn = document.getElementById("players-next");
    const pageInfo = document.getElementById("players-page-info");
    const summaryCard = document.getElementById("player-summary-card");
    const summaryContent = document.getElementById("player-summary-content");

    let offset = 0;
    const limit = 20;
    let lastTotal = 0;
    let allItems = [];

    async function loadPage() {
      try {
        const data = await api.getPlayers(offset, limit);
        lastTotal = data.total || (data.items ? data.items.length : 0);
        allItems = data.items || [];

        renderTable(allItems);
        updatePagination();
      } catch (e) {
        console.error(e);
        alert(e.message);
      }
    }

    function renderTable(items) {
      tableBody.innerHTML = "";
      const filter = (searchInput.value || "").toLowerCase().trim();

      items
        .filter((p) => !filter || (p.nickname || "").toLowerCase().includes(filter))
        .forEach((player) => {
          const tr = document.createElement("tr");

          tr.innerHTML = `
            <td>${player.id}</td>
            <td>${player.nickname}</td>
            <td class="cell-muted">${player.created_at ?? ""}</td>
            <td class="cell-muted">${player.user_id ?? ""}</td>
            <td>
              <button class="btn btn-secondary btn-sm" data-player-id="${player.id}">
                Summary
              </button>
            </td>
          `;

          const btn = tr.querySelector("button[data-player-id]");
          btn.addEventListener("click", async () => {
            try {
              const summary = await api.getPlayerSummary(player.id);
              summaryCard.style.display = "block";
              summaryContent.textContent = JSON.stringify(summary, null, 2);
            } catch (e) {
              console.error(e);
              alert(e.message);
            }
          });

          tableBody.appendChild(tr);
        });
    }

    function updatePagination() {
      const currentPage = Math.floor(offset / limit) + 1;
      const totalPages = lastTotal > 0 ? Math.ceil(lastTotal / limit) : 1;

      pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
      prevBtn.disabled = offset <= 0;
      nextBtn.disabled = offset + limit >= lastTotal;
    }

    reloadBtn.addEventListener("click", loadPage);
    searchInput.addEventListener("input", () => renderTable(allItems));

    prevBtn.addEventListener("click", () => {
      if (offset > 0) {
        offset -= limit;
        loadPage();
      }
    });

    nextBtn.addEventListener("click", () => {
      if (offset + limit < lastTotal) {
        offset += limit;
        loadPage();
      }
    });

    loadPage();
  }

  function initBattlesPage() {
    if (showGameRequiredWarningIfNeeded()) return;

    const tableBody = document.querySelector("#battles-table tbody");
    const reloadBtn = document.getElementById("reload-battles-btn");
    const playerIdInput = document.getElementById("battles-player-id");
    const rankedCheckbox = document.getElementById("battles-ranked-only");
    const prevBtn = document.getElementById("battles-prev");
    const nextBtn = document.getElementById("battles-next");
    const pageInfo = document.getElementById("battles-page-info");
    const detailsCard = document.getElementById("battle-details-card");
    const detailsContent = document.getElementById("battle-details-content");

    let offset = 0;
    const limit = 20;
    let lastTotal = 0;

    async function loadPage() {
      try {
        const params = { offset, limit };
        const playerIdValue = playerIdInput.value.trim();
        if (playerIdValue) params.player_id = parseInt(playerIdValue, 10);

        params.is_ranked = rankedCheckbox.checked;

        const data = await api.getBattles(params);
        lastTotal = data.total || (data.items ? data.items.length : 0);

        renderTable(data.items || []);
        updatePagination();
      } catch (e) {
        console.error(e);
        alert(e.message);
      }
    }

    function renderTable(items) {
      tableBody.innerHTML = "";

      items.forEach((battle) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><button class="btn btn-secondary btn-sm" data-battle-id="${battle.id}">${battle.id}</button></td>
          <td class="cell-muted">${battle.map_id}</td>
          <td class="cell-muted">${battle.mode_id}</td>
          <td>${battle.is_ranked ? "Yes" : "No"}</td>
          <td class="cell-muted">${battle.started_at ?? ""}</td>
          <td class="cell-muted">${battle.ended_at ?? ""}</td>
        `;

        const btn = tr.querySelector("button[data-battle-id]");
        btn.addEventListener("click", async () => {
          try {
            const details = await api.getBattleDetails(battle.id);
            detailsCard.style.display = "block";
            detailsContent.textContent = JSON.stringify(details, null, 2);
          } catch (e) {
            console.error(e);
            alert(e.message);
          }
        });

        tableBody.appendChild(tr);
      });
    }

    function updatePagination() {
      const currentPage = Math.floor(offset / limit) + 1;
      const totalPages = lastTotal > 0 ? Math.ceil(lastTotal / limit) : 1;

      pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
      prevBtn.disabled = offset <= 0;
      nextBtn.disabled = offset + limit >= lastTotal;
    }

    reloadBtn.addEventListener("click", loadPage);
    playerIdInput.addEventListener("change", () => {
      offset = 0;
      loadPage();
    });
    rankedCheckbox.addEventListener("change", () => {
      offset = 0;
      loadPage();
    });

    prevBtn.addEventListener("click", () => {
      if (offset > 0) {
        offset -= limit;
        loadPage();
      }
    });

    nextBtn.addEventListener("click", () => {
      if (offset + limit < lastTotal) {
        offset += limit;
        loadPage();
      }
    });

    loadPage();
  }

  function initStatsPage() {
    if (showGameRequiredWarningIfNeeded()) return;

    const playerIdInput = document.getElementById("stats-player-id");
    const rankedCheckbox = document.getElementById("stats-ranked-only");
    const loadBtn = document.getElementById("load-player-stats-btn");

    const summaryPre = document.getElementById("stats-summary");
    const mapsTbody = document.querySelector("#stats-maps-table tbody");
    const weaponsTbody = document.querySelector("#stats-weapons-table tbody");

    async function loadStats() {
      const idValue = playerIdInput.value.trim();
      if (!idValue) {
        alert("Please enter player ID");
        return;
      }

      const playerId = parseInt(idValue, 10);
      if (!playerId) {
        alert("Invalid player ID");
        return;
      }

      const rankedOnly = rankedCheckbox.checked;

      try {
        const [summary, maps, weapons] = await Promise.all([
          api.getPlayerStatsSummary(playerId, rankedOnly),
          api.getPlayerMapStats(playerId, rankedOnly),
          api.getPlayerWeaponStats(playerId, rankedOnly),
        ]);

        summaryPre.textContent = JSON.stringify(summary, null, 2);
        renderMaps(maps);
        renderWeapons(weapons);
      } catch (e) {
        console.error(e);
        alert(e.message);
      }
    }

    function renderMaps(items) {
      mapsTbody.innerHTML = "";
      items.forEach((m) => {
        const tr = document.createElement("tr");
        const draws = (m.draws !== undefined && m.draws !== null) ? m.draws : 0;

        tr.innerHTML = `
          <td>${m.map_name ?? m.map_id}</td>
          <td>${m.battles}</td>
          <td>${m.wins}</td>
          <td>${m.losses}</td>
          <td>${draws}</td>
          <td>${((m.win_rate || 0) * 100).toFixed(1)}%</td>
          <td>${Number(m.avg_kills || 0).toFixed(2)}</td>
          <td>${Number(m.avg_deaths || 0).toFixed(2)}</td>
          <td>${Number(m.avg_score || 0).toFixed(1)}</td>
        `;
        mapsTbody.appendChild(tr);
      });
    }

    function renderWeapons(items) {
      weaponsTbody.innerHTML = "";
      items.forEach((w) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${w.weapon_name ?? w.weapon_id}</td>
          <td>${w.kills}</td>
          <td>${w.headshots}</td>
          <td>${((w.accuracy || 0) * 100).toFixed(1)}%</td>
          <td>${w.usage_count}</td>
        `;
        weaponsTbody.appendChild(tr);
      });
    }

    loadBtn.addEventListener("click", loadStats);
  }

  // -------------------------
  // Global init on every page
  // -------------------------
  function initCommon() {
    initAuthUI();
    loadGamesIntoSelector();
    showGameRequiredWarningIfNeeded();
  }

  // run common init
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCommon);
  } else {
    initCommon();
  }
  return {
    initPlayersPage,
    initBattlesPage,
    initStatsPage,
  };
})();
