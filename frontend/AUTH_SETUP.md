# Frontend Authentication Setup Guide

This guide covers integrating Supabase authentication into the Next.js frontend.

## 1. Install Dependencies

```bash
cd frontend
npm install @supabase/ssr @supabase/supabase-js
```

**Packages:**
- `@supabase/ssr` - Supabase client for Next.js App Router (replaces deprecated `@supabase/auth-helpers-nextjs`)
- `@supabase/supabase-js` - Core Supabase client library

## 2. Environment Variables

Create or update `frontend/.env.local`:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000  # Development
# NEXT_PUBLIC_API_URL=https://your-api.onrender.com  # Production
```

### Get Supabase Credentials

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Settings** → **API**
4. Copy:
   - **Project URL** → `NEXT_PUBLIC_SUPABASE_URL`
   - **anon public key** → `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## 3. File Structure

The authentication implementation consists of:

```
frontend/
├── lib/
│   ├── supabase.ts              # Supabase client configuration
│   ├── auth-context.tsx         # Auth state management (useAuth hook)
│   └── api.ts                   # API client with JWT auth headers (updated)
├── components/
│   └── auth/
│       └── protected-route.tsx  # Route protection wrapper
├── app/
│   ├── login/
│   │   └── page.tsx            # Login/signup page
│   ├── layout.tsx              # Root layout with AuthProvider (updated)
│   └── page.tsx                # Home page with protection (updated)
└── components/
    └── sidebar.tsx             # Sidebar with user info (updated)
```

## 4. Key Components

### Supabase Client ([lib/supabase.ts](lib/supabase.ts))

Configured for Next.js App Router with browser-side authentication:

```typescript
import { createBrowserClient } from '@supabase/ssr'

export const supabase = createBrowserClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```

### Auth Context ([lib/auth-context.tsx](lib/auth-context.tsx))

Provides authentication state and methods throughout the app:

```typescript
const { user, session, loading, signUp, signIn, signOut } = useAuth()
```

**Available methods:**
- `signUp(email, password)` - Create new user account
- `signIn(email, password)` - Authenticate existing user
- `signOut()` - Sign out and redirect to login

### API Client ([lib/api.ts](lib/api.ts))

Automatically attaches JWT tokens to all API requests:

```typescript
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})
```

### Protected Routes ([components/auth/protected-route.tsx](components/auth/protected-route.tsx))

Wraps pages requiring authentication:

```typescript
export default function ProtectedPage() {
  return (
    <ProtectedRoute>
      <YourContent />
    </ProtectedRoute>
  )
}
```

## 5. Usage Examples

### Protecting a Page

```typescript
// app/videos/[id]/page.tsx
'use client'

import { ProtectedRoute } from '@/components/auth/protected-route'

export default function VideoDetailPage() {
  return (
    <ProtectedRoute>
      <VideoDetail />
    </ProtectedRoute>
  )
}
```

### Using Auth in Components

```typescript
'use client'

import { useAuth } from '@/lib/auth-context'

export function UserProfile() {
  const { user, signOut } = useAuth()

  return (
    <div>
      <p>Email: {user?.email}</p>
      <button onClick={signOut}>Sign Out</button>
    </div>
  )
}
```

### Making Authenticated API Calls

```typescript
import api from '@/lib/api'

// JWT token automatically included in Authorization header
const response = await api.get('/api/videos')
```

## 6. Testing Locally

### Start Development Server

```bash
cd frontend
npm run dev
```

### Test Authentication Flow

1. **Visit** http://localhost:3000
   - Should redirect to `/login` (not authenticated)

2. **Sign Up:**
   - Click "Sign Up" tab
   - Enter email and password
   - Submit form
   - Check email for confirmation (if enabled in Supabase)

3. **Sign In:**
   - Enter credentials
   - Should redirect to home page `/`
   - Sidebar should show user email and logout button

4. **Test Protected Routes:**
   - Try accessing `/videos/[id]` directly
   - Should redirect to `/login` if not authenticated
   - Should load normally if authenticated

5. **Test Logout:**
   - Click logout button in sidebar
   - Should redirect to `/login`
   - Should clear session

## 7. Deployment to Vercel

### Connect Repository

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Select `frontend` as root directory

### Configure Environment Variables

In Vercel project settings → **Environment Variables**, add:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
NEXT_PUBLIC_API_URL=https://your-api.onrender.com
```

### Deploy

```bash
git push origin main
# Vercel auto-deploys on push
```

### Update Supabase Redirect URLs

After deployment, add your Vercel URL to Supabase:

1. Go to Supabase Dashboard → **Authentication** → **URL Configuration**
2. Add to **Redirect URLs:**
   ```
   https://your-app.vercel.app/**
   https://your-app-git-*.vercel.app/**  (for preview deployments)
   ```

## 8. Troubleshooting

### "Invalid JWT" Errors

**Cause:** Token expired or invalid

**Solution:**
- Supabase tokens expire after 1 hour
- Auto-refresh is handled by `onAuthStateChange` listener
- Check that `SUPABASE_JWT_SECRET` matches in backend

### Redirect Loop on Login

**Cause:** Protected route wrapper detecting no user and redirecting repeatedly

**Solution:**
- Ensure login page (`/login`) is NOT wrapped in `ProtectedRoute`
- Check that `AuthProvider` is wrapping the entire app in `layout.tsx`

### API Calls Return 401 Unauthorized

**Cause:** JWT token not being sent or invalid

**Solution:**
1. **Check token is being attached:**
   ```javascript
   // In browser console
   const { data: { session } } = await supabase.auth.getSession()
   console.log(session?.access_token)
   ```

2. **Verify API interceptor:**
   - Check `lib/api.ts` includes auth interceptor
   - Ensure imports are correct: `import { supabase } from './supabase'`

3. **Check backend configuration:**
   - Verify `SUPABASE_JWT_SECRET` in backend matches Supabase
   - Test JWT decoding in backend logs

### Email Confirmation Not Working

**Cause:** Email confirmation enabled but not configured

**Solution:**
1. **For Development:**
   - Disable in Supabase Dashboard → **Authentication** → **Settings**
   - Toggle off "Enable email confirmations"

2. **For Production:**
   - Configure email templates in Supabase
   - Set up custom SMTP (optional)
   - Or use Supabase's built-in email service

### User State Not Persisting

**Cause:** Session not being saved or loaded

**Solution:**
- Check browser localStorage for `sb-*` keys
- Clear cache and cookies, try again
- Verify `AuthProvider` is in root layout

## 9. Security Best Practices

### Environment Variables

- ✅ **DO** use `NEXT_PUBLIC_` prefix for client-side variables
- ✅ **DO** keep `SUPABASE_ANON_KEY` public (it's designed for client use)
- ❌ **DON'T** expose `SUPABASE_JWT_SECRET` in frontend
- ❌ **DON'T** commit `.env.local` to git (already in `.gitignore`)

### Authentication Flow

- ✅ **DO** validate JWT on backend for every request
- ✅ **DO** filter data by user_id in backend queries
- ✅ **DO** use HTTPS in production (Vercel provides this automatically)
- ❌ **DON'T** trust client-side user data without backend verification

### Token Management

- ✅ **DO** let Supabase handle token refresh automatically
- ✅ **DO** use `getSession()` to get fresh tokens for API calls
- ❌ **DON'T** store tokens manually (Supabase handles this)
- ❌ **DON'T** decode JWT on frontend (trust backend validation)

## 10. Next Steps

### Implemented Features ✅

- [x] Email/password authentication
- [x] Protected routes
- [x] Auto token refresh
- [x] User session management
- [x] JWT verification in backend
- [x] User info display in sidebar

### Optional Enhancements

- [ ] OAuth providers (Google, GitHub)
- [ ] Password reset flow
- [ ] Email verification UI
- [ ] User profile management
- [ ] Remember me functionality
- [ ] Session timeout warnings
- [ ] Magic link authentication
- [ ] Two-factor authentication (2FA)

### OAuth Setup (Optional)

To add Google/GitHub sign-in:

1. **Configure in Supabase:**
   - Dashboard → **Authentication** → **Providers**
   - Enable Google/GitHub
   - Add OAuth credentials

2. **Update Login Page:**
   ```typescript
   const handleOAuthSignIn = async (provider: 'google' | 'github') => {
     await supabase.auth.signInWithOAuth({
       provider,
       options: {
         redirectTo: `${window.location.origin}/auth/callback`
       }
     })
   }
   ```

## 11. Cost Considerations

**Supabase Free Tier:**
- 50,000 Monthly Active Users (MAU)
- 50,000 Auth requests/month
- Perfect for development and small apps

**When to Upgrade:**
- More than 50k MAU
- Need advanced auth features (SAML, custom domains)
- Want dedicated support

**Vercel Free Tier:**
- Perfect for frontend hosting
- 100GB bandwidth/month
- Unlimited projects

## Support

For issues:
1. Check this guide's troubleshooting section
2. Review backend `AUTH_SETUP.md`
3. Check [Supabase Documentation](https://supabase.com/docs/guides/auth)
4. Check [Next.js Documentation](https://nextjs.org/docs)
