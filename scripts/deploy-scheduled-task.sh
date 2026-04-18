#!/bin/bash

# Deploy and manage the weekly meal plan scheduled task
# Usage: ./scripts/deploy-scheduled-task.sh [status|update|docs]

TASK_ID="weekly-meal-plan-remote"
TASK_DIR="$HOME/.claude/scheduled-tasks/$TASK_ID"
TASK_SKILL="$TASK_DIR/SKILL.md"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_DOCS="$REPO_DIR/tasks/weekly-meal-plan.md"

echo "📋 Weekly Meal Plan Task Manager"
echo "================================"
echo "Task ID: $TASK_ID"
echo "Location: $TASK_DIR"
echo ""

case "${1:-status}" in
  status)
    echo "📍 Task Status:"
    if [ -f "$TASK_SKILL" ]; then
      echo "✅ Task exists at: $TASK_SKILL"
      echo ""
      echo "📅 Schedule: Every Monday 8:07 AM"
      echo "🤖 Model: Claude Haiku"
      echo "📧 From: diegoezce@gmail.com"
      echo "📊 Cost: ~\$0.007 per meal plan"
      echo ""
      echo "📖 Documentation: $TASK_DOCS"
      echo ""
      echo "🚀 To run manually:"
      echo "   Go to Claude Code → Scheduled → weekly-meal-plan-remote → Run now"
    else
      echo "❌ Task not found at: $TASK_SKILL"
      echo "   Create it in Claude Code Scheduled section first"
    fi
    ;;

  docs)
    echo "📖 Documentation:"
    if [ -f "$TASK_DOCS" ]; then
      cat "$TASK_DOCS"
    else
      echo "❌ Documentation not found: $TASK_DOCS"
    fi
    ;;

  update)
    echo "🔄 Updating task documentation..."
    echo "   Note: Scheduled task logic is in Claude Code, not in this script"
    echo "   To update the actual task:"
    echo "   1. Open Claude Code"
    echo "   2. Go to Scheduled → weekly-meal-plan-remote"
    echo "   3. Click Edit (or update the prompt)"
    echo "   4. Reference: $TASK_DOCS for current spec"
    ;;

  *)
    echo "❌ Unknown command: $1"
    echo ""
    echo "Usage: $0 [status|update|docs]"
    echo ""
    echo "Commands:"
    echo "  status  - Show task status and how to run"
    echo "  docs    - Show task documentation"
    echo "  update  - Instructions for updating the task"
    exit 1
    ;;
esac
