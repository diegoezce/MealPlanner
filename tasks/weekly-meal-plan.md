# Weekly Meal Plan Task

**Task ID**: `weekly-meal-plan-remote`  
**Schedule**: Every Monday 8:07 AM (cron: `0 8 * * 1`)  
**Model**: Claude Haiku  
**Cost**: ~$0.007 per plan  

## Objective

Process meal plan requests from Google Sheet, generate personalized 7-day LatAm meal plans with varied recipes, send beautifully formatted HTML emails, and mark rows as "Done" in the sheet.

## Source Sheet

https://docs.google.com/spreadsheets/d/1O6DC-6u5Y642c1v8LkwSYkj9lBGDy_szSLnM0PfucFM/edit

## Recipe Generation (Personalized, No Fixed Bank)

Recipes are **generated dynamically** by Claude for each family based on:

**Dietary Adaptations:**
- **Celíaco / Gluten-free**: Automatically uses GF alternatives (rice, corn, quinoa bases instead of wheat)
- **Diabético**: Low GI foods, controlled carbs, no refined sugars
- **Vegetariano/Vegana**: Adapts proteins (eggs, cheese, legumes, nuts, tofu)
- **Alergias específicas**: Avoids mentioned allergens
- **Saludable/Liviana**: Grilled, baked, steamed (no fried foods)
- **Casera clásica**: Comfort-food style, familiar flavors

**Generation Quality:**
- LatAm style (Argentina, Mexico, Colombia, Peru)
- Infinite variety (no static recipe rotation)
- Never repeats from previous week
- Reuses ingredients to minimize shopping list
- Adapts portion sizes for family
- Respects cooking time constraints
- Picky-eater friendly when needed

## Workflow

1. **Read Google Sheet** → identify rows with empty Status
2. **Extract parameters**: family_size, ages, restrictions, picky_eaters, cooking_time, preferences, contact_email
3. **Check "Last Recipes" column** to avoid repeating last week's meals
4. **Generate meal plan** with Claude Haiku:
   - Reads all family constraints (dietary, health, time, preferences)
   - Generates 21 ORIGINAL recipes (7 days × 3 meals)
   - Respects dietary needs: gluten-free, low GI, vegetarian, allergies
   - Prioritizes health preferences: healthy, light, home-style
   - Reuses ingredients strategically
   - Never repeats last week's meals
5. **Send HTML email** from Mailjet (info@goplanify.com) with:
   - Personalized greeting with family size/ages
   - Styled 7-day meal table
   - Smart shopping list (categorized)
   - Meal prep tips
   - Nutritional insights (prep time, picky-friendly count, ingredient reuse, health options)
6. **Update sheet**:
   - Write "Done" in Status
   - Write all 21 meal names in "Last Recipes" (comma-separated)
   - Write "Error: [reason]" if failed

## Email Template

Subject: "🍽️ Tu plan de comidas semanal"  
From: diegoezce@gmail.com  
To: Contact from survey  

HTML format with:
- Green (#2d6a4f) header banner
- Professional styling (fonts, colors, spacing)
- Responsive table for meals
- Grid layout for shopping list
- Clean footer

## Monitoring

- Check inbox (info@goplanify.com via Mailjet) for sent emails
- Review Google Sheet Status column for "Done" or "Error"
- Check "Last Recipes" column to verify:
  - Recipes are different from previous week
  - Restrictions are respected (no gluten if celiac, etc)
  - Diversity of recipes (not repetitive)
- Verify insights reflect actual plan (picky-friendly count, prep time, health options)
- Use Claude Code notifications for task completion

## Updating the Task

To modify prompt or schedule:
1. Run `./scripts/deploy-scheduled-task.sh update`
2. Or manually edit in Claude Code → Scheduled → weekly-meal-plan-remote

Location: `~/.claude/scheduled-tasks/weekly-meal-plan-remote/SKILL.md`
