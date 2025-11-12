# Canvas to Notion Assignment Sync

Automatically sync your Canvas assignments to your Notion Tasks database!

## Setup Complete!

The automation is now set up and ready to use. Here's what's been created:

### Files Created

1. **canvas_to_notion_sync.py** - Fetches assignments from your Canvas calendar
2. **sync_to_notion.py** - Helper script to format data for Notion
3. **canvas_sync_data.json** - Cached Canvas data (auto-generated)
4. **requirements.txt** - Python dependencies

## How It Works

The system pulls assignments from your Canvas ICS calendar feed and automatically:
- Extracts course codes (MATH 231, HIST 281, CS 124, etc.)
- Matches them to your Notion Projects
- Converts Canvas due dates to Notion date format (all-day tasks)
- Formats assignment names properly

## Quick Start

### Option 1: Sync All Upcoming Assignments (Recommended)

Run this command in your terminal:

```bash
cd ~
python3 canvas_to_notion_sync.py
```

This will show you all assignments that will be synced. Then ask Claude Code to sync the remaining upcoming assignments.

### Option 2: Manual Sync via Claude Code

1. Run the Canvas fetch script:
   ```bash
   python3 canvas_to_notion_sync.py
   ```

2. Tell Claude Code:
   "Sync all assignments from canvas_sync_data.json that are due after today to my Notion Tasks database"

3. Claude will use the Notion MCP to create all the tasks

## What Gets Synced

- **Assignment Name**: Cleaned up (removes Canvas IDs and course codes)
- **Due Date**: Converted to all-day format (no time shown)
- **Status**: Set to "Not started"
- **Project**: Automatically linked to the correct class folder

## Currently Mapped Courses

- HIST 281
- CS 124
- MATH 231
- ENG 100
- ENG 111
- TE 200
- PHYS 100
- CS 199
- CS 100

## Adding New Courses

If you add a new class, edit `canvas_to_notion_sync.py` and add it to the `COURSE_MAPPING` dictionary:

```python
COURSE_MAPPING = {
    "NEW COURSE 123": "https://www.notion.so/YOUR-NOTION-PAGE-ID",
    # ... existing courses
}
```

## Duplicate Prevention

The system won't prevent duplicates automatically yet. To avoid duplicates:

1. Only sync assignments that are **upcoming** (not already in Notion)
2. Check your Notion Tasks database before running a full sync
3. Consider filtering by date when syncing

## Automation Schedule

To run this automatically every day:

### On Mac (using cron):

1. Open terminal and run:
   ```bash
   crontab -e
   ```

2. Add this line (runs daily at 8 AM):
   ```
   0 8 * * * cd /Users/budrey && /usr/bin/python3 canvas_to_notion_sync.py
   ```

### Manual Refresh

Just run the script whenever you want to check for new assignments:
```bash
python3 ~/canvas_to_notion_sync.py
```

## Troubleshooting

**No assignments found:**
- Check that your Canvas ICS feed URL is still valid
- Make sure you're enrolled in courses

**Course not matching:**
- Check the `COURSE_MAPPING` in `canvas_to_notion_sync.py`
- Canvas uses format like "math_231_120258_248828"
- Script converts this to "MATH 231" automatically

**Tasks not showing in Notion:**
- Make sure the task is linked to a Project
- Check that the due date is properly formatted

## Next Steps

1. Check your Notion Tasks database - you should see 7 new assignments I just created!
2. Run `python3 canvas_to_notion_sync.py` to see all available assignments
3. Ask Claude Code to sync any remaining assignments you want

Enjoy automated Canvas → Notion syncing!
