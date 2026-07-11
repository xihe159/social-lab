-- Social Lab V1.5 Supabase schema
-- Run this in the Supabase SQL editor before enabling the V1.5 backend.

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  username text,
  avatar text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.personas (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  scenario text not null check (scenario in ('advisor', 'work', 'social')),
  role text not null default '',
  goal text not null default '',
  persona_json jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  persona_id uuid references public.personas(id) on delete set null,
  scenario text not null check (scenario in ('advisor', 'work', 'social')),
  goal text not null default '',
  status text not null default 'active',
  created_at timestamptz not null default now()
);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions(id) on delete cascade,
  role text not null check (role in ('user', 'target')),
  content text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.reports (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions(id) on delete cascade,
  report_json jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.relationship_states (
  session_id uuid primary key references public.sessions(id) on delete cascade,
  trust integer not null default 50,
  respect integer not null default 50,
  familiarity integer not null default 50,
  affinity integer not null default 50,
  authority integer not null default 50,
  emotional integer not null default 0,
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.personas enable row level security;
alter table public.sessions enable row level security;
alter table public.messages enable row level security;
alter table public.reports enable row level security;
alter table public.relationship_states enable row level security;

create policy "profiles_own_rows" on public.profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);

create policy "personas_own_rows" on public.personas
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "sessions_own_rows" on public.sessions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "messages_own_session" on public.messages
  for all using (
    exists (
      select 1 from public.sessions
      where sessions.id = messages.session_id
      and sessions.user_id = auth.uid()
    )
  ) with check (
    exists (
      select 1 from public.sessions
      where sessions.id = messages.session_id
      and sessions.user_id = auth.uid()
    )
  );

create policy "reports_own_session" on public.reports
  for all using (
    exists (
      select 1 from public.sessions
      where sessions.id = reports.session_id
      and sessions.user_id = auth.uid()
    )
  ) with check (
    exists (
      select 1 from public.sessions
      where sessions.id = reports.session_id
      and sessions.user_id = auth.uid()
    )
  );

create policy "relationship_states_own_session" on public.relationship_states
  for all using (
    exists (
      select 1 from public.sessions
      where sessions.id = relationship_states.session_id
      and sessions.user_id = auth.uid()
    )
  ) with check (
    exists (
      select 1 from public.sessions
      where sessions.id = relationship_states.session_id
      and sessions.user_id = auth.uid()
    )
  );
