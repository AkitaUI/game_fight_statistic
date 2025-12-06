window.GameStatsUI = (function () {
    const api = {
        async getPlayers(offset = 0, limit = 20) {
            const url = `/players?offset=${offset}&limit=${limit}`;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`Failed to load players: ${resp.status}`);
            return await resp.json(); // { total, items }
        },

        async getPlayerSummary(playerId) {
            const url = `/players/${playerId}/summary`;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`Failed to load player summary: ${resp.status}`);
            return await resp.json();
        },

        async getBattles(params) {
            const query = new URLSearchParams();
            if (params.player_id) query.set("player_id", params.player_id);
            if (params.is_ranked !== undefined && params.is_ranked !== null) {
                query.set("is_ranked", params.is_ranked ? "true" : "false");
            }
            query.set("offset", params.offset || 0);
            query.set("limit", params.limit || 20);

            const url = `/battles?${query.toString()}`;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`Failed to load battles: ${resp.status}`);
            return await resp.json();
        },

        async getBattleDetails(battleId) {
            const url = `/battles/${battleId}`;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`Failed to load battle: ${resp.status}`);
            return await resp.json();
        },

        async getPlayerStatsSummary(playerId, rankedOnly) {
            const params = new URLSearchParams();
            if (rankedOnly !== undefined && rankedOnly !== null) {
                params.set("ranked_only", rankedOnly ? "true" : "false");
            }
            const url = `/stats/players/${playerId}?${params.toString()}`;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error("Failed to load player stats summary");
            return await resp.json();
        },

        async getPlayerMapStats(playerId, rankedOnly) {
            const params = new URLSearchParams();
            if (rankedOnly !== undefined && rankedOnly !== null) {
                params.set("ranked_only", rankedOnly ? "true" : "false");
            }
            const url = `/stats/players/${playerId}/maps?${params.toString()}`;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error("Failed to load player map stats");
            return await resp.json();
        },

        async getPlayerWeaponStats(playerId, rankedOnly) {
            const params = new URLSearchParams();
            if (rankedOnly !== undefined && rankedOnly !== null) {
                params.set("ranked_only", rankedOnly ? "true" : "false");
            }
            const url = `/stats/players/${playerId}/weapons?${params.toString()}`;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error("Failed to load player weapon stats");
            return await resp.json();
        }
    };

    function initPlayersPage() {
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
                lastTotal = data.total || data.items.length;
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
                .filter(p => !filter || p.nickname.toLowerCase().includes(filter))
                .forEach(player => {
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
                const params = {
                    offset,
                    limit,
                };

                const playerIdValue = playerIdInput.value.trim();
                if (playerIdValue) {
                    params.player_id = parseInt(playerIdValue, 10);
                }

                params.is_ranked = rankedCheckbox.checked;

                const data = await api.getBattles(params);
                lastTotal = data.total || data.items.length;

                renderTable(data.items || []);
                updatePagination();
            } catch (e) {
                console.error(e);
                alert(e.message);
            }
        }

        function renderTable(items) {
            tableBody.innerHTML = "";

            items.forEach(battle => {
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
            items.forEach(m => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${m.map_name ?? m.map_id}</td>
                    <td>${m.battles}</td>
                    <td>${m.wins}</td>
                    <td>${m.losses}</td>
                    <td>${(m.win_rate * 100).toFixed(1)}%</td>
                    <td>${m.avg_kills.toFixed(2)}</td>
                    <td>${m.avg_deaths.toFixed(2)}</td>
                    <td>${m.avg_score.toFixed(1)}</td>
                `;
                mapsTbody.appendChild(tr);
            });
        }

        function renderWeapons(items) {
            weaponsTbody.innerHTML = "";
            items.forEach(w => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${w.weapon_name ?? w.weapon_id}</td>
                    <td>${w.kills}</td>
                    <td>${w.headshots}</td>
                    <td>${(w.accuracy * 100).toFixed(1)}%</td>
                    <td>${w.usage_count}</td>
                `;
                weaponsTbody.appendChild(tr);
            });
        }

        loadBtn.addEventListener("click", loadStats);
    }

    return {
        initPlayersPage,
        initBattlesPage,
        initStatsPage,
    };
})();
