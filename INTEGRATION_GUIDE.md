# 2xBet Frontend-Backend Integration Guide

This guide walks you through connecting the single-file frontend (`index.html`, `style.css`, `app.js`) to the FastAPI backend.

## Architecture Overview

```
Frontend (Single HTML file)
├── index.html (scaffold & structure)
├── style.css (betPawa-inspired styling)
└── app.js (state management & API calls)
        ↓ (HTTP requests)
Backend (FastAPI + SQLAlchemy + PostgreSQL)
├── main.py (FastAPI app & route registration)
├── routes_auth.py (user registration/login)
├── routes_fixtures.py (matches & odds)
├── routes_bets.py (bet creation & settlement)
└── routes_wallet.py (balance & transactions)
```

## Setup Instructions

### 1. Start the Backend Server

```bash
cd backend
python init_db.py          # Initialize database with sample data
uvicorn main:app --reload  # Start server (runs on http://localhost:8000)
```

The backend is now running with:
- **API docs**: http://localhost:8000/api/docs (interactive Swagger UI)
- **Health check**: http://localhost:8000/api/health
- **CORS enabled** for frontend origins

### 2. Serve the Frontend

Option A: Live Server (if using VS Code)
```
Right-click index.html → Open with Live Server
```

Option B: Simple HTTP Server
```bash
python -m http.server 5500
# Open http://localhost:5500
```

Option C: Node.js http-server
```bash
npx http-server -p 5500
```

---

## API Integration Checklist

### ✅ Authentication Flow

**Register New User:**
```javascript
const response = await fetch('http://localhost:8000/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'johndoe',
    email: 'john@example.com',
    password: 'securepass123'
  })
});
const user = await response.json();
```

**Login & Get Token:**
```javascript
const response = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'john@example.com',
    password: 'securepass123'
  })
});
const data = await response.json();
const token = data.access_token;
// Save token to localStorage
localStorage.setItem('access_token', token);
```

**Protected API Calls:**
```javascript
const token = localStorage.getItem('access_token');
const response = await fetch('http://localhost:8000/api/wallet/balance', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const wallet = await response.json();
```

---

### ✅ Fetch & Display Fixtures

**Replace Mock Fixtures:**

In `app.js`, replace the hardcoded `appState.matches` with an API call:

```javascript
async function fetchFixtures() {
  console.log('[fetchFixtures] Fetching from backend...');
  
  try {
    const response = await fetch('http://localhost:8000/api/fixtures?per_page=50');
    const data = await response.json();
    
    // Map API response to app state
    appState.matches = data.fixtures.map(fixture => ({
      id: fixture.id,
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
  }
}

// Call on page load
document.addEventListener('DOMContentLoaded', () => {
  fetchFixtures();  // Replace hardcoded renderMatches()
  // ... rest of initialization
});
```

**Filter by Sport/League:**
```javascript
async function fetchFixturesByLeague(league) {
  const response = await fetch(
    `http://localhost:8000/api/fixtures/league/${league}?per_page=50`
  );
  const data = await response.json();
  appState.matches = data.fixtures.map(/* ... */);
  renderMatches();
}
```

---

### ✅ User Registration & Login Flow

**Handle Auth:**
```javascript
async function handleLogin() {
  const email = document.getElementById('auth-email').value;
  const password = document.getElementById('auth-password').value;
  
  try {
    const response = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (!response.ok) throw new Error('Login failed');
    
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    console.log('Login successful');
    loadUserData();
  } catch (error) {
    console.error('Login error:', error);
    alert('Login failed. Please try again.');
  }
}

async function handleRegister() {
  const username = document.getElementById('auth-username').value;
  const email = document.getElementById('auth-email').value;
  const password = document.getElementById('auth-password').value;
  
  try {
    const response = await fetch('http://localhost:8000/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password })
    });
    
    if (!response.ok) throw new Error('Registration failed');
    
    // Auto-login after register
    await handleLogin();
  } catch (error) {
    console.error('Registration error:', error);
    alert('Registration failed. Please try again.');
  }
}
```

---

### ✅ Load & Display User Wallet

**Fetch Wallet Balance:**
```javascript
async function loadUserWallet() {
  const token = localStorage.getItem('access_token');
  
  try {
    const response = await fetch('http://localhost:8000/api/wallet/balance', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const wallet = await response.json();
    
    console.log('Balance:', wallet.balance);
    console.log('Total Wagered:', wallet.total_wagered);
    console.log('Total Won:', wallet.total_won);
    
    // Update UI with wallet info
    displayWalletInfo(wallet);
  } catch (error) {
    console.error('Failed to load wallet:', error);
  }
}

async function loadUserData() {
  await loadUserWallet();
  await fetchFixtures();
}
```

**Mock Deposit (for testing):**
```javascript
async function mockDeposit(amount) {
  const token = localStorage.getItem('access_token');
  
  try {
    const response = await fetch(
      `http://localhost:8000/api/wallet/deposit?amount=${amount}`,
      {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );
    
    const result = await response.json();
    console.log('Deposit successful:', result);
    
    // Refresh balance
    await loadUserWallet();
  } catch (error) {
    console.error('Deposit failed:', error);
  }
}
```

---

### ✅ Create & Submit Bets

**Replace Mock Bet Submission:**

```javascript
async function submitBetSlip_BACKEND() {
  const token = localStorage.getItem('access_token');
  const stake = parseFloat(DOM.stakeInput.value) || 0;
  
  if (!token) {
    alert('Please login to place a bet');
    return;
  }
  
  if (stake <= 0) {
    alert('Invalid stake amount');
    return;
  }
  
  if (appState.betslipSelections.length === 0) {
    alert('No selections in betslip');
    return;
  }
  
  console.log('[submitBetSlip_BACKEND] Submitting bet...');
  
  try {
    const response = await fetch('http://localhost:8000/api/bets', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        bet_type: 'multi',
        stake: stake,
        selections: appState.betslipSelections.map(sel => ({
          fixture_id: parseInt(sel.matchId),
          pick: sel.pick,
          pick_label: sel.pickLabel,
          odds: parseFloat(sel.odds)
        }))
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Bet submission failed');
    }
    
    const bet = await response.json();
    console.log('[submitBetSlip_BACKEND] Bet created:', bet.id);
    
    alert(`Bet placed successfully! Bet ID: ${bet.id}`);
    
    // Clear betslip and refresh
    clearBetslip();
    await loadUserWallet();
  } catch (error) {
    console.error('[submitBetSlip_BACKEND] Error:', error);
    alert(`Failed to place bet: ${error.message}`);
  }
}
```

---

### ✅ Display User Bets & History

**Show Recent Bets:**
```javascript
async function loadUserBets() {
  const token = localStorage.getItem('access_token');
  
  try {
    const response = await fetch(
      'http://localhost:8000/api/bets?page=1&per_page=10',
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );
    
    const data = await response.json();
    console.log('User bets:', data.bets);
    displayUserBets(data.bets);
  } catch (error) {
    console.error('Failed to load bets:', error);
  }
}
```

**Show Transaction History:**
```javascript
async function loadTransactionHistory() {
  const token = localStorage.getItem('access_token');
  
  try {
    const response = await fetch(
      'http://localhost:8000/api/wallet/transactions?page=1&per_page=20',
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );
    
    const data = await response.json();
    console.log('Transactions:', data.transactions);
  } catch (error) {
    console.error('Failed to load transactions:', error);
  }
}
```

---

## Testing Checklist

### Manual Testing

- [ ] Backend server starts without errors
- [ ] API docs accessible at http://localhost:8000/api/docs
- [ ] Frontend loads and displays
- [ ] User can register and receive confirmation
- [ ] User can login and token is stored
- [ ] Fixtures load from API
- [ ] User can add selections to betslip
- [ ] Betslip calculates odds correctly
- [ ] User can place a bet
- [ ] Wallet balance updates after bet
- [ ] Transaction history appears after bet
- [ ] Can deposit/withdraw funds
- [ ] Can view bet history

---

## Common Issues & Troubleshooting

### Issue: CORS Error in Browser Console

**Solution:** Check backend CORS middleware in `main.py`. Frontend origin must be in `allow_origins` list.

### Issue: "Authorization header required"

**Solution:** Ensure token is being sent correctly:

```javascript
headers: {
  'Authorization': `Bearer ${token}`  // Note: "Bearer " prefix
}
```

### Issue: Database errors on startup

**Solution:** Reinitialize database:

```bash
cd backend
python init_db.py
```

### Issue: API returns 422 (Validation Error)

**Solution:** Check request body matches schema. View error details in browser console or API docs.

---

## API Reference

All endpoints documented at: http://localhost:8000/api/docs

Key endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/register` | POST | Register user |
| `/api/auth/login` | POST | Login and get token |
| `/api/fixtures` | GET | List all fixtures |
| `/api/fixtures/live` | GET | List live matches |
| `/api/bets` | POST | Create new bet |
| `/api/wallet/balance` | GET | Check balance |
| `/api/wallet/deposit` | POST | Deposit funds |
| `/api/wallet/transactions` | GET | Transaction history |

---

Happy coding! 🎉
