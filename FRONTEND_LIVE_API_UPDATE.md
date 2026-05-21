# Update Frontend to Use Live API Domain

This guide shows you exactly how to update your frontend to connect to your live backend on Render instead of the mock data.

---

## Step 1: Get Your Live API Domain

1. Go to your Render dashboard: https://dashboard.render.com
2. Click on your `2xbet-api` web service
3. Copy the **URL** at the top (looks like: `https://2xbet-api.onrender.com`)

Save this URL - you'll use it throughout the guide.

---

## Step 2: Update `app.js` - Add API Configuration

At the **very top** of `app.js`, add this configuration section (before `appState` definition):

```javascript
/* ===================================
   API Configuration
   =================================== */

// Change this to your live API domain
const API_BASE_URL = 'https://2xbet-api.onrender.com';
// For local development, use: 'http://localhost:8000'

// Helper function for API calls with auth
async function apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'API request failed');
    }
    
    return response.json();
}
```

---

## Step 3: Replace Mock Data with API Calls

### 3.1: Add Function to Fetch Fixtures

Find where `appState` is defined and add this function **after** `appState` definition:

```javascript
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
```

---

## Step 4: Update Authentication Functions

Find and replace the entire auth section. Look for:

```javascript
// OLD - Replace this section:
function addSelectionToSlip_BACKEND(matchId, pick) {
    console.log(`[BACKEND HOOK] addSelectionToSlip...`);
    // ... 
}
```

Replace with:

```javascript
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
```

---

## Step 5: Update Bet Submission

Find the `submitBetSlip_BACKEND` function and replace it with:

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
    
    console.log('[submitBetSlip] Submitting bet...');
    
    try {
        const response = await apiCall('/api/bets', {
            method: 'POST',
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
        
        console.log('[submitBetSlip] Bet created:', response.id);
        alert(`Bet placed successfully! Bet ID: ${response.id}`);
        
        // Clear betslip and refresh
        clearBetslip();
        await loadUserWallet();
    } catch (error) {
        console.error('[submitBetSlip] Error:', error);
        alert(`Failed to place bet: ${error.message}`);
    }
}
```

---

## Step 6: Add Wallet Functions

Add these new functions to `app.js`:

```javascript
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
```

---

## Step 7: Update DOMContentLoaded Event

Find the `document.addEventListener('DOMContentLoaded', ...)` section and update it:

**OLD:**
```javascript
document.addEventListener('DOMContentLoaded', () => {
    console.log('[DOMContentLoaded] Initializing 2xBet Dashboard');

    // Render initial state
    renderMatches();
    renderBetslip();
    renderTicker();
    // ... rest
});
```

**NEW:**
```javascript
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
```

---

## Step 8: Remove Old Backend Placeholder Functions

Find and **DELETE** these old functions (they're no longer needed):

```javascript
// DELETE THESE:
function addSelectionToSlip_BACKEND(matchId, pick) { ... }
function calculateWinBonus_BACKEND(selectionCount) { ... }
function submitBetSlip_BACKEND() { ... }
function streamLiveUpdates_BACKEND() { ... }
function fetchMatches_BACKEND() { ... }
```

They're replaced by the new `apiCall()` helper and specific functions like `submitBetSlip_BACKEND()` above.

---

## Step 9: Test the Connection

### 9.1: Open Frontend in Browser

1. Open your `index.html` in a browser (or via live server)
2. Open **Browser Console** (F12 → Console tab)
3. You should see logs like:
   ```
   [DOMContentLoaded] Initializing 2xBet Dashboard
   Backend URL: https://2xbet-api.onrender.com
   ```

### 9.2: Test Fixtures Loading

In the browser console, run:
```javascript
fetchFixtures()
```

You should see:
```
[fetchFixtures] Loading from live API...
[fetchFixtures] Loaded 6 fixtures
```

### 9.3: Test Authentication

Register a new user in browser console:
```javascript
registerUser('testuser', 'test@example.com', 'password123')
```

Then login:
```javascript
loginUser('test@example.com', 'password123')
```

If successful, you should see:
```
[auth] Login successful
[wallet] Fetching balance...
[fetchFixtures] Loading from live API...
```

### 9.4: Test Bet Placement

1. Login first (see 9.3)
2. Click on some odds buttons to add selections
3. Enter a stake amount
4. Click "Place Bet"
5. Check console and you should see bet created message

---

## Step 10: Environment Configuration (Optional but Recommended)

For easier switching between development and production, create a `config.js` file:

```javascript
// config.js
const ENV = {
    development: 'http://localhost:8000',
    production: 'https://2xbet-api.onrender.com'
};

// Detect environment
const CURRENT_ENV = window.location.hostname === 'localhost' ? 'development' : 'production';
const API_BASE_URL = ENV[CURRENT_ENV];

console.log('[config] Environment:', CURRENT_ENV, '| API:', API_BASE_URL);
```

Then in `index.html`, load it **before** `app.js`:

```html
<script src="config.js"></script>
<script src="app.js"></script>
```

Now `API_BASE_URL` will automatically switch based on where it's running!

---

## Troubleshooting

### Issue: "Failed to load fixtures" error

**Solution:**
1. Check your API domain is correct
2. Open browser DevTools (F12)
3. Go to Network tab
4. Look for failed requests
5. Check the response error message
6. Verify your Render service is running: `https://your-api-domain/api/health`

### Issue: CORS error in console

**Solution:**
1. Go to Render dashboard
2. Go to your web service **Environment** tab
3. Verify `ALLOWED_ORIGINS` includes your frontend domain
4. Redeploy the service

### Issue: 401 Unauthorized errors after login

**Solution:**
1. Check token is being saved: `localStorage.getItem('access_token')`
2. Verify token is being sent in headers
3. Check `SECRET_KEY` is set on Render
4. Redeploy backend

### Issue: "Connection refused" or service down

**Solution:**
1. Your Render service might be sleeping (free tier sleeps after 15 minutes)
2. Visit `https://your-api-domain/api/health` to wake it up
3. Wait 30 seconds and try again

---

## Complete Code Diff Summary

Here's what changed in `app.js`:

1. **Added** `API_BASE_URL` configuration at top
2. **Added** `apiCall()` helper function for authenticated requests
3. **Added** `fetchFixtures()` to load from API
4. **Added** authentication functions: `registerUser()`, `loginUser()`, `logoutUser()`
5. **Added** wallet functions: `loadUserWallet()`, `depositFunds()`, `withdrawFunds()`
6. **Updated** `DOMContentLoaded` to load from API if logged in
7. **Updated** `submitBetSlip_BACKEND()` to call real API
8. **Removed** old placeholder backend functions
9. **Removed** all hardcoded mock matches from `appState`

---

## Final Checklist

- [ ] Replace `API_BASE_URL` with your live domain
- [ ] Add `apiCall()` helper function
- [ ] Add `fetchFixtures()` function
- [ ] Update all auth functions
- [ ] Update bet submission function
- [ ] Update `DOMContentLoaded` event
- [ ] Test in browser console
- [ ] Verify fixtures load from API
- [ ] Test registration/login
- [ ] Test placing a bet
- [ ] Check DevTools Network tab for successful API calls

---

## Next Steps

1. **Push updated code to GitHub**
2. **Deploy frontend to Netlify or similar**
3. **Monitor Render backend logs** for any issues
4. **Share your live API with team**

Your frontend is now fully integrated with your live backend! 🚀
