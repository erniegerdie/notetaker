# Quick Start Guide

## ✅ What's Been Completed

### Backend
- ✅ Database migration completed (user_id columns added)
- ✅ Backend server running on http://localhost:8007
- ✅ Authentication endpoints protected (returns 403 for unauthenticated requests)
- ✅ Health check working: http://localhost:8007/health

### Frontend
- ✅ Supabase dependencies installed (`@supabase/ssr`, `@supabase/supabase-js`)
- ✅ Production build successful (no compilation errors)
- ✅ All authentication components created:
  - Login/signup page
  - Protected route wrapper
  - Auth context provider
  - User info in sidebar

## 🚀 Next Steps to Get Running

### 1. Create Supabase Project (5 minutes)

1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Fill in:
   - **Name:** notetaker
   - **Database Password:** (save this!)
   - **Region:** Choose closest to you
4. Wait ~2 minutes for provisioning

### 2. Get Supabase Credentials

Once project is ready:

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon public** key (the long JWT token)
   - **JWT Secret** (under "JWT Settings" section)

### 3. Configure Backend Environment

Update `backend/.env` with your Supabase credentials:

```bash
# Add these three lines (keep everything else):
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-super-secret-jwt-secret
```

### 4. Configure Frontend Environment

Update `frontend/.env.local` with your Supabase credentials:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8007

# Replace these with YOUR values from Supabase Dashboard:
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 5. Restart Backend (to pick up new env vars)

```bash
# Backend is already running, just restart it:
# Press Ctrl+C in the terminal where uvicorn is running
# Then start again:
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8007
```

### 6. Start Frontend

```bash
cd frontend
npm run dev
```

Visit http://localhost:3000 - you should see the login page!

### 7. Test the Flow

1. **Sign Up:**
   - Click "Sign Up" tab
   - Enter email and password
   - Submit (you'll get a confirmation message)
   - Note: Email confirmation might be enabled - check Supabase for confirmation email

2. **Sign In:**
   - Click "Sign In" tab
   - Enter your credentials
   - Should redirect to home page

3. **Upload a Video:**
   - Click upload button
   - Select a video file
   - It should process and show in your list

4. **Sign Out:**
   - Click logout button in sidebar
   - Should redirect to login

## 🛠️ Current Status

### Running Services

| Service | Status | URL | Notes |
|---------|--------|-----|-------|
| PostgreSQL | ✅ Running | localhost:5434 | Docker container |
| Backend API | ✅ Running | http://localhost:8007 | Uvicorn with hot reload |
| Frontend | ⏸️ Ready | http://localhost:3000 | Run `npm run dev` |

### What Works

✅ Backend authentication middleware
✅ Protected API endpoints
✅ Database schema with user_id columns
✅ Frontend build (no errors)
✅ All auth UI components

### What Needs Configuration

🔧 Supabase credentials in `backend/.env`
🔧 Supabase credentials in `frontend/.env.local`
🔧 Enable email auth in Supabase Dashboard

## 📝 Important Notes

### Supabase Email Settings

By default, Supabase requires email confirmation. For **development**, you can disable this:

1. Supabase Dashboard → **Authentication** → **Settings**
2. Find "Enable email confirmations"
3. Toggle it **OFF**
4. **Remember to re-enable for production!**

### Testing Without Supabase (Development Only)

If you want to test the backend API without authentication temporarily:

1. Comment out the `Depends(get_current_user)` in `backend/app/api/videos.py`
2. This is NOT recommended - only for testing!

## 🔍 Troubleshooting

### "Not authenticated" errors

**Cause:** Supabase credentials not configured
**Fix:** Add `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET` to backend `.env`

### Frontend won't start

**Cause:** Missing Supabase env vars
**Fix:** Add `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` to `frontend/.env.local`

### Login doesn't work

**Cause:** Email confirmation enabled
**Fix:** Disable email confirmations in Supabase Dashboard (see above)

### Database connection errors

**Cause:** PostgreSQL container not running
**Fix:** `cd backend && docker compose up -d`

## 📚 Full Documentation

For complete setup instructions and deployment guides, see:

- **Backend Setup:** [backend/AUTH_SETUP.md](backend/AUTH_SETUP.md)
- **Frontend Setup:** [frontend/AUTH_SETUP.md](frontend/AUTH_SETUP.md)
- **Full Summary:** [AUTHENTICATION_IMPLEMENTATION_SUMMARY.md](AUTHENTICATION_IMPLEMENTATION_SUMMARY.md)
- **Deployment:** [backend/render.yaml](backend/render.yaml) for Render configuration

## ✨ What You Get

Once configured, you'll have:

- ✅ Secure user authentication
- ✅ Multi-user support (data isolation)
- ✅ Professional login/signup UI
- ✅ User info in sidebar
- ✅ Protected routes
- ✅ Production-ready architecture

**Estimated setup time:** 10-15 minutes (mostly waiting for Supabase provisioning)
