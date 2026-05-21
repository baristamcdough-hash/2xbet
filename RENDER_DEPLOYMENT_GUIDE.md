# 2xBet Render Deployment Guide (Manual Setup - Option B)

Complete step-by-step instructions for deploying the 2xBet backend to Render with a PostgreSQL database.

---

## Prerequisites

- GitHub account with your forked/cloned `2xbet` repository
- Render account (free at https://render.com)
- Your repository URL: `https://github.com/baristamcdough-hash/2xbet`

---

## Step 1: Create a Render Account

1. Go to https://render.com
2. Click **Sign Up**
3. Choose **Sign up with GitHub** (recommended)
4. Authorize Render to access your GitHub account
5. Complete your profile setup

---

## Step 2: Create a PostgreSQL Database on Render

### 2.1: Navigate to Dashboard

1. After login, you should be on your Render dashboard
2. Click **+ New** button in the top-right
3. Select **PostgreSQL**

### 2.2: Configure the Database

Fill in the form:

| Field | Value |
|-------|-------|
| **Name** | `2xbet-db` |
| **Database** | `2xbet` |
| **User** | `2xbet_user` |
| **Region** | Choose closest to you (e.g., `US East (Ohio)`) |
| **Version** | `13` (or latest available) |
| **Plan** | `Free` (for testing) |

**Important:** Write down your **Internal Database URL** - you'll need it in Step 5.

3. Click **Create Database**
4. Wait for the database to be created (takes ~1-2 minutes)
5. Once created, you'll see a dashboard with connection details

---

## Step 3: Create a Web Service on Render

### 3.1: Navigate to Services

1. From your Render dashboard, click **+ New**
2. Select **Web Service**
3. Click **Connect a repository**

### 3.2: Connect Your GitHub Repository

1. In the **GitHub repository** field, search for `2xbet`
2. Select `baristamcdough-hash/2xbet`
3. Click **Connect**

Render will now scan your repository.

---

## Step 4: Configure the Web Service

### 4.1: General Settings

Fill in the basic configuration:

| Field | Value |
|-------|-------|
| **Name** | `2xbet-api` |
| **Root Directory** | `backend` |
| **Environment** | `Python 3` |
| **Region** | Same as database (e.g., `US East`) |
| **Branch** | `main` |
| **Plan** | `Free` (for testing) |

### 4.2: Build Command

1. Scroll down to **Build Command**
2. Enter:
   ```bash
   ./build.sh
   ```

### 4.3: Start Command

1. Scroll down to **Start Command**
2. Enter:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### 4.4: Environment Variables

Now add environment variables for your database and app configuration.

1. Scroll down to **Environment Variables**
2. Click **Add Environment Variable**
3. Add the following (one by one):

#### Variable 1: DATABASE_URL

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Paste your PostgreSQL connection string from Step 2 |

**Where to get the connection string:**
- Go back to your PostgreSQL service dashboard
- Copy the **Internal Database URL** (looks like: `postgresql://2xbet_user:password@dpg-xxx.postgres.render.com/2xbet`)
- Paste it here

#### Variable 2: SECRET_KEY

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Generate a secure random key (use command below) |

**To generate a secure SECRET_KEY, run this in your terminal:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and paste it into the `SECRET_KEY` value field.

#### Variable 3: ALLOWED_ORIGINS

| Key | Value |
|-----|-------|
| `ALLOWED_ORIGINS` | `*` (for now; customize later with your frontend domain) |

**Example for when your frontend is deployed:**
```
https://2xbet.netlify.app,https://yourdomain.com,http://localhost:5500
```

#### Variable 4: PYTHON_VERSION

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11.6` |

### 4.5: Create the Service

1. Scroll to the bottom
2. Click **Create Web Service**

Render will now:
- Clone your repository
- Run `./build.sh` (installs dependencies + initializes database)
- Start your FastAPI server
- Assign a public URL (e.g., `https://2xbet-api.onrender.com`)

⏳ **Wait 5-10 minutes for the initial deployment** (first build takes longer)

---

## Step 5: Verify Deployment

### 5.1: Check Deployment Status

1. Go to your **Web Service** dashboard (you should already be there)
2. Check the **Status** indicator:
   - 🟢 **Live** = Successfully deployed
   - 🟡 **Deploying** = Still building
   - 🔴 **Failed** = Something went wrong (check logs)

### 5.2: View Deployment Logs

1. Click on the **Logs** tab
2. You should see something like:
   ```
   [startup] Initializing database...
   [startup] Database initialized
   ```

### 5.3: Test the API

1. Copy your **service URL** (e.g., `https://2xbet-api.onrender.com`)
2. Visit in your browser:
   ```
   https://2xbet-api.onrender.com/api/health
   ```
3. You should see:
   ```json
   {
     "status": "ok",
     "service": "2xBet API",
     "timestamp": "2024-01-15T10:30:00.123456"
   }
   ```

4. **Interactive API Docs:**
   ```
   https://2xbet-api.onrender.com/api/docs
   ```

---

## Step 6: Common Issues & Troubleshooting

### Issue: Build fails with "ModuleNotFoundError"

**Solution:**
1. Go to **Settings** tab
2. Scroll down and click **Clear build cache**
3. Click **Deploy** to redeploy

### Issue: "Connection refused" when accessing `/api/docs`

**Solution:**
1. Wait 2-3 more minutes (cold start)
2. If still failing, check logs for database connection errors
3. Verify `DATABASE_URL` environment variable is correct

### Issue: Database connection timeout

**Solution:**
1. Your database might be spinning down (free tier sleeps after 15 minutes of inactivity)
2. Make an API request to wake it up: `https://2xbet-api.onrender.com/api/health`
3. Wait 30 seconds and try again

### Issue: "Secret key not set" or similar auth errors

**Solution:**
1. Go to **Environment** tab
2. Verify `SECRET_KEY` is set
3. Click **Redeploy** from the **Manual Deploy** dropdown

### Issue: Database doesn't have sample data

**Solution:**
1. Database is created but needs seeding
2. Go to your web service's **Shell** tab
3. Run:
   ```bash
   python init_db.py
   ```
4. Check your API docs again

---

## Step 7: Connect Your Frontend

Once your backend is deployed and working, update your frontend to point to the live API.

### 7.1: Update API Base URL in Frontend

In your `app.js` file, find all `fetch()` calls and update the domain:

**Before (local):**
```javascript
const response = await fetch('http://localhost:8000/api/fixtures', { ... });
```

**After (production):**
```javascript
const response = await fetch('https://2xbet-api.onrender.com/api/fixtures', { ... });
```

### 7.2: Easier Way - Environment Variable

1. Create a `.env.js` file at your frontend root:
   ```javascript
   const API_BASE_URL = 'https://2xbet-api.onrender.com';
   ```

2. In `app.js`, add at the top:
   ```javascript
   const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8000';
   ```

3. In `index.html`, add before `<script src="app.js">`:
   ```html
   <script src=".env.js"></script>
   ```

4. Update all API calls:
   ```javascript
   const response = await fetch(`${API_BASE_URL}/api/fixtures`, { ... });
   ```

### 7.3: Update CORS Configuration

If your frontend has a permanent domain (e.g., Netlify), add it to your backend's `ALLOWED_ORIGINS`:

1. Go to your web service's **Environment** tab
2. Click edit on `ALLOWED_ORIGINS`
3. Change from `*` to:
   ```
   https://2xbet.netlify.app,https://yourdomain.com
   ```
4. Click **Deploy**

---

## Step 8: Testing Full Integration

### Test Registration & Login

```javascript
// In browser console:

// Register
fetch('https://2xbet-api.onrender.com/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'testuser',
    email: 'test@example.com',
    password: 'testpass123'
  })
}).then(r => r.json()).then(console.log);

// Login
fetch('https://2xbet-api.onrender.com/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'testpass123'
  })
}).then(r => r.json()).then(d => {
  localStorage.setItem('access_token', d.access_token);
  console.log('Token saved:', d.access_token);
});
```

### Test Fixtures API

```javascript
// Get all fixtures
fetch('https://2xbet-api.onrender.com/api/fixtures?per_page=50')
  .then(r => r.json())
  .then(console.log);
```

### Test Protected Endpoint

```javascript
// Get wallet balance (requires token)
const token = localStorage.getItem('access_token');
fetch('https://2xbet-api.onrender.com/api/wallet/balance', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json()).then(console.log);
```

---

## Step 9: Monitor & Maintain

### View Metrics

1. Click on your web service
2. **Metrics** tab shows:
   - CPU usage
   - Memory usage
   - Network traffic
   - Request count

### Enable Auto-Deploy

1. Go to **Settings**
2. Enable **Auto-Deploy** (redeploys on every push to `main`)

### Manual Redeploy

1. Click **Manual Deploy** dropdown
2. Select **Deploy latest commit**
3. Wait 2-5 minutes

---

## Step 10: Upgrade from Free Plan (Optional)

When you're ready for production:

1. Go to your service's **Settings** tab
2. Click **Change Plan**
3. Select **Starter** or higher (adds auto-scaling, better performance)

---

## Useful Links

- **Your Backend API:** https://2xbet-api.onrender.com
- **API Docs:** https://2xbet-api.onrender.com/api/docs
- **Render Dashboard:** https://dashboard.render.com
- **Database Settings:** https://dashboard.render.com (PostgreSQL service)

---

## Final Checklist

- [ ] PostgreSQL database created on Render
- [ ] Web service created with correct root directory (`backend`)
- [ ] Build command set to `./build.sh`
- [ ] Start command set to `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Environment variables configured (`DATABASE_URL`, `SECRET_KEY`, `ALLOWED_ORIGINS`, `PYTHON_VERSION`)
- [ ] Deployment status is 🟢 **Live**
- [ ] Health check endpoint responds (http://your-url/api/health)
- [ ] API docs accessible (http://your-url/api/docs)
- [ ] Test registration/login works
- [ ] Frontend updated to use live API URL
- [ ] CORS allows your frontend domain

---

## Troubleshooting Commands

**SSH into your deployed service (via Render Shell):**
```bash
# Check environment variables
env | grep DATABASE_URL

# Test database connection
python -c "from database import engine; print(engine.connect())"

# Reinitialize database
python init_db.py

# Check Python version
python --version

# View logs in real-time
# (Use Render dashboard Logs tab)
```

---

**Congratulations! Your 2xBet backend is now live on Render!** 🚀

For questions or issues, check the Render documentation at https://render.com/docs
