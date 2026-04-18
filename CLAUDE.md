# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MealPlanner automates weekly meal planning:
1. Reads survey responses from Google Sheet
2. Generates personalized 7-day LatAm meal plans with Claude Haiku
3. Sends formatted HTML email with full plan details
4. Updates sheet status

**Remote task** runs every Monday at 8:07 AM.

## Architecture

```
Google Sheet (survey)
    ↓
Claude Haiku (generation)
    ↓
Gmail (send HTML email)
    ↓
Google Sheet (status: Done/Error)
```

## Configuration

**Scheduled Task**: `weekly-meal-plan-remote`
- Schedule: `0 8 * * 1` (Mondays 8 AM)
- Model: Claude Haiku (cost: ~$0.007/plan)
- Auth: diegoezce@gmail.com (Gmail), Google Sheets

**Survey Sheet**: https://docs.google.com/spreadsheets/d/1O6DC-6u5Y642c1v8LkwSYkj9lBGDy_szSLnM0PfucFM/edit

## Common Tasks

**Run manually**: Scheduled → weekly-meal-plan-remote → "Run now"

**Regenerate for one row**: Clear Status column → Run task

**Modify prompt**: Edit task in Scheduled section

## Generation Rules

- LatAm recipes (Argentina, Mexico, Colombia, Peru)
- Adapt to: picky eaters, cooking time, food preferences
- Reuse ingredients across 7 days
- Output: HTML email (no attachments)

## Email Format

- From: diegoezce@gmail.com
- To: Contact from survey row
- Subject: "🍽️ Tu plan de comidas semanal - [ID]"
- Body: HTML table with meal plan, shopping list (by category), tips, insights

## Integration Points

- **Google Sheets**: Read survey params, write Status
- **Gmail**: Send HTML email to contact
- **Claude API**: Generate meal plan JSON

## Future

- WhatsApp delivery
- Frontend (currently Google Forms)
- Historical tracking
- Grocery delivery integration
