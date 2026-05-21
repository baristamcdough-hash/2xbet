/* ===================================
   2xBet Dashboard - JavaScript
   =================================== */

// ===================================
// STATE MANAGEMENT
// ===================================

const API_BASE_URL = 'https://twoxbet-j42a.onrender.com';

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
    // Fetch fixtures from live API
async function fetchFixtures() {
    console.log('[fetchFixtures] Loading from live API...');
    
    try {
        const data = await apiCall('/api/fixtures?per_page=50');
        
        // Map API response to app state format
        appState.matches = data.fixtures.map(fixture => ({
            id: fixture.id.toString(),
            homeTeam: fixture.home_team,
            awayTeam: fixture.away_team,
            league: fixture.league,
            sport: fixture.sport,
            startTime: new Date(fixture.scheduled_start),
            status: fixture.status === 'live' ? 'live' : 'upcoming',
            homeScore: fixture.home_score,
            awayScore: fixture.away_score,
            odds: {
                win1: parseFloat(fixture.odds_win_home),
                draw: fixture.odds_draw ? parseFloat(fixture.odds_draw) : null,
                win2: parseFloat(fixture.odds_win_away)
            }
        }));
        
        console.log('[fetchFixtures] Loaded', appState.matches.length, 'fixtures');
        renderMatches();
    } catch (error) {
        console.error('[fetchFixtures] Error:', error);
        alert('Failed to load fixtures. Check console for details.');
        // Fall back to mock data if API fails
        renderMatches();
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

// ===================================
// AUTHENTICATION & API INTEGRATION
// ===================================

async function registerUser(username, email, password) {
    console.log('[auth] Registering user...');
    
    try {
        const response = await apiCall('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
        
        console.log('[auth] Registration successful');
        alert('Registration successful! Please login.');
        return true;
    } catch (error) {
        console.error('[auth] Registration error:', error);
        alert(`Registration failed: ${error.message}`);
        return false;
    }
}

async function loginUser(email, password) {
    console.log('[auth] Logging in...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
            throw new Error('Invalid email or password');
        }
        
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        
        console.log('[auth] Login successful');
        await loadUserData();
        return true;
    } catch (error) {
        console.error('[auth] Login error:', error);
        alert(`Login failed: ${error.message}`);
        return false;
    }
}

async function logoutUser() {
    console.log('[auth] Logging out...');
    localStorage.removeItem('access_token');
    alert('Logged out successfully');
    location.reload();
}

async function loadUserData() {
    console.log('[auth] Loading user data...');
    
    try {
        await loadUserWallet();
        await fetchFixtures();
    } catch (error) {
        console.error('[auth] Failed to load user data:', error);
    }
}

async function loadUserWallet() {
    console.log('[wallet] Fetching balance...');
    
    try {
        const wallet = await apiCall('/api/wallet/balance');
        
        console.log('Wallet:', wallet);
        
        // Update UI with wallet info
        const balanceEl = document.getElementById('wallet-balance') || 
                         document.createElement('div');
        balanceEl.textContent = `Balance: $${wallet.balance}`;
        
        return wallet;
    } catch (error) {
        console.error('[wallet] Error:', error);
        return null;
    }
}

async function depositFunds(amount) {
    console.log('[wallet] Deposit:', amount);
    
    try {
        const response = await apiCall(`/api/wallet/deposit?amount=${amount}`, {
            method: 'POST'
        });
        
        console.log('[wallet] Deposit successful');
        alert(`Deposited $${amount} successfully!`);
        await loadUserWallet();
    } catch (error) {
        console.error('[wallet] Deposit error:', error);
        alert(`Deposit failed: ${error.message}`);
    }
}

async function withdrawFunds(amount) {
    console.log('[wallet] Withdraw:', amount);
    
    try {
        const response = await apiCall(`/api/wallet/withdraw?amount=${amount}`, {
            method: 'POST'
        });
        
        console.log('[wallet] Withdrawal successful');
        alert(`Withdrew $${amount} successfully!`);
        await loadUserWallet();
    } catch (error) {
        console.error('[wallet] Withdrawal error:', error);
        alert(`Withdrawal failed: ${error.message}`);
    }
}

async function loadTransactionHistory() {
    console.log('[wallet] Loading transactions...');
    
    try {
        const response = await apiCall('/api/wallet/transactions?page=1&per_page=20');
        
        console.log('[wallet] Transactions:', response.transactions);
        return response.transactions;
    } catch (error) {
        console.error('[wallet] Error loading transactions:', error);
        return [];
    }
}

// ===================================
// EVENT LISTENERS
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('[DOMContentLoaded] Initializing 2xBet Dashboard');
    
    const token = localStorage.getItem('access_token');
    
    if (token) {
        // User is logged in - load from API
        console.log('[DOMContentLoaded] User logged in, loading from API...');
        loadUserData();
    } else {
        // No login - show mock data or login prompt
        console.log('[DOMContentLoaded] No user logged in, using mock data');
        fetchFixtures().catch(() => {
            console.log('[DOMContentLoaded] Falling back to mock data');
            renderMatches();
        });
    }
    
    // Initialize UI
    renderBetslip();
    renderTicker();

    // Filter button listeners
    DOM.filterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            setFilterActive(e.target.dataset.filter);
        });
    });

    setFilterActive('all');

    // Navigation link listeners
    DOM.navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            console.log(`[Navigation] Clicked:`, e.target.textContent);
            setNavLinkActive(e.target);
        });
    });

    // Betslip controls
    DOM.stakeInput.addEventListener('input', () => {
        updateBetslipStats();
    });

    DOM.submitBetBtn.addEventListener('click', () => {
        console.log('[UI Event] Submit Bet Button Clicked');
        submitBetSlip_BACKEND();
    });

    DOM.clearSlipBtn.addEventListener('click', () => {
        console.log('[UI Event] Clear Slip Button Clicked');
        clearBetslip();
    });
    
    console.log('\n========== API INTEGRATION READY ==========');
    console.log('Backend URL:', API_BASE_URL);
    console.log('==========================================\n');
});
