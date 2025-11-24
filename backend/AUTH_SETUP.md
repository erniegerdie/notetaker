# Authentication Setup Guide

This guide walks through setting up Supabase authentication for the notetaker backend.

## Architecture

**Stack:**
- **Backend Auth:** Supabase JWT verification (no custom auth code)
- **Database:** Render PostgreSQL or Supabase PostgreSQL
- **Frontend:** Supabase client handles authentication
- **Deployment:** Render (backend) + Vercel (frontend)

## 1. Create Supabase Project

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Fill in project details:
   - **Name:** notetaker
   - **Database Password:** (save this securely)
   - **Region:** Choose closest to your Render region
4. Wait for project to provision (~2 minutes)

## 2. Configure Supabase Authentication

### Enable Email Authentication

1. In Supabase Dashboard → **Authentication** → **Providers**
2. Enable **Email** provider
3. Disable email confirmation for development (optional):
   - Go to **Authentication** → **Settings**
   - Toggle off "Enable email confirmations"
   - **Note:** Re-enable for production!

### Get API Credentials

Go to **Settings** → **API** and note these values:

```bash
# Project URL
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co

# Anon/Public Key (safe for frontend)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# JWT Secret (keep secure! backend only)
SUPABASE_JWT_SECRET=your-super-secret-jwt-token-with-at-least-32-characters-long
```

### Configure Site URL and Redirect URLs

1. Go to **Authentication** → **URL Configuration**
2. **Site URL:** `http://localhost:3000` (development) or your production URL
3. **Redirect URLs:** Add:
   - `http://localhost:3000/**`
   - `https://your-app.vercel.app/**` (production)

## 3. Database Setup

### Option A: Use Render PostgreSQL (Recommended for Cost)

1. Database will be created by `render.yaml`
2. Run Alembic migrations to add user_id columns:

```bash
cd backend
uv run alembic upgrade head
```

### Option B: Use Supabase PostgreSQL (Recommended for RLS)

1. Get connection string from Supabase Dashboard → **Settings** → **Database**
2. Update `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:[password]@db.[ref].supabase.co:5432/postgres
```

3. Run migrations:

```bash
uv run alembic upgrade head
```

4. **Optional:** Enable Row Level Security (RLS) for maximum security:

```sql
-- Run in Supabase SQL Editor

-- Enable RLS
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;

-- RLS Policies for videos
CREATE POLICY "Users can view own videos"
  ON videos FOR SELECT
  USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own videos"
  ON videos FOR INSERT
  WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own videos"
  ON videos FOR UPDATE
  USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own videos"
  ON videos FOR DELETE
  USING (auth.uid()::text = user_id);

-- Similar policies for collections and tags
```

## 4. Backend Configuration

### Install Dependencies

```bash
cd backend
uv sync
```

This installs `pyjwt` for JWT verification (already added to `pyproject.toml`).

### Configure Environment Variables

Create or update `backend/.env`:

```bash
# Copy from .env.example
cp .env.example .env

# Edit with your values
nano .env
```

Required values:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_JWT_SECRET`
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`

## 5. Migrate Existing Data (If Applicable)

If you have existing videos/collections/tags without a user_id, assign them to a user:

```bash
# First, create a user in Supabase (via Supabase Dashboard or frontend)
# Then get the user's UUID from Supabase Dashboard → Authentication → Users

# Run migration script
cd backend
uv run python scripts/assign_existing_data_to_user.py <user-uuid>
```

Example:
```bash
uv run python scripts/assign_existing_data_to_user.py 550e8400-e29b-41d4-a716-446655440000
```

## 6. Testing Locally

### Start Backend

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Test Authentication Flow

1. **Register User** (via Supabase Dashboard or frontend):
   - Go to Supabase Dashboard → Authentication → Users
   - Click "Add user" → Email
   - Or use frontend signup form

2. **Get JWT Token:**
   - Use Supabase client in frontend to sign in
   - Token will be returned automatically
   - Or use Supabase Dashboard → Authentication → Users → ... → Copy JWT

3. **Test Protected Endpoint:**

```bash
# Without token (should fail with 401)
curl http://localhost:8000/api/videos

# With token (should succeed)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/videos
```

## 7. Deployment to Render

### Deploy Backend

1. **Connect Repository:**
   - In Render Dashboard → New → Web Service
   - Connect your GitHub repository
   - Select `backend` directory

2. **Or Use Blueprint (render.yaml):**
   ```bash
   # Push render.yaml to repository
   git add backend/render.yaml
   git commit -m "Add Render configuration"
   git push
   ```

3. **Add Environment Variables** in Render Dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_JWT_SECRET`
   - `OPENAI_API_KEY`
   - `OPENROUTER_API_KEY`

4. **Run Migrations** after first deploy:
   ```bash
   # In Render Shell
   cd backend
   uv run alembic upgrade head
   ```

### Update CORS in Production

Update `backend/app/main.py` with your production frontend URL:

```python
allow_origins=[
    "http://localhost:3000",
    "https://your-app.vercel.app",  # Add your Vercel URL
]
```

## 8. Frontend Integration

See `frontend/AUTH_SETUP.md` for frontend implementation details.

## Security Checklist

- [ ] `SUPABASE_JWT_SECRET` kept secure (not committed to git)
- [ ] CORS configured with specific origins (not `*`)
- [ ] Email confirmation enabled in production
- [ ] RLS policies enabled if using Supabase database
- [ ] HTTPS enforced (automatic on Render)
- [ ] All protected endpoints use `Depends(get_current_user)`

## Troubleshooting

### 401 Unauthorized Errors

1. **Check JWT token is being sent:**
   ```bash
   # Inspect request headers in browser DevTools
   Authorization: Bearer eyJhbG...
   ```

2. **Verify JWT secret matches:**
   - Backend `.env` `SUPABASE_JWT_SECRET`
   - Supabase Dashboard → Settings → API → JWT Secret

3. **Check token expiry:**
   - Supabase tokens expire after 1 hour by default
   - Frontend should handle auto-refresh

### Database Connection Issues

1. **Verify DATABASE_URL format:**
   ```bash
   # Correct for Render
   postgresql://user:pass@host:5432/dbname

   # Correct for Supabase
   postgresql+asyncpg://postgres:pass@db.xxx.supabase.co:5432/postgres
   ```

2. **Check firewall/network:**
   - Render can connect to Supabase (no firewall issues)
   - Supabase allows connections from any IP by default

### User ID Not Found in Token

1. **Check token payload:**
   ```python
   # In backend, add logging
   import jwt
   payload = jwt.decode(token, verify=False)
   print(payload)
   ```

2. **Verify `sub` claim exists:**
   - Should contain Supabase user UUID
   - If missing, token is invalid

## Cost Breakdown

**Option 1: Render + Supabase Free**
- Render Web Service: $7/mo
- Render PostgreSQL: $7/mo
- Supabase Auth: Free (50k MAU)
- **Total: ~$14/mo**

**Option 2: Full Supabase**
- Supabase Pro: $25/mo
- Render Web Service: $7/mo
- **Total: ~$32/mo**

## Next Steps

1. ✅ Backend authentication configured
2. ⏭️ Set up frontend authentication (see `frontend/AUTH_SETUP.md`)
3. ⏭️ Deploy to production
4. ⏭️ Add OAuth providers (Google, GitHub) if needed
5. ⏭️ Implement password reset flow
6. ⏭️ Add user profile management
