-- NutriWell backend-to-Supabase audit migration
-- Safe to run against the existing public schema. No tables or data are dropped.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Shared timestamp maintenance for mutable records.
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    auth_user_id UUID UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Existing users table: align it with Supabase Auth ownership lookups.
ALTER TABLE IF EXISTS public.users
    ADD COLUMN IF NOT EXISTS auth_user_id UUID,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS ux_users_auth_user_id
    ON public.users(auth_user_id)
    WHERE auth_user_id IS NOT NULL;

-- 2. FOODS TABLE
CREATE TABLE IF NOT EXISTS public.foods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    calories NUMERIC(7, 2) NOT NULL DEFAULT 0,
    protein NUMERIC(6, 2) NOT NULL DEFAULT 0,
    carbs NUMERIC(6, 2) NOT NULL DEFAULT 0,
    fats NUMERIC(6, 2) NOT NULL DEFAULT 0,
    fiber NUMERIC(6, 2) NOT NULL DEFAULT 0,
    sugar NUMERIC(6, 2) DEFAULT 0,
    sodium NUMERIC(7, 2) DEFAULT 0,
    serving_size NUMERIC(6, 2) DEFAULT 100.0,
    serving_unit VARCHAR(50) DEFAULT 'g',
    category VARCHAR(100) DEFAULT 'General',
    diet_type VARCHAR(50) DEFAULT 'Veg',
    is_custom BOOLEAN DEFAULT FALSE,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Existing foods table: ensure numeric serving quantity and audit columns
ALTER TABLE IF EXISTS public.foods
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS diet_type VARCHAR(50) DEFAULT 'Veg',
    ADD COLUMN IF NOT EXISTS is_custom BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS created_by UUID DEFAULT auth.uid();

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'foods'
          AND column_name = 'serving_size'
          AND data_type IN ('character varying', 'text')
    ) THEN
        ALTER TABLE public.foods ALTER COLUMN serving_size DROP DEFAULT;
        ALTER TABLE public.foods
            ALTER COLUMN serving_size TYPE NUMERIC
            USING NULLIF(regexp_replace(serving_size::TEXT, '[^0-9.-]', '', 'g'), '')::NUMERIC;
    END IF;
END $$;

ALTER TABLE IF EXISTS public.foods
    ALTER COLUMN serving_size SET DEFAULT 100.0;

-- Tables absent from the live PostgREST schema.
CREATE TABLE IF NOT EXISTS public.nutrition_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    age INTEGER CHECK (age >= 1 AND age <= 120),
    gender VARCHAR(50),
    height NUMERIC(5, 2) CHECK (height > 0),
    weight NUMERIC(5, 2) CHECK (weight > 0),
    activity_level VARCHAR(50) DEFAULT 'Moderately Active',
    dietary_preference VARCHAR(50) DEFAULT 'Veg',
    food_preferences TEXT[] DEFAULT '{}',
    allergies TEXT[] DEFAULT '{}',
    medical_or_dietary_restrictions TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.nutrition_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    goal_type VARCHAR(50) NOT NULL CHECK (goal_type IN ('weight_loss', 'weight_gain', 'maintenance', 'muscle_gain', 'healthy_eating')),
    target_weight NUMERIC(5, 2),
    daily_calorie_target NUMERIC(7, 2) NOT NULL DEFAULT 2000,
    daily_protein_target NUMERIC(6, 2) NOT NULL DEFAULT 150,
    daily_carbs_target NUMERIC(6, 2) NOT NULL DEFAULT 250,
    daily_fat_target NUMERIC(6, 2) NOT NULL DEFAULT 70,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE IF EXISTS public.nutrition_goals
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- The live project currently has a legacy FK from nutrition_goals.user_id
-- to public.users. Ownership IDs are Supabase Auth UUIDs, so use auth.users.
ALTER TABLE IF EXISTS public.nutrition_goals
    DROP CONSTRAINT IF EXISTS nutrition_goals_user_id_fkey;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'nutrition_goals_auth_user_id_fkey'
    ) THEN
        ALTER TABLE public.nutrition_goals
            ADD CONSTRAINT nutrition_goals_auth_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES auth.users(id) NOT VALID;
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS ux_nutrition_profiles_user_id
    ON public.nutrition_profiles(user_id);

CREATE TABLE IF NOT EXISTS public.meals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    meal_type VARCHAR(50) NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'Breakfast', 'Lunch', 'Dinner', 'Snacks')),
    meal_date DATE NOT NULL DEFAULT CURRENT_DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.meal_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_id UUID NOT NULL,
    food_id UUID,
    food_name VARCHAR(255) NOT NULL,
    quantity NUMERIC(6, 2) NOT NULL DEFAULT 1.0,
    serving_size VARCHAR(50) DEFAULT '1 serving',
    calories NUMERIC(7, 2) NOT NULL DEFAULT 0,
    protein NUMERIC(6, 2) NOT NULL DEFAULT 0,
    carbs NUMERIC(6, 2) NOT NULL DEFAULT 0,
    fats NUMERIC(6, 2) NOT NULL DEFAULT 0,
    fiber NUMERIC(6, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_meal_items_meal
        FOREIGN KEY (meal_id) REFERENCES public.meals(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS public.meal_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.meal_plan_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_plan_id UUID NOT NULL,
    food_id UUID,
    food_name VARCHAR(255) NOT NULL,
    meal_type VARCHAR(50) NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'Breakfast', 'Lunch', 'Dinner', 'Snacks')),
    quantity NUMERIC(6, 2) NOT NULL DEFAULT 1.0,
    day_number INTEGER NOT NULL DEFAULT 1 CHECK (day_number >= 1 AND day_number <= 31),
    calories NUMERIC(7, 2) DEFAULT 0,
    protein NUMERIC(6, 2) DEFAULT 0,
    carbs NUMERIC(6, 2) DEFAULT 0,
    fats NUMERIC(6, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_meal_plan_items_plan
        FOREIGN KEY (meal_plan_id) REFERENCES public.meal_plans(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS public.daily_nutrition (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    calories_consumed NUMERIC(7, 2) DEFAULT 0,
    protein_consumed NUMERIC(6, 2) DEFAULT 0,
    carbs_consumed NUMERIC(6, 2) DEFAULT 0,
    fats_consumed NUMERIC(6, 2) DEFAULT 0,
    fiber_consumed NUMERIC(6, 2) DEFAULT 0,
    water_intake NUMERIC(6, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_daily_nutrition_user_date UNIQUE (user_id, date)
);

CREATE TABLE IF NOT EXISTS public.progress_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    weight NUMERIC(5, 2) NOT NULL,
    bmi NUMERIC(4, 2),
    calories_consumed NUMERIC(7, 2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Parent/child integrity. These are added only when absent and do not alter rows.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_meal_items_food') THEN
        ALTER TABLE public.meal_items
            ADD CONSTRAINT fk_meal_items_food
            FOREIGN KEY (food_id) REFERENCES public.foods(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_meal_plan_items_food') THEN
        ALTER TABLE public.meal_plan_items
            ADD CONSTRAINT fk_meal_plan_items_food
            FOREIGN KEY (food_id) REFERENCES public.foods(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON public.users(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_nutrition_goals_user_id ON public.nutrition_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_meals_user_date ON public.meals(user_id, meal_date);
CREATE INDEX IF NOT EXISTS idx_meal_items_meal_id ON public.meal_items(meal_id);
CREATE INDEX IF NOT EXISTS idx_meal_plans_user_id ON public.meal_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_items_plan_day ON public.meal_plan_items(meal_plan_id, day_number);
CREATE INDEX IF NOT EXISTS idx_daily_nutrition_user_date ON public.daily_nutrition(user_id, date);
CREATE INDEX IF NOT EXISTS idx_progress_records_user_date ON public.progress_records(user_id, date);

-- Timestamp triggers are recreated by name only; data is untouched.
DROP TRIGGER IF EXISTS set_users_updated_at ON public.users;
CREATE TRIGGER set_users_updated_at
BEFORE UPDATE ON public.users
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS set_foods_updated_at ON public.foods;
CREATE TRIGGER set_foods_updated_at
BEFORE UPDATE ON public.foods
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS set_nutrition_profiles_updated_at ON public.nutrition_profiles;
CREATE TRIGGER set_nutrition_profiles_updated_at
BEFORE UPDATE ON public.nutrition_profiles
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS set_nutrition_goals_updated_at ON public.nutrition_goals;
CREATE TRIGGER set_nutrition_goals_updated_at
BEFORE UPDATE ON public.nutrition_goals
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS set_meals_updated_at ON public.meals;
CREATE TRIGGER set_meals_updated_at
BEFORE UPDATE ON public.meals
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS set_meal_plans_updated_at ON public.meal_plans;
CREATE TRIGGER set_meal_plans_updated_at
BEFORE UPDATE ON public.meal_plans
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS set_daily_nutrition_updated_at ON public.daily_nutrition;
CREATE TRIGGER set_daily_nutrition_updated_at
BEFORE UPDATE ON public.daily_nutrition
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- RLS is enabled on every application table.
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.foods ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meal_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meal_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meal_plan_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_nutrition ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.progress_records ENABLE ROW LEVEL SECURITY;

-- Recreate ownership policies idempotently. The server uses the secret key;
-- these policies also protect direct client access.
DROP POLICY IF EXISTS "Users can view own user record" ON public.users;
CREATE POLICY "Users can view own user record" ON public.users
FOR SELECT TO authenticated USING (auth.uid() = auth_user_id);

DROP POLICY IF EXISTS "Users can update own user record" ON public.users;
CREATE POLICY "Users can update own user record" ON public.users
FOR UPDATE TO authenticated USING (auth.uid() = auth_user_id)
WITH CHECK (auth.uid() = auth_user_id);

DROP POLICY IF EXISTS "Users can view own nutrition profile" ON public.nutrition_profiles;
CREATE POLICY "Users can view own nutrition profile" ON public.nutrition_profiles
FOR SELECT TO authenticated USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own nutrition profile" ON public.nutrition_profiles;
CREATE POLICY "Users can insert own nutrition profile" ON public.nutrition_profiles
FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own nutrition profile" ON public.nutrition_profiles;
CREATE POLICY "Users can update own nutrition profile" ON public.nutrition_profiles
FOR UPDATE TO authenticated USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can view own nutrition goals" ON public.nutrition_goals;
CREATE POLICY "Users can view own nutrition goals" ON public.nutrition_goals
FOR SELECT TO authenticated USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own nutrition goals" ON public.nutrition_goals;
CREATE POLICY "Users can insert own nutrition goals" ON public.nutrition_goals
FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own nutrition goals" ON public.nutrition_goals;
CREATE POLICY "Users can update own nutrition goals" ON public.nutrition_goals
FOR UPDATE TO authenticated USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Anyone can view foods" ON public.foods;
CREATE POLICY "Anyone can view foods" ON public.foods
FOR SELECT TO anon, authenticated
USING (COALESCE(is_custom, FALSE) = FALSE OR auth.uid() = created_by);

DROP POLICY IF EXISTS "Users can insert custom foods" ON public.foods;
CREATE POLICY "Users can insert custom foods" ON public.foods
FOR INSERT TO authenticated WITH CHECK (auth.uid() = created_by);

DROP POLICY IF EXISTS "Users can update own custom foods" ON public.foods;
CREATE POLICY "Users can update own custom foods" ON public.foods
FOR UPDATE TO authenticated USING (auth.uid() = created_by)
WITH CHECK (auth.uid() = created_by);

DROP POLICY IF EXISTS "Users can delete own custom foods" ON public.foods;
CREATE POLICY "Users can delete own custom foods" ON public.foods
FOR DELETE TO authenticated USING (auth.uid() = created_by);

DROP POLICY IF EXISTS "Users can manage own meals" ON public.meals;
CREATE POLICY "Users can manage own meals" ON public.meals
FOR ALL TO authenticated USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can manage own meal items" ON public.meal_items;
CREATE POLICY "Users can manage own meal items" ON public.meal_items
FOR ALL TO authenticated
USING (EXISTS (SELECT 1 FROM public.meals m WHERE m.id = meal_id AND m.user_id = auth.uid()))
WITH CHECK (EXISTS (SELECT 1 FROM public.meals m WHERE m.id = meal_id AND m.user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can manage own meal plans" ON public.meal_plans;
CREATE POLICY "Users can manage own meal plans" ON public.meal_plans
FOR ALL TO authenticated USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can manage own meal plan items" ON public.meal_plan_items;
CREATE POLICY "Users can manage own meal plan items" ON public.meal_plan_items
FOR ALL TO authenticated
USING (EXISTS (SELECT 1 FROM public.meal_plans p WHERE p.id = meal_plan_id AND p.user_id = auth.uid()))
WITH CHECK (EXISTS (SELECT 1 FROM public.meal_plans p WHERE p.id = meal_plan_id AND p.user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can manage own daily nutrition" ON public.daily_nutrition;
CREATE POLICY "Users can manage own daily nutrition" ON public.daily_nutrition
FOR ALL TO authenticated USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can manage own progress" ON public.progress_records;
CREATE POLICY "Users can manage own progress" ON public.progress_records
FOR ALL TO authenticated USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

NOTIFY pgrst, 'reload schema';
