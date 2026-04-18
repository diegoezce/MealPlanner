# Weekly Meal Plan Task

**Task ID**: `weekly-meal-plan-remote`  
**Schedule**: Every Monday 8:07 AM (cron: `0 8 * * 1`)  
**Model**: Claude Haiku  
**Cost**: ~$0.007 per plan  

## Objective

Process meal plan requests from Google Sheet, generate personalized 7-day LatAm meal plans with varied recipes, send beautifully formatted HTML emails, and mark rows as "Done" in the sheet.

## Source Sheet

https://docs.google.com/spreadsheets/d/1O6DC-6u5Y642c1v8LkwSYkj9lBGDy_szSLnM0PfucFM/edit

## Recipe Bank (Rotates Weekly)

**Breakfasts** (rotate):
- Tostadas con manteca y mermelada + leche con cacao
- Tostadas con queso cremoso + jugo de naranja
- Cereales con leche + banana
- Medialunas caseras + té con leche
- Huevos revueltos + pan + manteca
- Pancakes caseros + mermelada + jugo
- Omelette con queso + tostadas

**Lunches/Viandas** (rotate to avoid repeat in 4 weeks):
- Fideos con salsa de tomate y queso
- Arroz blanco + milanesa + ensalada
- Fideos fritos con aceite, ajo, orégano
- Arroz con pollo
- Pastas al horno con queso y jamón
- Lentejas con verduras + arroz
- Choclo con queso fundido
- Cazuela de verduras con carne picada
- Tallarín con salsa bolognesa

**Dinners** (simple & quick, <30 min):
- Milanesas de ternera + puré + ensalada
- Milanesas de pollo + papas bastón + ensalada
- Empanadas de carne al horno + ensalada
- Fideos con salsa blanca
- Polenta con salsa de carne
- Omelette de queso + pan tostado
- Hamburguesas caseras + papas
- Picadillo con puré
- Pollo guisado + verduras
- Choclo con manteca + ensalada
- Tartas de verdura (acelga, espinaca, cebolla)

## Workflow

1. **Read Google Sheet** → identify rows with empty Status
2. **Extract parameters**: family_size, ages, restrictions, picky_eaters, cooking_time, preferences, contact_email
3. **Check "Last Recipes" column** for previous week's meals
4. **Generate meal plan**:
   - Use different recipes than "Last Recipes"
   - Adapt to picky eaters (simple, mild)
   - Reuse ingredients
   - Keep <20 min if low cooking time
5. **Send HTML email** from diegoezce@gmail.com with:
   - Green header with personalization
   - Styled 7-day meal table
   - Shopping list by category (2-column grid)
   - Meal prep tips
   - Insights summary
6. **Update sheet**:
   - Write "Done" in Status
   - Write meal names in "Last Recipes" (comma-separated)
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

- Check diegoezce@gmail.com inbox for sent emails
- Review Google Sheet Status column for "Done" or "Error"
- Check "Last Recipes" column to verify recipes rotated
- Use Claude Code notifications for task completion

## Updating the Task

To modify prompt or schedule:
1. Run `./scripts/deploy-scheduled-task.sh update`
2. Or manually edit in Claude Code → Scheduled → weekly-meal-plan-remote

Location: `~/.claude/scheduled-tasks/weekly-meal-plan-remote/SKILL.md`
