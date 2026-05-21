/* ===================================
   2xBet Dashboard - JavaScript
   =================================== */

// ===================================
// STATE MANAGEMENT
// ===================================

const API_BASE_URL = 'https://2xbet-api.onrender.com';

async function apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options, headers
    });
    
    if (!response.ok) throw new Error('API request failed');
    return response.json();
}

const appState = {
    // Current matches data
    matches: [
        {
            id: 'match-001',
            homeTeam: 'Manchester United',
            awayTeam: 'Liverpool',
            league: 'Premier League',
            sport: 'soccer',
            startTime: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours from now
            status: 'upcoming', // 'upcoming' or 'live'
            homeScore: null,
            awayScore: null,
            odds: {
                win1: 2.45,
                draw: 3.20,
                win2: 2.80
            }
        },
        {
            id: 'match-002',
            homeTeam: 'Barcelona',
            awayTeam: 'Real Madrid',
            league: 'La Liga',
            sport: 'soccer',
            startTime: new Date(Date.now() + 5 * 60 * 60 * 1000),
            status: 'upcoming',
            homeScore: null,
            awayScore: null,
            odds: {
                win1: 2.15,
                draw: 3.50,
                win2: 3.40
            }
        },
        {
            id: 'match-003',
            homeTeam: 'Lakers',
            awayTeam: 'Celtics',
            league: 'NBA',
            sport: 'basketball',
            startTime: new Date(Date.now() + 45 * 60 * 1000), // 45 minutes from now
            status: 'live',
            homeScore: 78,
            awayScore: 82,
            odds: {
                win1: 1.95,
                draw: null,
                win2: 1.85
            }
        },
        {
            id: 'match-004',
            homeTeam: 'Chelsea',
            awayTeam: 'Arsenal',
            league: 'Premier League',
            sport: 'soccer',
            startTime: new Date(Date.now() + 8 * 60 * 60 * 1000),
            status: 'upcoming',
            homeScore: null,
            awayScore: null,
            odds: {
                win1: 2.30,
                draw: 3.10,
                win2: 3.15
            }
        },
        {
            id: 'match-005',
            homeTeam: 'PSG',
            awayTeam: 'Monaco',
            league: 'Ligue 1',
            sport: 'soccer',
            startTime: new Date(Date.now() + 3.5 * 60 * 60 * 1000),
            status: 'upcoming',
            homeScore: null,
            awayScore: null,
            odds: {
                win1: 1.65,
                draw: 3.80,
                win2: 5.50
            }
        },
        {
            id: 'match-006',
            homeTeam: 'Warriors',
            awayTeam: 'Nets',
            league: 'NBA',
            sport: 'basketball',
            startTime: new Date(Date.now() + 6 * 60 * 60 * 1000),
            status: 'upcoming',
            homeScore: null,
            awayScore: null,
            odds: {
                win1: 1.55,
                draw: null,
                win2: 2.35
            }
        }
    ],

    // Active betslip selections
    betslipSelections: [],

    // Live ticker items
    tickerItems: [
        { id: 'ticker-1', username: 'JohnBets', selection: 'Man United Win', odds: 2.45, won: true, timestamp: Date.now() },
        { id: 'ticker-2', username: 'LuckyLion', selection: 'Barcelona + Draw', odds: 5.12, won: true, timestamp: Date.now() - 30000 },
        { id: 'ticker-3', username: 'ProGambler', selection: 'Lakers 1X2', odds: 1.95, won: true, timestamp: Date.now() - 60000 }
    ],

    // Current stake input
    stakeAmount: 0,

    // Filter state
    currentFilter: 'all' // 'all', 'live', 'upcoming'
};

// ===================================
// DOM REFERENCES
// ===================================

const DOM = {
    matchesList: document.getElementById('matches-list'),
    betslipSelections: document.getElementById('betslip-selections'),
    tickerFeed: document.getElementById('ticker-feed'),
    stakeInput: document.getElementById('stake-input'),
    selectionCount: document.getElementById('selection-count'),
    potentialWin: document.getElementById('potential-win'),
    winBonus: document.getElementById('win-bonus'),
    submitBetBtn: document.getElementById('submit-bet-btn'),
    clearSlipBtn: document.getElementById('clear-slip-btn'),
    filterBtns: document.querySelectorAll('.filter-btn'),
    navLinks: document.querySelectorAll('.nav-link')
};

// ===================================
// UTILITY FUNCTIONS
// ===================================

function formatTime(date) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

function formatDate(date) {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    return days[date.getDay()];
}

function calculateWinBonus(selectionCount) {
    // Win bonus scaling: 2+ selections get bonus
    if (selectionCount < 2) return 0;
    if (selectionCount === 2) return 5;
    if (selectionCount === 3) return 10;
    if (selectionCount === 4) return 15;
    if (selectionCount === 5) return 20;
    return 25; // Max 25% for 6+ selections
}

function getFilteredMatches() {
    if (appState.currentFilter === 'all') {
        return appState.matches;
    } else if (appState.currentFilter === 'live') {
        return appState.matches.filter(m => m.status === 'live');
    } else if (appState.currentFilter === 'upcoming') {
        return appState.matches.filter(m => m.status === 'upcoming');
    }
}

// ===================================
// RENDER FUNCTIONS
// ===================================

function renderMatches() {
    console.log('[renderMatches] Rendering matches list');
    const filteredMatches = getFilteredMatches();
    
    DOM.matchesList.innerHTML = '';

    filteredMatches.forEach(match => {
        const matchEl = document.createElement('div');
        matchEl.className = `match-row ${match.status === 'live' ? 'live' : ''}`;
        matchEl.dataset.matchId = match.id;

        const statusLabel = match.status === 'live' 
            ? 'LIVE' 
            : formatTime(match.startTime);
        const statusClass = match.status === 'live' ? 'live' : 'upcoming';

        let scoreDisplay = '';
        if (match.status === 'live') {
            scoreDisplay = `<div class="team">${match.homeTeam} <strong>${match.homeScore}</strong></div>
                            <div class="vs-separator">vs</div>
                            <div class="team"><strong>${match.awayScore}</strong> ${match.awayTeam}</div>`;
        } else {
            scoreDisplay = `<div class="team">${match.homeTeam}</div>
                            <div class="vs-separator">vs</div>
                            <div class="team">${match.awayTeam}</div>`;
        }

        const oddsHtml = `
            <button class="odds-btn" data-match-id="${match.id}" data-pick="win1">
                <span class="odds-label">1</span>
                <span class="odds-value">${match.odds.win1.toFixed(2)}</span>
            </button>
            ${match.odds.draw ? `
            <button class="odds-btn" data-match-id="${match.id}" data-pick="draw">
                <span class="odds-label">X</span>
                <span class="odds-value">${match.odds.draw.toFixed(2)}</span>
            </button>
            ` : ''}
            <button class="odds-btn" data-match-id="${match.id}" data-pick="win2">
                <span class="odds-label">2</span>
                <span class="odds-value">${match.odds.win2.toFixed(2)}</span>
            </button>
        `;

        matchEl.innerHTML = `
            <span class="match-status ${statusClass}">${statusLabel}</span>
            <div class="match-info">
                <div class="match-time">${formatDate(match.startTime)} • ${match.league}</div>
                <div class="match-teams">
                    ${scoreDisplay}
                </div>
            </div>
            <div class="odds-section">
                ${oddsHtml}
            </div>
        `;

        DOM.matchesList.appendChild(matchEl);
    });

    // Attach event listeners to odds buttons
    attachOddsButtonListeners();
}

function renderBetslip() {
    console.log('[renderBetslip] Rendering betslip with', appState.betslipSelections.length, 'selections');
    
    DOM.betslipSelections.innerHTML = '';

    if (appState.betslipSelections.length === 0) {
        DOM.betslipSelections.innerHTML = '<div class="betslip-empty">No selections yet</div>';
        DOM.submitBetBtn.disabled = true;
        updateBetslipStats();
        return;
    }

    appState.betslipSelections.forEach(selection => {
        const selEl = document.createElement('div');
        selEl.className = 'betslip-selection-item';
        selEl.innerHTML = `
            <div class="selection-info">
                <div class="selection-match">${selection.homeTeam} vs ${selection.awayTeam}</div>
                <div class="selection-pick">${selection.pickLabel} @ ${selection.odds.toFixed(2)}</div>
            </div>
            <button class="remove-selection" data-selection-id="${selection.id}">✕</button>
        `;
        DOM.betslipSelections.appendChild(selEl);
    });

    // Attach remove listeners
    document.querySelectorAll('.remove-selection').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const selectionId = e.target.dataset.selectionId;
            removeSelectionFromSlip(selectionId);
        });
    });

    DOM.submitBetBtn.disabled = false;
    updateBetslipStats();
}

function renderTicker() {
    console.log('[renderTicker] Rendering live ticker with', appState.tickerItems.length, 'items');
    
    DOM.tickerFeed.innerHTML = '';

    appState.tickerItems.forEach(item => {
        const tickerEl = document.createElement('div');
        tickerEl.className = 'ticker-item';
        tickerEl.innerHTML = `
            <span class="ticker-item-highlight">${item.username}</span>
            won on ${item.selection} @ ${item.odds.toFixed(2)}
        `;
        DOM.tickerFeed.insertBefore(tickerEl, DOM.tickerFeed.firstChild);
    });

    // Keep only last 5 items
    while (DOM.tickerFeed.children.length > 5) {
        DOM.tickerFeed.removeChild(DOM.tickerFeed.lastChild);
    }
}

function updateBetslipStats() {
    console.log('[updateBetslipStats] Updating betslip statistics');
    
    const count = appState.betslipSelections.length;
    const totalOdds = appState.betslipSelections.reduce((acc, sel) => acc * sel.odds, 1);
    const stake = parseFloat(DOM.stakeInput.value) || 0;
    const potentialWinAmount = stake * totalOdds;
    const bonus = calculateWinBonus(count);

    DOM.selectionCount.textContent = count;
    DOM.potentialWin.textContent = potentialWinAmount.toFixed(2);
    DOM.winBonus.textContent = `${bonus}%`;

    console.log(`[updateBetslipStats] Count: ${count}, Odds: ${totalOdds.toFixed(4)}, Bonus: ${bonus}%`);
}

// ===================================
// USER INTERACTION HANDLERS
// ===================================

function attachOddsButtonListeners() {
    document.querySelectorAll('.odds-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const matchId = e.currentTarget.dataset.matchId;
            const pick = e.currentTarget.dataset.pick;
            addSelectionToSlip(matchId, pick);
        });
    });
}

function addSelectionToSlip(matchId, pick) {
    console.log(`[addSelectionToSlip] Adding selection - Match: ${matchId}, Pick: ${pick}`);
    
    // Find the match
    const match = appState.matches.find(m => m.id === matchId);
    if (!match) {
        console.error('Match not found:', matchId);
        return;
    }

    // Prevent duplicate selections from same match
    const existingSelection = appState.betslipSelections.find(s => s.matchId === matchId);
    if (existingSelection) {
        console.log('[addSelectionToSlip] Selection already exists, removing previous');
        removeSelectionFromSlip(existingSelection.id);
    }

    // Map pick code to label and odds
    const pickMap = {
        'win1': { label: `${match.homeTeam} Win`, odds: match.odds.win1 },
        'draw': { label: 'Draw', odds: match.odds.draw },
        'win2': { label: `${match.awayTeam} Win`, odds: match.odds.win2 }
    };

    const pickData = pickMap[pick];
    if (!pickData) {
        console.error('Invalid pick:', pick);
        return;
    }

    // Create selection object
    const selection = {
        id: `${matchId}-${pick}-${Date.now()}`,
        matchId,
        pick,
        pickLabel: pickData.label,
        odds: pickData.odds,
        homeTeam: match.homeTeam,
        awayTeam: match.awayTeam
    };

    appState.betslipSelections.push(selection);
    console.log('[addSelectionToSlip] Selection added. Total selections:', appState.betslipSelections.length);

    // Update UI
    renderBetslip();
    updateOddsButtonStates();
}

function removeSelectionFromSlip(selectionId) {
    console.log(`[removeSelectionFromSlip] Removing selection: ${selectionId}`);
    
    appState.betslipSelections = appState.betslipSelections.filter(s => s.id !== selectionId);
    console.log('[removeSelectionFromSlip] Total selections remaining:', appState.betslipSelections.length);
    
    renderBetslip();
    updateOddsButtonStates();
}

function updateOddsButtonStates() {
    // Clear all active states
    document.querySelectorAll('.odds-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Set active for selected buttons
    appState.betslipSelections.forEach(selection => {
        const btn = document.querySelector(
            `.odds-btn[data-match-id="${selection.matchId}"][data-pick="${selection.pick}"]`
        );
        if (btn) {
            btn.classList.add('active');
        }
    });
}

function clearBetslip() {
    console.log('[clearBetslip] Clearing all selections');
    appState.betslipSelections = [];
    DOM.stakeInput.value = '';
    renderBetslip();
    updateOddsButtonStates();
}

function setFilterActive(filterType) {
    console.log(`[setFilterActive] Setting filter to: ${filterType}`);
    appState.currentFilter = filterType;
    
    DOM.filterBtns.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === filterType) {
            btn.classList.add('active');
        }
    });

    renderMatches();
}

function setNavLinkActive(element) {
    DOM.navLinks.forEach(link => {
        link.classList.remove('active');
    });
    if (element) {
        element.classList.add('active');
    }
}

// ===================================
// BACKEND INTEGRATION PLACEHOLDERS
// ===================================

function addSelectionToSlip_BACKEND(matchId, pick) {
    console.log(`[BACKEND HOOK] addSelectionToSlip - Match: ${matchId}, Pick: ${pick}`);
    console.log('TODO: Connect to API endpoint: POST /api/betslip/add-selection');
    console.log('Payload: { matchId, pick, timestamp }');
}

function calculateWinBonus_BACKEND(selectionCount) {
    console.log(`[BACKEND HOOK] calculateWinBonus - Selection Count: ${selectionCount}`);
    console.log('TODO: Connect to API endpoint: GET /api/bonus/calculate');
    console.log('Expected response: { bonusPercentage, bonusAmount }');
    
    // Current implementation uses local calculation
    const bonus = calculateWinBonus(selectionCount);
    console.log(`Calculated bonus locally: ${bonus}%`);
    return bonus;
}

function submitBetSlip_BACKEND() {
    console.log('[BACKEND HOOK] submitBetSlip');
    console.log('Payload: {');
    console.log('  selections:', appState.betslipSelections);
    console.log('  stake:', parseFloat(DOM.stakeInput.value) || 0);
    console.log('  totalOdds:', appState.betslipSelections.reduce((acc, s) => acc * s.odds, 1));
    console.log('  potentialWin:', parseFloat(DOM.potentialWin.textContent));
    console.log('}');
    console.log('TODO: Connect to API endpoint: POST /api/bets/submit');
    console.log('Expected response: { betId, status, confirmation }');
}

function streamLiveUpdates_BACKEND() {
    console.log('[BACKEND HOOK] streamLiveUpdates');
    console.log('TODO: Set up WebSocket connection to: ws://api.2xbet.local/live-stream');
    console.log('Expected events: { type, data }');
    console.log('  - type: "match_update" -> score, status changes');
    console.log('  - type: "ticker_update" -> new win notifications');
    console.log('  - type: "odds_update" -> odds changes');
}

function fetchMatches_BACKEND() {
    console.log('[BACKEND HOOK] fetchMatches');
    console.log('TODO: Replace mock data with API call: GET /api/matches');
    console.log('Query params: { sport, league, filter, page, limit }');
    console.log('Expected response: { matches: [...], total, page }');
}

// ===================================
// EVENT LISTENERS
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('[DOMContentLoaded] Initializing 2xBet Dashboard');

    // Render initial state
    renderMatches();
    renderBetslip();
    renderTicker();

    // Filter button listeners
    DOM.filterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            setFilterActive(e.target.dataset.filter);
        });
    });

    // Set 'All' as default active filter
    setFilterActive('all');

    // Navigation link listeners
    DOM.navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            console.log(`[Navigation] Clicked:`, e.target.textContent, e.target.dataset);
            setNavLinkActive(e.target);
        });
    });

    // Betslip controls
    DOM.stakeInput.addEventListener('input', () => {
        updateBetslipStats();
    });

    DOM.submitBetBtn.addEventListener('click', () => {
        console.log('[UI Event] Submit Bet Button Clicked');
        const stake = parseFloat(DOM.stakeInput.value);
        if (isNaN(stake) || stake <= 0) {
            console.warn('Invalid stake amount');
            alert('Please enter a valid stake amount');
            return;
        }
        if (appState.betslipSelections.length === 0) {
            console.warn('No selections in betslip');
            alert('Please select at least one bet');
            return;
        }
        submitBetSlip_BACKEND();
        console.log('[UI Event] Bet submission ready for backend integration');
    });

    DOM.clearSlipBtn.addEventListener('click', () => {
        console.log('[UI Event] Clear Slip Button Clicked');
        clearBetslip();
    });

    // Initialize backend integration hooks
    console.log('\n========== BACKEND INTEGRATION READY ==========');
    console.log('Call the following functions to connect to your backend:');
    console.log('- fetchMatches_BACKEND()');
    console.log('- streamLiveUpdates_BACKEND()');
    console.log('- addSelectionToSlip_BACKEND(matchId, pick)');
    console.log('- submitBetSlip_BACKEND()');
    console.log('============================================\n');
});

// Simulate live ticker updates
setInterval(() => {
    if (Math.random() > 0.7) { // 30% chance every 5 seconds
        const usernames = ['BetKing', 'LuckyPunch', 'ProTrader', 'GreenGoblin', 'OddsWizard'];
        const selections = ['Arsenal Win', 'Over 2.5', 'Draw + Over', 'Liverpool 1X2'];
        
        const newItem = {
            id: `ticker-${Date.now()}`,
            username: usernames[Math.floor(Math.random() * usernames.length)],
            selection: selections[Math.floor(Math.random() * selections.length)],
            odds: (Math.random() * 3 + 1.5).toFixed(2),
            won: true,
            timestamp: Date.now()
        };

        appState.tickerItems.unshift(newItem);
        renderTicker();
    }
}, 5000);

// Example: Simulate live match updates every 30 seconds
setInterval(() => {
    const liveMatches = appState.matches.filter(m => m.status === 'live');
    if (liveMatches.length > 0) {
        const randomLiveMatch = liveMatches[Math.floor(Math.random() * liveMatches.length)];
        randomLiveMatch.homeScore = Math.max(0, randomLiveMatch.homeScore + (Math.random() > 0.8 ? 1 : 0));
        randomLiveMatch.awayScore = Math.max(0, randomLiveMatch.awayScore + (Math.random() > 0.8 ? 1 : 0));
        console.log(`[Live Update] ${randomLiveMatch.homeTeam} ${randomLiveMatch.homeScore} - ${randomLiveMatch.awayScore} ${randomLiveMatch.awayTeam}`);
        renderMatches();
    }
}, 30000);
