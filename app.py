import os
import requests
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

USDA_API_KEY = os.getenv("USDA_API_KEY")

FALLBACK_CALORIES = {
    "egg": 143, "eggs": 143,
    "rice": 130, "cooked rice": 130,
    "spinach": 23, "tofu": 76,
    "chicken": 165, "bread": 79,
    "carrot": 41, "onion": 40,
    "potato": 77, "milk": 61,
    "soy sauce": 53, "oil": 884,
    "cooking oil": 884,
    "garlic": 149, "ginger": 80,
    "noodles": 138, "pasta": 131,
    "flour": 364, "sugar": 387,
    "butter": 717, "cheese": 402,
    "tomato": 18, "mushroom": 22,
    "broccoli": 34, "corn": 86,
    "bok choy": 13, "cabbage": 25,
    "pork": 242, "beef": 250,
    "shrimp": 99, "fish": 136,
    "coconut milk": 197, "anchovies": 131,
    "spring onion": 32, "spring onions": 32,
    "salt": 0, "pepper": 251
}

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ── USDA Calorie Lookup ───────────────────────────────────────────────────
def get_calories_usda(ingredient):
    try:
        url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {
            "query": ingredient.strip(),
            "api_key": USDA_API_KEY,
            "pageSize": 1,
            "dataType": "SR Legacy"
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        foods = data.get("foods", [])
        if foods:
            nutrients = foods[0].get("foodNutrients", [])
            for n in nutrients:
                if "Energy" in n.get("nutrientName", ""):
                    cal = n.get("value")
                    if cal:
                        return round(float(cal))
    except Exception:
        pass
    ingredient_lower = ingredient.strip().lower()
    for key in FALLBACK_CALORIES:
        if key in ingredient_lower:
            return FALLBACK_CALORIES[key]
    return None


def estimate_calories(ingredients_text):
    if not ingredients_text.strip():
        return ""
    ingredients = [i.strip() for i in ingredients_text.split(",")]
    lines = []
    for ing in ingredients:
        if not ing:
            continue
        cal = get_calories_usda(ing)
        if cal:
            lines.append(f"  • {ing.capitalize()}: ~{cal} kcal/100g")
        else:
            lines.append(f"  • {ing.capitalize()}: data unavailable")
    summary = "\n".join(lines)
    summary += "\n\n  📊 Source: USDA FoodData Central"
    summary += "\n  ⚠️ Estimates are per 100g of raw ingredient."
    return summary


# ── Prompt Builder ────────────────────────────────────────────────────────
def build_prompt(profile, request, leftovers, calorie_info=""):
    calorie_section = f"\nIngredient Calorie Reference (from USDA FoodData Central):\n{calorie_info}" if calorie_info else ""
    return f"""
You are a personalized healthy and sustainable cooking assistant.

User Profile:
- Age: {profile['age']}
- Gender: {profile['gender']}
- Health conditions: {profile['health']}
- Dietary preferences: {profile['diet']}
- Preferred meal type: {profile['meal_type']}
- Skill level: {profile['skill']}

Meal Request:
- Time available: {request['time']} minutes
- Servings: {request['servings']}
- Difficulty: {request['difficulty']}
- Ingredients: {request['ingredients']}
- Current leftovers: {leftovers}
{calorie_section}

Generate a response with:
1. Recipe Name
2. Ingredients (with approximate quantities)
3. Steps
4. Estimated Calories per serving (use the USDA reference data above where available)
5. Why this recipe suits the user
6. How it helps reduce food waste
7. What to cook next using remaining leftovers

Keep it clear and practical. Add a disclaimer that calorie estimates are approximate.
"""


# ── Image Scanning (Demo Mode) ────────────────────────────────────────────
def scan_ingredients_from_image(image_path):
    if image_path is None:
        return ""
    return "spring onion, eggs, rice, soy sauce, cooking oil, salt, pepper"


# ── Recipe Generator ──────────────────────────────────────────────────────
def generate_recipe(age, gender, health, diet, meal_type, skill,
                    time, servings, difficulty, ingredients, leftovers):
    profile = {
        "age": age, "gender": gender, "health": health,
        "diet": diet, "meal_type": meal_type, "skill": skill
    }
    request = {
        "time": time, "servings": servings,
        "difficulty": difficulty, "ingredients": ingredients
    }
    calorie_info = estimate_calories(ingredients)
    prompt = build_prompt(profile, request, leftovers, calorie_info)

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
        )
        output = response.choices[0].message.content
        calorie_display = f"\n\n---\n**📊 Calorie Reference (USDA FoodData Central)**\n{calorie_info}" if calorie_info else ""
        return f"## Your Personalized Recipe\n\n{output}{calorie_display}"

    except Exception as e:
        err = str(e)
        if "402" in err or "Insufficient Balance" in err:
            return """## Your Personalized Recipe

**Demo Recipe: Egg Fried Rice**

**Ingredients**
- 2 cups cooked rice
- 2 eggs
- 1 tbsp soy sauce
- 1 tbsp cooking oil
- Spring onions, salt, pepper to taste

**Steps**
1. Heat oil in a wok over medium-high heat.
2. Crack eggs in and scramble lightly.
3. Add leftover rice and stir fry for 3 minutes.
4. Season with soy sauce, salt and pepper.
5. Garnish with spring onions and serve hot.

**Estimated Calories per serving:** ~380 kcal

**Why this recipe suits you**
- Quick and easy — ready in under 15 minutes
- Uses up leftover rice and eggs efficiently

**How it helps reduce food waste**
- Uses leftover cooked rice that would otherwise be discarded

**What to cook next**
- Use remaining spring onions and egg for a simple omelette

---
**📊 Calorie Reference (USDA FoodData Central)**
• Eggs: ~143 kcal/100g | Rice: ~130 kcal/100g
• Spring onion: ~32 kcal/100g | Soy sauce: ~53 kcal/100g
"""
        return f"Error: {err}"


# ── Page switch functions ─────────────────────────────────────────────────
def generate_and_switch(age, gender, health, diet, meal_type, skill,
                        time, servings, difficulty, ingredients, leftovers):
    recipe = generate_recipe(age, gender, health, diet, meal_type, skill,
                             time, servings, difficulty, ingredients, leftovers)
    # Return recipe text + switch inner_tabs to index 1 (recipe page)
    return recipe, gr.Tabs(selected=1)


def go_to_rating_page():
    return gr.Tabs(selected=2)


def go_back_to_input():
    return gr.Tabs(selected=0)


def save_and_go_back(new_leftovers_input, current_saved, rating):
    combined = new_leftovers_input if not current_saved else f"{current_saved}, {new_leftovers_input}"
    confirmation = f"✅ Saved! Rating: {rating}. Leftovers stored for next recipe."
    return combined, combined, confirmation, gr.Tabs(selected=0)


# ── CSS ───────────────────────────────────────────────────────────────────
custom_css = """
body {
    font-family: Arial, sans-serif !important;
    background: #f5f1e8;
}

.gradio-container {
    background: transparent !important;
}

#mobile-shell {
    max-width: 390px;
    margin: 20px auto;
    background: #fffaf3;
    border: 1px solid #e7dccb;
    border-radius: 28px;
    padding: 18px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.08);
}

#app-title {
    text-align: center !important;
    font-size: 42px !important;
    font-weight: 700 !important;
    color: #5c3b1e;
    margin-bottom: 12px;
}

.section-title {
    font-size: 18px;
    font-weight: 700;
    color: #f1642e;
    margin-top: 10px;
    margin-bottom: 8px;
}

/* Hide the inner tabs nav bar so users dont see it */
#inner-tabs .tab-nav {
    display: none !important;
}

#generate-btn {
    background: #f1642e !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
}

#tried-btn {
    background: #4CAF50 !important;
    color: white !important;
    border-radius: 24px !important;
    font-weight: 700 !important;
}

#save-btn {
    background: #9E9E9E !important;
    color: white !important;
    border-radius: 24px !important;
    font-weight: 700 !important;
}

#retry-btn {
    background: #f44336 !important;
    color: white !important;
    border-radius: 24px !important;
    font-weight: 700 !important;
}

#scan-btn {
    background: #f1642e !important;
    color: white !important;
    border-radius: 24px !important;
    font-weight: 700 !important;
}

#save-rating-btn {
    background: #f1642e !important;
    color: white !important;
    border-radius: 24px !important;
    font-weight: 700 !important;
}

.recipe-card {
    background: white;
    border: 1px solid #ecdcc7;
    border-radius: 16px;
    padding: 12px;
    margin-bottom: 12px;
}

.feed-title {
    font-size: 16px;
    font-weight: 700;
    color: #5c3b1e;
    margin-bottom: 4px;
}

.feed-sub {
    font-size: 13px;
    color: #6d6d6d;
}

textarea, input {
    border-radius: 12px !important;
}
"""

# ── UI ────────────────────────────────────────────────────────────────────
with gr.Blocks(css=custom_css) as app:

    # Global state
    saved_leftovers = gr.State("")

    with gr.Column(elem_id="mobile-shell"):
        gr.Markdown("<div id='app-title'>NourishAI</div>")

        # ── Outer tabs (main navigation) ──────────────────────────────────
        with gr.Tabs():

            # ── Home Tab ──────────────────────────────────────────────────
            with gr.Tab("home"):
                gr.HTML("""
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; padding-top:8px;">
                    <div style="border-radius:14px; overflow:hidden; background:white; border:1px solid #ecdcc7;">
                        <img src="https://images.unsplash.com/photo-1547592180-85f173990554?w=400" style="width:100%; height:130px; object-fit:cover;" />
                        <div style="padding:6px 8px; font-size:11px; color:#5c3b1e;">Veggie Bowl • Easy • 20 min</div>
                    </div>
                    <div style="border-radius:14px; overflow:hidden; background:white; border:1px solid #ecdcc7;">
                        <img src="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400" style="width:100%; height:130px; object-fit:cover;" />
                        <div style="padding:6px 8px; font-size:11px; color:#5c3b1e;">Lunch Plate • Easy • 30 min</div>
                    </div>
                    <div style="border-radius:14px; overflow:hidden; background:white; border:1px solid #ecdcc7;">
                        <img src="https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=400" style="width:100%; height:130px; object-fit:cover;" />
                        <div style="padding:6px 8px; font-size:11px; color:#5c3b1e;">Dinner Idea • Medium • 45 min</div>
                    </div>
                    <div style="border-radius:14px; overflow:hidden; background:white; border:1px solid #ecdcc7;">
                        <img src="https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=400" style="width:100%; height:130px; object-fit:cover;" />
                        <div style="padding:6px 8px; font-size:11px; color:#5c3b1e;">Salad Bowl • Easy • 15 min</div>
                    </div>
                    <div style="border-radius:14px; overflow:hidden; background:white; border:1px solid #ecdcc7;">
                        <img src="https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400" style="width:100%; height:130px; object-fit:cover;" />
                        <div style="padding:6px 8px; font-size:11px; color:#5c3b1e;">Grilled Chicken • Medium • 35 min</div>
                    </div>
                    <div style="border-radius:14px; overflow:hidden; background:white; border:1px solid #ecdcc7;">
                        <img src="https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=400" style="width:100%; height:130px; object-fit:cover;" />
                        <div style="padding:6px 8px; font-size:11px; color:#5c3b1e;">Fresh Bowl • Easy • 10 min</div>
                    </div>
                </div>
                """)

            # ── Search Tab ────────────────────────────────────────────────
            with gr.Tab("search"):
                gr.Markdown("<div class='section-title'>Search</div>")
                gr.HTML("""
                <div style="margin-bottom:10px;">
                    <input type="text" placeholder="🔍  Search recipes, ingredients..."
                    style="width:100%; padding:10px 14px; border-radius:12px; border:1px solid #ecdcc7;
                    font-size:14px; color:#5c3b1e; background:#fff; box-sizing:border-box;" />
                </div>
                <div class="recipe-card">
                    <div class="feed-title">Popular Ingredients</div>
                    <div class="feed-sub">Chicken • Rice • Spinach • Eggs • Tofu • Carrot</div>
                </div>
                <div class="recipe-card">
                    <div class="feed-title">Trending Recipes</div>
                    <div class="feed-sub">Veggie Stir Fry • Avocado Toast • Miso Soup • Greek Salad</div>
                </div>
                <div class="recipe-card">
                    <div class="feed-title">Browse by Diet</div>
                    <div class="feed-sub">Vegan • Vegetarian • Halal • Keto • Low-Calorie</div>
                </div>
                <div class="recipe-card">
                    <div class="feed-title">Quick & Easy</div>
                    <div class="feed-sub">Recipes under 20 minutes — perfect for busy days.</div>
                </div>
                """)

            # ── Create Tab ────────────────────────────────────────────────
            with gr.Tab("(create)"):

                # Inner tabs — nav bar hidden via CSS, switched programmatically
                with gr.Tabs(elem_id="inner-tabs") as inner_tabs:

                    # ── Inner Page 0: Input Form ──────────────────────────
                    with gr.Tab("input", id=0):
                        gr.Markdown("<div class='section-title'>Profile</div>")
                        age = gr.Dropdown(["", "Under 18", "18-25", "26-40", "40+"], label="Age (optional)", value="")
                        gender = gr.Dropdown(["", "Male", "Female", "Other"], label="Gender (optional)", value="")
                        health = gr.Textbox(label="Health Conditions (optional)")
                        diet = gr.Dropdown(
                            ["None", "Vegetarian", "Vegan", "Halal", "Keto"],
                            label="Dietary Preference"
                        )
                        meal_type = gr.Dropdown(
                            ["Quick meal", "Balanced meal", "Full course"],
                            label="Meal Type"
                        )
                        skill = gr.Dropdown(
                            ["Beginner", "Intermediate", "Advanced"],
                            label="Skill Level"
                        )

                        gr.Markdown("<div class='section-title'>Meal Request</div>")
                        time = gr.Slider(5, 120, value=30, label="Time Available (minutes)")
                        servings = gr.Slider(1, 6, value=2, label="Servings")
                        difficulty = gr.Dropdown(["Easy", "Medium", "Hard"], label="Difficulty")

                        gr.Markdown("<div class='section-title'>Ingredients</div>")
                        ingredient_image = gr.Image(
                            type="filepath",
                            label="📷 Upload a photo of your ingredients (optional)"
                        )
                        scan_btn = gr.Button("Scan Ingredients", elem_id="scan-btn")
                        ingredients = gr.Textbox(
                            label="Available Ingredients",
                            placeholder="e.g. eggs, rice, soy sauce, spring onion"
                        )
                        leftovers = gr.Textbox(
                            label="Current Leftovers",
                            placeholder="e.g. fried chicken, cooked rice"
                        )

                        scan_btn.click(
                            scan_ingredients_from_image,
                            inputs=[ingredient_image],
                            outputs=[ingredients]
                        )

                        generate_btn = gr.Button("Generate Recipe", elem_id="generate-btn")

                    # ── Inner Page 1: Recipe Output ───────────────────────
                    with gr.Tab("recipe", id=1):
                        output = gr.Markdown()
                        gr.HTML("<div style='margin-top:16px; margin-bottom:8px; font-size:13px; color:#888;'>What would you like to do?</div>")
                        with gr.Row():
                            tried_btn = gr.Button("✅ I've tried it!", elem_id="tried-btn")
                            save_btn = gr.Button("🔖 Save this", elem_id="save-btn")
                            retry_btn = gr.Button("❌ Retry", elem_id="retry-btn")

                    # ── Inner Page 2: Rating ──────────────────────────────
                    with gr.Tab("rating", id=2):
                        gr.Markdown("<div class='section-title'>Rate the recipe!</div>")
                        rating = gr.Dropdown(
                            ["⭐⭐⭐⭐⭐ 5 — Loved it!",
                             "⭐⭐⭐⭐ 4 — Pretty good",
                             "⭐⭐⭐ 3 — It was okay",
                             "⭐⭐ 2 — Not great",
                             "⭐ 1 — Didn't like it"],
                            label="Rating"
                        )
                        gr.Markdown("<div class='section-title'>What leftovers do you have?</div>")
                        new_leftovers = gr.Textbox(
                            label="Remaining Leftovers",
                            placeholder="Example: half block tofu, 1 cup rice..."
                        )
                        save_rating_btn = gr.Button("Save", elem_id="save-rating-btn")
                        rating_confirmation = gr.Markdown()

                # ── Button wiring ─────────────────────────────────────────
                generate_btn.click(
                    generate_and_switch,
                    inputs=[age, gender, health, diet, meal_type, skill,
                            time, servings, difficulty, ingredients, leftovers],
                    outputs=[output, inner_tabs]
                )

                tried_btn.click(
                    go_to_rating_page,
                    inputs=[],
                    outputs=[inner_tabs]
                )

                retry_btn.click(
                    go_back_to_input,
                    inputs=[],
                    outputs=[inner_tabs]
                )

                save_btn.click(
                    go_back_to_input,
                    inputs=[],
                    outputs=[inner_tabs]
                )

                save_rating_btn.click(
                    save_and_go_back,
                    inputs=[new_leftovers, saved_leftovers, rating],
                    outputs=[saved_leftovers, leftovers, rating_confirmation, inner_tabs]
                )

            # ── Saved Tab ─────────────────────────────────────────────────
            with gr.Tab("saved"):
                gr.HTML("""
                <div style="padding: 4px 0;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <div style="font-size:18px; font-weight:700; color:#f1642e;">Saved posts</div>
                        <button style="background:#f1642e; color:white; border:none; border-radius:20px; padding:5px 14px; font-size:13px; font-weight:600;">Filter</button>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:20px;">
                        <div style="border-radius:14px; overflow:hidden; background:white; border:1px solid #ecdcc7;">
                            <img src="https://images.unsplash.com/photo-1547592180-85f173990554?w=400" style="width:100%; height:130px; object-fit:cover;" />
                            <div style="padding:6px 8px; font-size:11px; color:#5c3b1e;">Veggie Bowl • Easy • 20 min • 2 servings</div>
                        </div>
                        <div style="border-radius:14px; overflow:hidden; background:white; border:1px solid #ecdcc7;">
                            <img src="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400" style="width:100%; height:130px; object-fit:cover;" />
                            <div style="padding:6px 8px; font-size:11px; color:#5c3b1e;">Lunch Plate • Easy • 30 min • 2 servings</div>
                        </div>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <div style="font-size:18px; font-weight:700; color:#f1642e;">Saved boards</div>
                        <button style="background:#f1642e; color:white; border:none; border-radius:20px; padding:5px 14px; font-size:13px; font-weight:600;">Add</button>
                    </div>
                    <div style="background:white; border:1px solid #ecdcc7; border-radius:16px; padding:12px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-size:15px; font-weight:700; color:#5c3b1e;">thai cuisine</div>
                            <div style="font-size:12px; color:#f1642e; margin-top:2px;">Edit</div>
                        </div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:3px; width:110px; height:80px;">
                            <img src="https://images.unsplash.com/photo-1547592180-85f173990554?w=200" style="width:100%; height:100%; object-fit:cover; border-radius:6px 0 0 6px;" />
                            <div style="display:flex; flex-direction:column; gap:3px;">
                                <img src="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=200" style="width:100%; height:48%; object-fit:cover; border-radius:0 6px 0 0;" />
                                <img src="https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=200" style="width:100%; height:48%; object-fit:cover; border-radius:0 0 6px 0;" />
                            </div>
                        </div>
                    </div>
                </div>
                """)

            # ── Profile Tab ───────────────────────────────────────────────
            with gr.Tab("profile"):
                gr.Markdown("<div class='section-title'>Profile & Settings</div>")
                gr.HTML("""
                <div style="padding: 4px 0;">
                    <div style="background:white; border:1px solid #ecdcc7; border-radius:16px; padding:12px; margin-bottom:12px;">
                        <div style="font-size:16px; font-weight:600; color:#5c3b1e; margin-bottom:4px;">Preferences</div>
                        <div style="font-size:13px; color:#6d6d6d;">Edit dietary needs, meal type, and cooking preferences anytime.</div>
                    </div>
                    <div style="background:white; border:1px solid #ecdcc7; border-radius:16px; padding:14px; margin-bottom:12px;">
                        <div style="font-size:16px; font-weight:600; color:#5c3b1e; margin-bottom:2px;">Sustainability Insights</div>
                        <div style="font-size:13px; color:#6d6d6d; margin-bottom:16px;">Your food waste & ingredient reuse patterns this month.</div>
                        <div style="display:flex; gap:10px; margin-bottom:16px;">
                            <div style="flex:1; background:#fdf6ee; border-radius:10px; padding:10px; text-align:center;">
                                <div style="font-size:22px; font-weight:700; color:#f1642e;">73%</div>
                                <div style="font-size:11px; color:#888;">Ingredients reused</div>
                            </div>
                            <div style="flex:1; background:#fdf6ee; border-radius:10px; padding:10px; text-align:center;">
                                <div style="font-size:22px; font-weight:700; color:#f1642e;">8</div>
                                <div style="font-size:11px; color:#888;">Leftovers used up</div>
                            </div>
                            <div style="flex:1; background:#fdf6ee; border-radius:10px; padding:10px; text-align:center;">
                                <div style="font-size:22px; font-weight:700; color:#f1642e;">1.2kg</div>
                                <div style="font-size:11px; color:#888;">Waste avoided</div>
                            </div>
                        </div>
                        <div style="font-size:13px; font-weight:600; color:#5c3b1e; margin-bottom:8px;">Leftover usage breakdown</div>
                        <div style="display:flex; flex-direction:column; gap:8px; margin-bottom:16px;">
                            <div>
                                <div style="display:flex;justify-content:space-between;font-size:12px;color:#5c3b1e;margin-bottom:3px;"><span>Used in next meal</span><span>45%</span></div>
                                <div style="background:#f0e8de;border-radius:999px;height:7px;"><div style="background:#f1642e;width:45%;height:7px;border-radius:999px;"></div></div>
                            </div>
                            <div>
                                <div style="display:flex;justify-content:space-between;font-size:12px;color:#5c3b1e;margin-bottom:3px;"><span>Repurposed</span><span>28%</span></div>
                                <div style="background:#f0e8de;border-radius:999px;height:7px;"><div style="background:#f1642e;width:28%;height:7px;border-radius:999px;"></div></div>
                            </div>
                            <div>
                                <div style="display:flex;justify-content:space-between;font-size:12px;color:#5c3b1e;margin-bottom:3px;"><span>Stored</span><span>18%</span></div>
                                <div style="background:#f0e8de;border-radius:999px;height:7px;"><div style="background:#f1642e;width:18%;height:7px;border-radius:999px;"></div></div>
                            </div>
                            <div>
                                <div style="display:flex;justify-content:space-between;font-size:12px;color:#5c3b1e;margin-bottom:3px;"><span>Wasted</span><span>9%</span></div>
                                <div style="background:#f0e8de;border-radius:999px;height:7px;"><div style="background:#f1642e;width:9%;height:7px;border-radius:999px;"></div></div>
                            </div>
                        </div>
                        <div style="font-size:13px; font-weight:600; color:#5c3b1e; margin-bottom:8px;">Top reused ingredients</div>
                        <div style="display:flex; flex-direction:column; gap:8px;">
                            <div>
                                <div style="display:flex;justify-content:space-between;font-size:12px;color:#5c3b1e;margin-bottom:3px;"><span>Rice</span><span>9x</span></div>
                                <div style="background:#f0e8de;border-radius:999px;height:7px;"><div style="background:#f1642e;width:90%;height:7px;border-radius:999px;"></div></div>
                            </div>
                            <div>
                                <div style="display:flex;justify-content:space-between;font-size:12px;color:#5c3b1e;margin-bottom:3px;"><span>Eggs</span><span>7x</span></div>
                                <div style="background:#f0e8de;border-radius:999px;height:7px;"><div style="background:#f1642e;width:70%;height:7px;border-radius:999px;"></div></div>
                            </div>
                            <div>
                                <div style="display:flex;justify-content:space-between;font-size:12px;color:#5c3b1e;margin-bottom:3px;"><span>Spinach</span><span>5x</span></div>
                                <div style="background:#f0e8de;border-radius:999px;height:7px;"><div style="background:#f1642e;width:50%;height:7px;border-radius:999px;"></div></div>
                            </div>
                            <div>
                                <div style="display:flex;justify-content:space-between;font-size:12px;color:#5c3b1e;margin-bottom:3px;"><span>Carrot</span><span>4x</span></div>
                                <div style="background:#f0e8de;border-radius:999px;height:7px;"><div style="background:#f1642e;width:40%;height:7px;border-radius:999px;"></div></div>
                            </div>
                        </div>
                    </div>
                </div>
                """)

if __name__ == "__main__":
    app.launch()
