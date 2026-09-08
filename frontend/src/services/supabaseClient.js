import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY
const isConfigured = (url) => !!url && url.startsWith('http')

export const supabase = (isConfigured(supabaseUrl) && isConfigured(supabaseKey))
  ? createClient(supabaseUrl, supabaseKey)
  : null

export const signUp = (email, password) => {
  if (!supabase) throw new Error('Supabase is not configured')
  return supabase.auth.signUp({ email, password })
}

export const signIn = (email, password) => {
  if (!supabase) throw new Error('Supabase is not configured')
  return supabase.auth.signInWithPassword({ email, password })
}

export const signOut = () => supabase?.auth.signOut()

export default supabase
