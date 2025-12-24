/* eslint-disable no-alert */
window.GameStatsUI = (function () {
  "use strict";

  // -------------------------
  // Config
  // -------------------------
  const CFG = window.APP_CONFIG || {
    apiBase: "/api",
    gamesEndpoint: "/api/games",
    authRegisterEndpoint: "/api/auth/register",
    authTokenEndpoint: "/api/auth/token",
    authMeEndpoint: "/api/auth/me",
    storageKeys: { token: "access_token", gameId: "selected_game_id" },
  };

  // -------------------------
  // Utils
  // -------------------------
  function $(sel) {
    return document.querySelector(sel);
  }

  function show(el, display = "block") {
    if (!el) return;
    el.style.display = display;
  }

  function hide(el) {
    if (!el) return;
    el.style.display = "none";
  }

  function setText(el, text) {
    if (!el) return;
    el.textContent = text ?? "";
  }

  function safeJsonParse(text) {
    try {
      return JSON.parse(text);
    } catch {
      return null;
    }
  }

  // -------------------------
  // Storage
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
  // HTTP
  // -------------------------
  async function apiFetch(url, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set("Accept", "application/json");

    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);

    // JSON for non-FormData bodies
    if (options.body && !(options.body instanceof FormData)) {
      if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    }

    const resp = await fetch(url, {
      ...options,
      headers,
      cache: "no-store", // important for debugging
    });

    return resp;
  }

  async function apiJson(url, options = {}) {
    const resp = await apiFetch(url, options);

    // Read text first (so we can show meaningful error even for non-json)
    const text = await resp.text();
    const maybeJson = safeJsonParse(text);

    if (!resp.ok) {
      const detail =
        (maybeJson && (maybeJson.detail || maybeJson.message)) ? (maybeJson.detail || maybeJson.message) : text;
      throw new Error(`Request failed (${resp.status})${detail ? `: ${String(detail).slice(0, 300)}` : ""}`);
    }

    if (resp.status === 204) return null;
    return maybeJson ?? text;
  }

  function gameScoped(pathTemplate) {
    const gameId = getSelectedGameId();
    if (!gameId) return null;
    return pathTemplate.replace("{gameId}", String(gameId));
  }

  // -------------------------
  // UI helpers (badge/warn)
  // -------------------------
  function setBadge(game) {
    const badge = $("#selected-game-badge");
    if (!badge) return;

    const gameId = getSelectedGameId();
    if (!gameId || !game) {
      hide(badge);
      return;
    }
    badge.textContent = `Game: ${game.name}`;
    show(badge, "inline-flex");
  }

  function showGameRequiredWarningIfNeeded() {
    const warn = $("#game-required-warning");
    if (!warn) return false;

    const gameId = getSelectedGameId();
    if (!gameId) {
      show(warn, "block");
      return true;
    }
    hide(warn);
    return false;
  }

  // -------------------------
  // Auth
  // -------------------------
  async function doRegister(username, password) {
    const payload = { username, password };
    return await apiJson(CFG.authRegisterEndpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async function doLogin(username, password) {
    const form = new URLSearchParams();
    form.set("username", username);
    form.set("password", password);

    const resp = await fetch(CFG.authTokenEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Accept: "application/json",
      },
      body: form.toString(),
      cache: "no-store",
    });

    const text = await resp.text();
    const data = safeJsonParse(text);

    if (!resp.ok) {
      const detail = data?.detail || text;
      throw new Error(`Login failed (${resp.status})${detail ? `: ${String(detail).slice(0, 300)}` : ""}`);
    }

    // {access_token, token_type}
    return data || {};
  }

  async function apiMe() {
    const token = getToken();
    if (!token) return null;

    try {
      // Важно: используем apiFetch, чтобы автоматически проставлялся Bearer токен
      const resp = await apiFetch(CFG.authMeEndpoint || "/api/auth/me", { method: "GET" });
      if (!resp.ok) return null;
      return await resp.json();
    } catch (e) {
      console.warn("[Auth] /auth/me failed", e);
      return null;
    }
  }

  async function renderUserBadge() {
    const slot = $("#userInfo");
    if (!slot) return;

    const user = await apiMe();
    if (!user) {
      slot.textContent = "";
      return;
    }

    // ожидаем что бэкенд отдаёт хотя бы username и role
    const role = user.role ?? user.user_role ?? "";
    slot.textContent = role ? `${user.username} (${role})` : `${user.username}`;
  }


  function openAuthModal(mode /* 'login' | 'register' */) {
    const modal = $("#authModal");
    const title = $("#authModalTitle");
    const hint = $("#authModalHint");
    const err = $("#authError");
    const submit = $("#authSubmit");
    const userEl = $("#authUsername");
    const passEl = $("#authPassword");

    if (!modal || !title || !hint || !err || !submit || !userEl || !passEl) {
      console.error("[Auth] Modal elements missing", {
        modal: !!modal,
        title: !!title,
        hint: !!hint,
        err: !!err,
        submit: !!submit,
        userEl: !!userEl,
        passEl: !!passEl,
      });
      return;
    }

    // reset
    err.textContent = "";
    hide(err);
    userEl.value = "";
    passEl.value = "";

    if (mode === "register") {
      title.textContent = "Register";
      hint.textContent = "Create a new account (username + password).";
      submit.dataset.mode = "register";
      passEl.autocomplete = "new-password";
    } else {
      title.textContent = "Login";
      hint.textContent = "Enter your username and password to get access token.";
      submit.dataset.mode = "login";
      passEl.autocomplete = "current-password";
    }

    // Explicit display!
    show(modal, "block");
    modal.style.pointerEvents = "auto";
    modal.style.zIndex = "2147483647";

    // Focus UX
    setTimeout(() => userEl.focus(), 0);
  }

  function closeAuthModal() {
    const modal = $("#authModal");
    if (modal) hide(modal);
  }

  function syncAuthButtons() {
    const token = getToken();
    const statusEl = $("#authStatus");
    const btnLogin = $("#btnLogin");
    const btnRegister = $("#btnRegister");
    const btnLogout = $("#btnLogout");

    // If auth UI is disabled on this page - just skip quietly
    if (!btnLogin && !btnRegister && !btnLogout) return;

    if (!btnLogin || !btnRegister || !btnLogout) {
      console.warn("[Auth] Some auth buttons missing in DOM", {
        btnLogin: !!btnLogin,
        btnRegister: !!btnRegister,
        btnLogout: !!btnLogout,
      });
      return;
    }

    if (token) {
      setText(statusEl, "Logged in");
      hide(btnLogin);
      hide(btnRegister);
      show(btnLogout, "inline-flex");
    } else {
      setText(statusEl, "");
      show(btnLogin, "inline-flex");
      show(btnRegister, "inline-flex");
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

    // If auth UI not present, skip
    if (!btnLogin && !btnRegister && !btnLogout && !modal) return;

    if (btnLogin && !btnLogin.dataset.bound) {
      btnLogin.addEventListener("click", () => openAuthModal("login"), { capture: true });
      btnLogin.dataset.bound = "1";
    }

    if (btnRegister && !btnRegister.dataset.bound) {
      btnRegister.addEventListener("click", () => openAuthModal("register"), { capture: true });
      btnRegister.dataset.bound = "1";
    }

    if (btnLogout && !btnLogout.dataset.bound) {
      btnLogout.addEventListener("click", async () => {
        setToken("");
        syncAuthButtons();
        await renderUserBadge();
        alert("Logged out");
      }, { capture: true });
      btnLogout.dataset.bound = "1";
    }

    if (modalClose && !modalClose.dataset.bound) {
      modalClose.addEventListener("click", closeAuthModal, { capture: true });
      modalClose.dataset.bound = "1";
    }

    if (modal && !modal.dataset.boundBackdrop) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) closeAuthModal();
      }, { capture: true });
      modal.dataset.boundBackdrop = "1";
    }

    if (!document.documentElement.dataset.boundEsc) {
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeAuthModal();
      }, { capture: true });
      document.documentElement.dataset.boundEsc = "1";
    }

    if (submit && !submit.dataset.bound) {
      submit.addEventListener("click", async () => {
        const mode = submit.dataset.mode || "login";
        const userEl = $("#authUsername");
        const passEl = $("#authPassword");
        const err = $("#authError");

        if (!userEl || !passEl || !err) {
          console.error("[Auth] Submit elements missing");
          return;
        }

        const username = (userEl.value || "").trim();
        const password = (passEl.value || "").trim();

        if (!username || !password) {
          err.textContent = "Username and password are required.";
          show(err, "block");
          return;
        }

        try {
          hide(err);

          if (mode === "register") {
            await doRegister(username, password);
          }

          const tokenResp = await doLogin(username, password);
          if (!tokenResp.access_token) throw new Error("No access_token in response");

          setToken(tokenResp.access_token);
          syncAuthButtons();
          await renderUserBadge();
          closeAuthModal();
          alert(mode === "register" ? "Registered and logged in" : "Logged in");
        } catch (e) {
          console.error(e);
          err.textContent = e?.message || "Auth error";
          show(err, "block");
        }
      }, { capture: true });
      submit.dataset.bound = "1";
    }

    syncAuthButtons();
  }

  // -------------------------
  // Games selector
  // -------------------------
  let cachedGames = [];

  async function loadGamesIntoSelector() {
    const selectEl = $("#gameSelect");

    // If selector not present on this page, skip
    if (!selectEl) return;

    // Prevent double binding
    if (!selectEl.dataset.boundChange) {
      selectEl.addEventListener("change", () => {
        const v = selectEl.value;
        setSelectedGameId(v ? parseInt(v, 10) : null);

        const saved = getSelectedGameId();
        const selected = cachedGames.find((g) => Number(g.id) === Number(saved));
        setBadge(selected || null);

        window.location.reload();
      });
      selectEl.dataset.boundChange = "1";
    }

    // Show loading immediately
    selectEl.innerHTML = `<option value="">Loading…</option>`;

    try {
      const games = await apiJson(CFG.gamesEndpoint);
      cachedGames = Array.isArray(games) ? games : (games?.items || []);

      selectEl.innerHTML = `<option value="">— Select game —</option>`;

      if (!cachedGames.length) {
        // No games in DB/seed
        selectEl.innerHTML = `<option value="">(No games available)</option>`;
        return;
      }

      cachedGames.forEach((g) => {
        const opt = document.createElement("option");
        opt.value = String(g.id);
        opt.textContent = g.name ?? `Game ${g.id}`;
        selectEl.appendChild(opt);
      });

      const saved = getSelectedGameId();
      if (saved) selectEl.value = String(saved);

      const selected = cachedGames.find((g) => Number(g.id) === Number(saved));
      setBadge(selected || null);
    } catch (e) {
      console.error("[Games] Failed to load", e);

      // Make it obvious in UI why it failed
      selectEl.innerHTML = `<option value="">(Failed to load games)</option>`;

      // Optional: also show warning if exists
      const warn = $("#game-required-warning");
      if (warn) {
        warn.textContent = `Failed to load games: ${e?.message || e}`;
        show(warn, "block");
      }
    }
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
      query.set("offset", String(params.offset || 0));
      query.set("limit", String(params.limit || 20));

      return await apiJson(`${base}?${query.toString()}`);
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
      params.set("ranked_only", rankedOnly ? "true" : "false");
      return await apiJson(`${base}?${params.toString()}`);
    },

    async getPlayerMapStats(playerId, rankedOnly) {
      const base = gameScoped(`${CFG.apiBase}/games/{gameId}/stats/players/${playerId}/maps`);
      if (!base) throw new Error("Game is not selected");

      const params = new URLSearchParams();
      params.set("ranked_only", rankedOnly ? "true" : "false");
      return await apiJson(`${base}?${params.toString()}`);
    },

    async getPlayerWeaponStats(playerId, rankedOnly) {
      const base = gameScoped(`${CFG.apiBase}/games/{gameId}/stats/players/${playerId}/weapons`);
      if (!base) throw new Error("Game is not selected");

      const params = new URLSearchParams();
      params.set("ranked_only", rankedOnly ? "true" : "false");
      return await apiJson(`${base}?${params.toString()}`);
    },
  };

  // -------------------------
  // Pages (same as before, just using api.*)
  // -------------------------
  function initPlayersPage() {
    if (showGameRequiredWarningIfNeeded()) return;

    const tableBody = document.querySelector("#players-table tbody");
    const reloadBtn = document.getElementById("reload-players-btn");
    const searchInput = document.getElementById("players-search-input");
    const prevBtn = document.getElementById("players-prev");
    const nextBtn = document.getElementById("players-next");
    const pageInfo = document.getElementById("players-page-info");
    const summaryCard = document.getElementById("player-summary-card");
    const summaryContent = document.getElementById("player-summary-content");

    if (!tableBody || !reloadBtn || !searchInput || !prevBtn || !nextBtn || !pageInfo) {
      console.warn("[Players] Some DOM elements missing, page init skipped");
      return;
    }

    let offset = 0;
    const limit = 20;
    let lastTotal = 0;
    let allItems = [];

    async function loadPage() {
      try {
        const data = await api.getPlayers(offset, limit);
        lastTotal = data.total ?? (data.items ? data.items.length : 0);
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
        .filter((p) => !filter || String(p.nickname || "").toLowerCase().includes(filter))
        .forEach((player) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${player.id}</td>
            <td>${player.nickname ?? ""}</td>
            <td class="cell-muted">${player.created_at ?? ""}</td>
            <td class="cell-muted">${player.user_id ?? ""}</td>
            <td>
              <button class="btn btn-secondary btn-sm" data-player-id="${player.id}">Summary</button>
            </td>
          `;

          const btn = tr.querySelector("button[data-player-id]");
          if (btn) {
            btn.addEventListener("click", async () => {
              try {
                const summary = await api.getPlayerSummary(player.id);
                if (summaryCard) summaryCard.style.display = "block";
                if (summaryContent) summaryContent.textContent = JSON.stringify(summary, null, 2);
              } catch (e) {
                console.error(e);
                alert(e.message);
              }
            });
          }

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

    if (!tableBody || !reloadBtn || !playerIdInput || !rankedCheckbox || !prevBtn || !nextBtn || !pageInfo) {
      console.warn("[Battles] Some DOM elements missing, page init skipped");
      return;
    }

    let offset = 0;
    const limit = 20;
    let lastTotal = 0;

    async function loadPage() {
      try {
        const params = { offset, limit };
        const playerIdValue = (playerIdInput.value || "").trim();
        if (playerIdValue) params.player_id = parseInt(playerIdValue, 10);
        params.is_ranked = !!rankedCheckbox.checked;

        const data = await api.getBattles(params);
        lastTotal = data.total ?? (data.items ? data.items.length : 0);

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
        if (btn) {
          btn.addEventListener("click", async () => {
            try {
              const details = await api.getBattleDetails(battle.id);
              if (detailsCard) detailsCard.style.display = "block";
              if (detailsContent) detailsContent.textContent = JSON.stringify(details, null, 2);
            } catch (e) {
              console.error(e);
              alert(e.message);
            }
          });
        }

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

    if (!playerIdInput || !rankedCheckbox || !loadBtn || !summaryPre || !mapsTbody || !weaponsTbody) {
      console.warn("[Stats] Some DOM elements missing, page init skipped");
      return;
    }

    async function loadStats() {
      const idValue = (playerIdInput.value || "").trim();
      if (!idValue) {
        alert("Please enter player ID");
        return;
      }

      const playerId = parseInt(idValue, 10);
      if (!playerId) {
        alert("Invalid player ID");
        return;
      }

      const rankedOnly = !!rankedCheckbox.checked;

      try {
        const [summary, maps, weapons] = await Promise.all([
          api.getPlayerStatsSummary(playerId, rankedOnly),
          api.getPlayerMapStats(playerId, rankedOnly),
          api.getPlayerWeaponStats(playerId, rankedOnly),
        ]);

        summaryPre.textContent = JSON.stringify(summary, null, 2);
        renderMaps(maps || []);
        renderWeapons(weapons || []);
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
  // Global init
  // -------------------------
  function initCommon() {
    try {
      initAuthUI();
      renderUserBadge();
      loadGamesIntoSelector();
      showGameRequiredWarningIfNeeded();
    } catch (e) {
      console.error("[initCommon] fatal", e);
    }
  }

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
