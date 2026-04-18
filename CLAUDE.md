# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MealPlanner is an automation system that:
1. Reads meal plan survey responses from a Google Sheet
2. Generates personalized 7-day LatAm meal plans using Claude API
3. Sends meal plans via email to survey respondents
4. Tracks processing status in the source sheet

The system runs as a scheduled remote agent on Anthropic's servers every Monday at 8:07 AM.

## Architecture

### Data Flow
```
Google Sheet (survey responses)
    ↓
Claude API (meal plan generation)
    ↓
Gmail API (email delivery)
    ↓
Google Sheet (status update)
```

### Key Components

**Survey Input Sheet**
- URL: https://docs.google.com/spreadsheets/d/1O6DC-6u5Y642c1v8LkwSYkj9lBGDy_szSLnM0PfucFM/edit
- Collects: family size, ages, dietary restrictions, picky eater details, cooking time, food preferences
- Expected columns: Submission ID, Respondent ID, Submitted at, Family size, Ages, Restrictions, Picky eaters, Cooking time, Preferences

**Meal Plan Generation**
- Uses Claude Haiku (cost-optimized)
- Generates JSON with: 7-day meal plan, categorized shopping list, meal prep tips, insights
- Constraints: LatAm recipes, respects picky eater preferences, adapts to cooking time availability, reuses ingredients

**Email Delivery**
- From: mealplannerbot@gmail.com
- To: Contact email from survey row
- Attachment: JSON meal plan file
- Subject: "🍽️ Tu plan de comidas semanal - [Submission ID]"

**Status Tracking**
- Sheet Status column: "Done" or "Error: [reason]"
- Allows manual regeneration by clearing Status and running task

### Configuration

**Scheduled Task ID**: `weekly-meal-plan-remote`
- Cron: `0 8 * * 1` (every Monday 8 AM local time)
- Model: Claude Haiku (for cost efficiency)
- Authentication: Requires Gmail (mealplannerbot@gmail.com) and Google Sheets access

## Development

### Common Tasks

**Generate a meal plan manually**
- Navigate to "Scheduled" section in Claude Code
- Find "weekly-meal-plan-remote"
- Click "Run now"

**Regenerate plan for a specific survey response**
- Find the row in the Google Sheet
- Clear the "Status" column
- Run the scheduled task (or run manually)

**Modify generation parameters**
- Edit the task prompt in Claude Code Scheduled section
- Or update the remote agent via Claude API

### Testing & Validation

**Before deploying changes:**
1. Test with a sample survey row manually
2. Verify email delivery to mealplannerbot@gmail.com inbox
3. Confirm JSON structure and attachment generation
4. Check Google Sheet status update

**Monitoring**
- Check mealplannerbot@gmail.com inbox for sent emails
- Review Google Sheet Status column for errors
- Use Claude Code notifications (task completion alerts)

## Integration Points

### Google Sheets MCP
- Read survey responses (columns: family_size, ages, restrictions, picky_eaters, cooking_time, preferences, contact_email)
- Write status updates (Status, Generated, Avg Time columns)
- Create "Status" column if missing

### Gmail MCP
- Authenticate as mealplannerbot@gmail.com
- Send email with JSON attachment
- Handle auth failures gracefully

### Claude API
- Model: claude-haiku-4-5-20251001
- Prompt: Generates JSON meal plan based on survey parameters
- Cost: ~$0.007 per plan

## Future Enhancements

- [ ] WhatsApp delivery option (currently email only)
- [ ] Frontend for survey submission (currently Google Forms)
- [ ] Database persistence for historical plans
- [ ] Meal preference learning (track user feedback)
- [ ] Integration with grocery delivery APIs
- [ ] Multi-language support

## Constraints & Assumptions

- LatAm recipes only (Argentina, Mexico, Colombia, Peru focus)
- Families 2-10 people (based on typical survey range)
- Email delivery (WhatsApp coming later)
- Cooking time: <20 min, 20-40 min, or >40 min options
- Meal plan generated fresh weekly (no historical tracking yet)
