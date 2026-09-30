-- ==========================================================
-- NUTRI-WELL PRODUCTION DATABASE SCHEMA (SUPABASE POSTGRESQL)
-- ==========================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. USERS TABLE (Preserved & Enhanced)
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    auth_user_id UUID UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure auth_user_id column exists if table was created previously
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='auth_user_id') THEN
        ALTER TABLE public.users ADD COLUMN auth_user_id UUID UNIQUE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='updated_at') THEN
        ALTER TABLE public.users ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- 2. NUTRITION PROFILES TABLE
CREATE TABLE IF NOT EXISTS public.nutrition_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    age INTEGER CHECK (age >= 1 AND age <= 120),
    gender VARCHAR(50),
    height NUMERIC(5, 2) CHECK (height > 0), -- in cm
    weight NUMERIC(5, 2) CHECK (weight > 0), -- in kg
    activity_level VARCHAR(50) DEFAULT 'Moderately Active',
    dietary_preference VARCHAR(50) DEFAULT 'Veg',
    food_preferences TEXT[] DEFAULT '{}',
    allergies TEXT[] DEFAULT '{}',
    medical_or_dietary_restrictions TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. NUTRITION GOALS TABLE
CREATE TABLE IF NOT EXISTS public.nutrition_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    goal_type VARCHAR(50) NOT NULL CHECK (goal_type IN ('weight_loss', 'weight_gain', 'maintenance', 'muscle_gain', 'healthy_eating')),
    target_weight NUMERIC(5, 2),
    daily_calorie_target NUMERIC(7, 2) NOT NULL,
    daily_protein_target NUMERIC(6, 2) NOT NULL,
    daily_carbs_target NUMERIC(6, 2) NOT NULL,
    daily_fat_target NUMERIC(6, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. FOODS TABLE
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
    serving_size VARCHAR(50) NOT NULL DEFAULT '100g',
    serving_unit VARCHAR(50) NOT NULL DEFAULT 'g',
    category VARCHAR(100) NOT NULL DEFAULT 'General',
    diet_type VARCHAR(50) DEFAULT 'Veg',
    is_custom BOOLEAN DEFAULT FALSE,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. MEALS TABLE
CREATE TABLE IF NOT EXISTS public.meals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    meal_type VARCHAR(50) NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'Breakfast', 'Lunch', 'Dinner', 'Snacks')),
    meal_date DATE NOT NULL DEFAULT CURRENT_DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. MEAL ITEMS TABLE
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
    CONSTRAINT fk_mealitem_meal FOREIGN KEY (meal_id) REFERENCES public.meals(id) ON DELETE CASCADE
);

-- 7. MEAL PLANS TABLE
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

-- 8. MEAL PLAN ITEMS TABLE
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
    CONSTRAINT fk_mealplanitem_plan FOREIGN KEY (meal_plan_id) REFERENCES public.meal_plans(id) ON DELETE CASCADE
);

-- 9. DAILY NUTRITION TABLE
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
    CONSTRAINT uq_user_daily_date UNIQUE (user_id, date)
);

-- 10. PROGRESS RECORDS TABLE
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

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_nutrition_profiles_user_id ON public.nutrition_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_nutrition_goals_user_id ON public.nutrition_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_meals_user_date ON public.meals(user_id, meal_date);
CREATE INDEX IF NOT EXISTS idx_meal_items_meal_id ON public.meal_items(meal_id);
CREATE INDEX IF NOT EXISTS idx_meal_plans_user_id ON public.meal_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_items_plan ON public.meal_plan_items(meal_plan_id, day_number);
CREATE INDEX IF NOT EXISTS idx_daily_nutrition_user_date ON public.daily_nutrition(user_id, date);
CREATE INDEX IF NOT EXISTS idx_progress_records_user_date ON public.progress_records(user_id, date);
CREATE INDEX IF NOT EXISTS idx_foods_name ON public.foods(name);
CREATE INDEX IF NOT EXISTS idx_foods_category ON public.foods(category);
