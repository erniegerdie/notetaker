/**
 * Supabase client for authentication
 *
 * This client is used for auth operations only. The backend API
 * handles all data operations with JWT verification.
 */

import { createBrowserClient } from '@supabase/ssr'

export const supabase = createBrowserClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
