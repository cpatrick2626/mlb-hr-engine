-- 012_community_bet_slips.sql
-- Community Bet Slips Phase 1: identity + social publication only.
-- Run manually in the Supabase Dashboard SQL Editor before deploying the API.
-- This migration never reads from or writes to scoring, pipeline, slate, MAIN, or JIG tables.

-- A database sequence, rather than MAX(app_number) + 1, makes concurrent
-- signups collision-safe. Gaps are acceptable if a signup transaction rolls back.
CREATE SEQUENCE IF NOT EXISTS public.profiles_app_number_seq AS integer START WITH 1;

CREATE TABLE IF NOT EXISTS public.profiles (
  user_id     uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  app_number  integer,
  username    text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS app_number integer;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS username text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.profiles ALTER COLUMN app_number SET DEFAULT nextval('public.profiles_app_number_seq');

-- Existing profiles (if any) receive permanent numbers before constraints are added.
UPDATE public.profiles
SET app_number = nextval('public.profiles_app_number_seq')
WHERE app_number IS NULL;

UPDATE public.profiles
SET username = 'user-' || app_number::text
WHERE username IS NULL OR btrim(username) = '';

SELECT setval(
  'public.profiles_app_number_seq',
  COALESCE((SELECT MAX(app_number) FROM public.profiles), 0) + 1,
  false
);

ALTER TABLE public.profiles ALTER COLUMN app_number SET NOT NULL;
ALTER TABLE public.profiles ALTER COLUMN username SET NOT NULL;
ALTER TABLE public.profiles ADD CONSTRAINT profiles_app_number_unique UNIQUE (app_number);
CREATE UNIQUE INDEX IF NOT EXISTS profiles_username_lower_unique
  ON public.profiles (lower(username));

CREATE OR REPLACE FUNCTION public.set_profile_identity_defaults()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.app_number IS NULL THEN
    NEW.app_number := nextval('public.profiles_app_number_seq');
  END IF;
  IF NEW.username IS NULL OR btrim(NEW.username) = '' THEN
    NEW.username := 'user-' || NEW.app_number::text;
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.prevent_profile_app_number_change()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.app_number IS DISTINCT FROM OLD.app_number THEN
    RAISE EXCEPTION 'app_number is permanent and cannot be changed';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS profiles_set_identity_defaults ON public.profiles;
CREATE TRIGGER profiles_set_identity_defaults
  BEFORE INSERT ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.set_profile_identity_defaults();

DROP TRIGGER IF EXISTS profiles_prevent_app_number_change ON public.profiles;
CREATE TRIGGER profiles_prevent_app_number_change
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.prevent_profile_app_number_change();

-- Create a profile for every email/password or OAuth signup. The profile trigger
-- assigns both the sequential permanent app_number and a unique editable default username.
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (user_id) VALUES (NEW.id)
  ON CONFLICT (user_id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created_profile ON auth.users;
CREATE TRIGGER on_auth_user_created_profile
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();

CREATE TABLE IF NOT EXISTS public.community_posts (
  post_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id  uuid NOT NULL UNIQUE REFERENCES public.tickets(ticket_id) ON DELETE CASCADE,
  user_id    uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  posted_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS community_posts_user_posted_at_idx
  ON public.community_posts (user_id, posted_at DESC);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_posts ENABLE ROW LEVEL SECURITY;

-- API access is through the service-role client and JWT ownership checks.
-- Direct anon/authenticated table access remains closed by RLS.
