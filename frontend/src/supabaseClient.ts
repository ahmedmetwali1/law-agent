import { createClient, SupabaseClient } from '@supabase/supabase-js'

// Use dummy values if env vars not set (prevents crash during development)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBsYWNlaG9sZGVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE2NDUxOTI4MDAsImV4cCI6MTk2MDc2ODgwMH0.placeholder'

if (!import.meta.env.VITE_SUPABASE_URL) {
    console.warn('⚠️ Using placeholder Supabase credentials. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env for real data.')
}

export const isConfigured = supabaseUrl !== 'https://placeholder.supabase.co'

// Cache for authenticated client (to avoid multiple instances)
let cachedAuthClient: SupabaseClient | null = null
let cachedToken: string | null = null

// Create base supabase client (singleton)
const baseClient = createClient(supabaseUrl, supabaseAnonKey)

/**
 * Get authenticated supabase client
 * WARNING: With custom authentication, RLS policies won't work
 * Make sure to run migration 09_disable_rls_for_custom_auth.sql
 */
export function getAuthenticatedSupabase(): SupabaseClient {
    const token = localStorage.getItem('access_token')

    // Return cached client if token hasn't changed
    if (cachedAuthClient && cachedToken === token) {
        return cachedAuthClient
    }

    // Update cache
    cachedToken = token

    if (token) {
        // For now, use base client with anon key since RLS will be disabled
        // The backend will handle authorization
        cachedAuthClient = baseClient
        return cachedAuthClient
    }

    // No token - return base client
    cachedAuthClient = baseClient
    return baseClient
}

// Export base client for compatibility
export const supabase = baseClient
