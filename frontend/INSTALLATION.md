# Installation Instructions

## Install Supabase Dependencies

Run this command in the `frontend` directory:

```bash
npm install @supabase/ssr @supabase/supabase-js
```

## Verify Installation

Check that these packages were added to your `package.json`:

```json
{
  "dependencies": {
    "@supabase/ssr": "^0.5.2",
    "@supabase/supabase-js": "^2.47.10"
  }
}
```

## Configure Environment Variables

Create `frontend/.env.local` with:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Start Development Server

```bash
npm run dev
```

Visit http://localhost:3000 - you should see the login page!

## Next Steps

1. Follow [AUTH_SETUP.md](./AUTH_SETUP.md) for complete setup guide
2. Create a Supabase project at https://supabase.com
3. Configure your credentials in `.env.local`
4. Test the authentication flow
