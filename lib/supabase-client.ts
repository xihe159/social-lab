import { createClient } from "@supabase/supabase-js";

const DEFAULT_SUPABASE_URL = "https://fhwezvhjbkjojktoqxte.supabase.co";
const DEFAULT_SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZod2V6dmhqYmtqb2prdG9xeHRlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM3MTU1ODcsImV4cCI6MjA5OTI5MTU4N30.Saj7XsqCJnzy4J3SO0-enLCnHJRkgt9ypLfU9MwuTRY";

const supabaseUrl =
  process.env.NEXT_PUBLIC_SUPABASE_URL || DEFAULT_SUPABASE_URL;
const supabaseAnonKey =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || DEFAULT_SUPABASE_ANON_KEY;

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl as string, supabaseAnonKey as string, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: false,
        flowType: "pkce",
      },
    })
  : null;
