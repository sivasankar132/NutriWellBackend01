-- ==========================================================
-- NUTRI-WELL PRODUCTION ROW LEVEL SECURITY (RLS) POLICIES
-- ==========================================================

-- 1. Enable RLS on all tables
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

-- 2. USERS POLICIES
DROP POLICY IF EXISTS "Users can view their own record" ON public.users;
CREATE POLICY "Users can view their own record"
ON public.users FOR SELECT
TO authenticated
USING (auth.uid() = auth_user_id);

DROP POLICY IF EXISTS "Users can update their own record" ON public.users;
CREATE POLICY "Users can update their own record"
ON public.users FOR UPDATE
TO authenticated
USING (auth.uid() = auth_user_id)
WITH CHECK (auth.uid() = auth_user_id);

-- Service role bypasses RLS automatically

-- 3. NUTRITION PROFILES POLICIES
DROP POLICY IF EXISTS "Users can view own nutrition profile" ON public.nutrition_profiles;
CREATE POLICY "Users can view own nutrition profile"
ON public.nutrition_profiles FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own nutrition profile" ON public.nutrition_profiles;
CREATE POLICY "Users can insert own nutrition profile"
ON public.nutrition_profiles FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own nutrition profile" ON public.nutrition_profiles;
CREATE POLICY "Users can update own nutrition profile"
ON public.nutrition_profiles FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 4. NUTRITION GOALS POLICIES
DROP POLICY IF EXISTS "Users can view own goals" ON public.nutrition_goals;
CREATE POLICY "Users can view own goals"
ON public.nutrition_goals FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own goals" ON public.nutrition_goals;
CREATE POLICY "Users can insert own goals"
ON public.nutrition_goals FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own goals" ON public.nutrition_goals;
CREATE POLICY "Users can update own goals"
ON public.nutrition_goals FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 5. FOODS POLICIES (Public read for system items, private read/write for custom items)
DROP POLICY IF EXISTS "Anyone can view standard foods" ON public.foods;
CREATE POLICY "Anyone can view standard foods"
ON public.foods FOR SELECT
TO authenticated, anon
USING (is_custom = FALSE OR auth.uid() = created_by);

DROP POLICY IF EXISTS "Users can insert custom foods" ON public.foods;
CREATE POLICY "Users can insert custom foods"
ON public.foods FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = created_by);

-- 6. MEALS & MEAL ITEMS POLICIES
DROP POLICY IF EXISTS "Users can view own meals" ON public.meals;
CREATE POLICY "Users can view own meals"
ON public.meals FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own meals" ON public.meals;
CREATE POLICY "Users can insert own meals"
ON public.meals FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own meals" ON public.meals;
CREATE POLICY "Users can update own meals"
ON public.meals FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own meals" ON public.meals;
CREATE POLICY "Users can delete own meals"
ON public.meals FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- Meal items inherit via meal_id relation
DROP POLICY IF EXISTS "Users can view items of own meals" ON public.meal_items;
CREATE POLICY "Users can view items of own meals"
ON public.meal_items FOR SELECT
TO authenticated
USING (EXISTS (SELECT 1 FROM public.meals WHERE meals.id = meal_items.meal_id AND meals.user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can insert items to own meals" ON public.meal_items;
CREATE POLICY "Users can insert items to own meals"
ON public.meal_items FOR INSERT
TO authenticated
WITH CHECK (EXISTS (SELECT 1 FROM public.meals WHERE meals.id = meal_items.meal_id AND meals.user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can update items in own meals" ON public.meal_items;
CREATE POLICY "Users can update items in own meals"
ON public.meal_items FOR UPDATE
TO authenticated
USING (EXISTS (SELECT 1 FROM public.meals WHERE meals.id = meal_items.meal_id AND meals.user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can delete items from own meals" ON public.meal_items;
CREATE POLICY "Users can delete items from own meals"
ON public.meal_items FOR DELETE
TO authenticated
USING (EXISTS (SELECT 1 FROM public.meals WHERE meals.id = meal_items.meal_id AND meals.user_id = auth.uid()));

-- 7. MEAL PLANS POLICIES
DROP POLICY IF EXISTS "Users can view own meal plans" ON public.meal_plans;
CREATE POLICY "Users can view own meal plans"
ON public.meal_plans FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own meal plans" ON public.meal_plans;
CREATE POLICY "Users can insert own meal plans"
ON public.meal_plans FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own meal plans" ON public.meal_plans;
CREATE POLICY "Users can update own meal plans"
ON public.meal_plans FOR UPDATE
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own meal plans" ON public.meal_plans;
CREATE POLICY "Users can delete own meal plans"
ON public.meal_plans FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- 8. DAILY NUTRITION POLICIES
DROP POLICY IF EXISTS "Users can view own daily nutrition" ON public.daily_nutrition;
CREATE POLICY "Users can view own daily nutrition"
ON public.daily_nutrition FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert/update own daily nutrition" ON public.daily_nutrition;
CREATE POLICY "Users can insert/update own daily nutrition"
ON public.daily_nutrition FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 9. PROGRESS RECORDS POLICIES
DROP POLICY IF EXISTS "Users can view own progress" ON public.progress_records;
CREATE POLICY "Users can view own progress"
ON public.progress_records FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own progress" ON public.progress_records;
CREATE POLICY "Users can insert own progress"
ON public.progress_records FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own progress" ON public.progress_records;
CREATE POLICY "Users can delete own progress"
ON public.progress_records FOR DELETE
TO authenticated
USING (auth.uid() = user_id);
