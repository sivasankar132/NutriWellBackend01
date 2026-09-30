-- ==========================================================
-- NUTRI-WELL PRODUCTION SEED DATA (FOOD DATABASE)
-- ==========================================================

INSERT INTO public.foods (name, category, serving_size, serving_unit, calories, protein, carbs, fats, fiber, sugar, sodium, diet_type, is_custom)
VALUES
-- High Protein / Staples
('Boiled Egg', 'Protein', '1 large (50g)', 'piece', 78, 6.3, 0.6, 5.3, 0, 0.6, 62, 'Eggetarian', FALSE),
('Egg White', 'Protein', '1 large (33g)', 'piece', 17, 3.6, 0.2, 0.1, 0, 0.2, 55, 'Eggetarian', FALSE),
('Grilled Chicken Breast', 'Protein', '100g', 'g', 165, 31.0, 0.0, 3.6, 0, 0, 74, 'Non-Veg', FALSE),
('Paneer (Cottage Cheese)', 'Protein', '100g', 'g', 265, 18.3, 3.4, 20.8, 0, 2.0, 18, 'Veg', FALSE),
('Low Fat Paneer', 'Protein', '100g', 'g', 175, 25.0, 4.0, 6.0, 0, 2.0, 22, 'Veg', FALSE),
('Tofu (Firm)', 'Protein', '100g', 'g', 76, 8.0, 1.9, 4.8, 0.3, 0.5, 7, 'Vegan', FALSE),
('Soya Chunks (Dry)', 'Protein', '100g', 'g', 345, 52.0, 33.0, 0.5, 13.0, 0, 20, 'Vegan', FALSE),
('Cooked Yellow Dal (Moong/Toor)', 'Protein', '1 cup (200g)', 'cup', 180, 12.0, 28.0, 2.5, 7.0, 1.5, 240, 'Veg', FALSE),
('Cooked Chana Masala (Chickpeas)', 'Protein', '1 cup (200g)', 'cup', 240, 11.5, 36.0, 5.0, 9.0, 3.0, 320, 'Veg', FALSE),
('Cooked Rajma (Kidney Beans)', 'Protein', '1 cup (200g)', 'cup', 220, 13.0, 35.0, 2.0, 10.0, 2.0, 290, 'Veg', FALSE),
('Whey Protein Isolate', 'Protein', '1 scoop (30g)', 'scoop', 120, 25.0, 1.5, 1.0, 0, 0.5, 50, 'Veg', FALSE),
('Greek Yogurt (Plain 0% Fat)', 'Dairy', '100g', 'g', 59, 10.0, 3.6, 0.4, 0, 3.2, 36, 'Veg', FALSE),
('Curd / Dahi (Homemade Whole Milk)', 'Dairy', '100g', 'g', 98, 3.5, 4.7, 4.3, 0, 4.0, 46, 'Veg', FALSE),
('Cow Milk (Toned)', 'Dairy', '1 glass (250ml)', 'ml', 150, 7.8, 12.0, 7.5, 0, 12.0, 105, 'Veg', FALSE),

-- Carbohydrates & Grains
('Cooked White Rice', 'Carbs', '1 cup (150g)', 'cup', 195, 4.0, 43.0, 0.4, 0.6, 0.1, 1, 'Vegan', FALSE),
('Cooked Brown Rice', 'Carbs', '1 cup (150g)', 'cup', 165, 3.5, 35.0, 1.4, 2.8, 0.2, 2, 'Vegan', FALSE),
('Whole Wheat Roti (No Ghee)', 'Carbs', '1 medium (35g)', 'piece', 104, 3.1, 21.0, 0.5, 3.2, 0.4, 5, 'Vegan', FALSE),
('Oats (Rolled, Raw)', 'Carbs', '50g', 'g', 190, 6.5, 33.0, 3.5, 5.0, 0.5, 2, 'Vegan', FALSE),
('Brown Bread', 'Carbs', '1 slice (30g)', 'slice', 75, 3.0, 14.0, 0.9, 1.8, 1.5, 130, 'Vegan', FALSE),
('Boiled Sweet Potato', 'Carbs', '1 medium (130g)', 'piece', 112, 2.0, 26.0, 0.1, 3.9, 5.4, 72, 'Vegan', FALSE),
('Idli (Steamed)', 'Carbs', '1 piece (40g)', 'piece', 58, 2.0, 12.0, 0.2, 0.8, 0.2, 65, 'Vegan', FALSE),
('Dosa (Plain, Medium)', 'Carbs', '1 piece (80g)', 'piece', 168, 3.9, 28.0, 3.7, 1.4, 0.5, 110, 'Veg', FALSE),

-- Vegetables & Greens
('Spinach (Palak, Cooked)', 'Vegetables', '1 cup (180g)', 'cup', 41, 5.3, 6.7, 0.5, 4.3, 0.8, 126, 'Vegan', FALSE),
('Broccoli (Steamed)', 'Vegetables', '1 cup (100g)', 'cup', 35, 2.4, 7.2, 0.4, 2.6, 1.4, 33, 'Vegan', FALSE),
('Cucumber (Raw with peel)', 'Vegetables', '1 medium (200g)', 'piece', 30, 1.3, 7.3, 0.2, 1.0, 3.4, 4, 'Vegan', FALSE),
('Tomato (Raw)', 'Vegetables', '1 medium (120g)', 'piece', 22, 1.1, 4.8, 0.2, 1.5, 3.2, 6, 'Vegan', FALSE),
('Mixed Vegetable Curry', 'Vegetables', '1 cup (200g)', 'cup', 140, 3.5, 16.0, 6.5, 4.5, 4.0, 310, 'Veg', FALSE),

-- Fruits
('Banana (Medium)', 'Fruits', '1 piece (118g)', 'piece', 105, 1.3, 27.0, 0.3, 3.1, 14.4, 1, 'Vegan', FALSE),
('Apple (Medium with skin)', 'Fruits', '1 piece (182g)', 'piece', 95, 0.5, 25.0, 0.3, 4.4, 19.0, 2, 'Vegan', FALSE),
('Papaya (Cubed)', 'Fruits', '1 cup (145g)', 'cup', 62, 0.7, 15.7, 0.4, 2.5, 11.3, 12, 'Vegan', FALSE),
('Pomegranate (Arils)', 'Fruits', '0.5 cup (87g)', 'cup', 72, 1.5, 16.3, 1.0, 3.5, 11.9, 3, 'Vegan', FALSE),

-- Healthy Fats & Nuts
('Almonds (Raw)', 'Healthy Fats', '10 pieces (15g)', 'piece', 87, 3.2, 3.2, 7.5, 1.8, 0.7, 0, 'Vegan', FALSE),
('Walnuts (Halves)', 'Healthy Fats', '5 pieces (15g)', 'piece', 98, 2.3, 2.0, 9.8, 1.0, 0.4, 0, 'Vegan', FALSE),
('Peanut Butter (Unsweetened)', 'Healthy Fats', '1 tbsp (16g)', 'tbsp', 94, 4.0, 3.0, 8.0, 1.0, 0.5, 5, 'Vegan', FALSE),
('Olive Oil / Mustard Oil', 'Healthy Fats', '1 tbsp (14g)', 'tbsp', 119, 0.0, 0.0, 13.5, 0, 0, 0, 'Vegan', FALSE),
('Desi Cow Ghee', 'Healthy Fats', '1 tsp (5g)', 'tsp', 45, 0.0, 0.0, 5.0, 0, 0, 0, 'Veg', FALSE)
ON CONFLICT DO NOTHING;
