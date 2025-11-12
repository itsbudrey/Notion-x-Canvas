#!/usr/bin/env python3
"""
Sync Canvas assignments to Notion
Reads canvas_sync_data.json and creates tasks in Notion via Claude Code
"""

import json
import sys


def load_sync_data():
    """Load the Canvas sync data"""
    try:
        with open('/Users/budrey/canvas_sync_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: canvas_sync_data.json not found. Run canvas_to_notion_sync.py first.")
        sys.exit(1)


def generate_notion_task_data(task):
    """
    Generate Notion task data for a Canvas assignment
    Returns a dict that can be used with Notion MCP create-pages tool
    """
    assignment_name = task['assignment_name']
    course_code = task['course_code']
    due_date = task['due_date']
    is_datetime = task['is_datetime']
    notion_project_url = task['notion_project_url']
    canvas_url = task['canvas_url']

    # Build the task properties
    properties = {
        "Name": assignment_name,
        "Status": "Not started",
        "💡 Project": [notion_project_url]
    }

    # Add due date if present
    if due_date:
        # For Canvas assignments, we want them to show as all-day tasks
        # So we convert datetime to date-only
        if is_datetime and 'T' in due_date:
            # Extract just the date part
            date_only = due_date.split('T')[0]
            properties["date:Due Date:start"] = date_only
            properties["date:Due Date:is_datetime"] = 0
        else:
            properties["date:Due Date:start"] = due_date
            properties["date:Due Date:is_datetime"] = 0

    # Build content with Canvas link if available
    content = ""
    if canvas_url:
        content = f"[View in Canvas]({canvas_url})"

    return {
        "properties": properties,
        "content": content
    }


def print_summary(sync_data):
    """Print a summary of what will be synced"""
    tasks_to_create = sync_data['tasks_to_create']

    print("="*80)
    print("CANVAS TO NOTION SYNC SUMMARY")
    print("="*80)
    print(f"\nTotal assignments to sync: {len(tasks_to_create)}")

    # Group by course
    by_course = {}
    for task in tasks_to_create:
        course = task['course_code']
        if course not in by_course:
            by_course[course] = []
        by_course[course].append(task['assignment_name'])

    print("\nBreakdown by course:")
    for course, assignments in sorted(by_course.items()):
        print(f"\n  {course} ({len(assignments)} assignments):")
        for assignment in assignments[:5]:  # Show first 5
            print(f"    - {assignment}")
        if len(assignments) > 5:
            print(f"    ... and {len(assignments) - 5} more")

    print("\n" + "="*80)


def main():
    """Main function"""
    # Load sync data
    sync_data = load_sync_data()

    # Print summary
    print_summary(sync_data)

    # Generate Notion task data for each assignment
    tasks_to_create = sync_data['tasks_to_create']

    print("\n" + "="*80)
    print("NOTION TASK DATA (for Claude Code)")
    print("="*80)
    print("\nThe following JSON contains all tasks to be created in Notion.")
    print("Copy this and use it with Claude Code's Notion MCP.\n")

    # Generate all task data
    notion_tasks = []
    for task in tasks_to_create:
        notion_task = generate_notion_task_data(task)
        notion_tasks.append(notion_task)

    # Output as JSON
    output = {
        "parent": {
            "type": "data_source_id",
            "data_source_id": "23e399d3-5713-805c-9c0a-000be677710c"
        },
        "pages": notion_tasks
    }

    print(json.dumps(output, indent=2))

    print("\n" + "="*80)
    print(f"\n✓ Generated {len(notion_tasks)} tasks ready for Notion")
    print("\nTo sync these to Notion:")
    print("1. The JSON data above is ready to use with Notion MCP create-pages")
    print("2. Claude Code will use this to create all tasks in your Notion database")
    print("3. Duplicate prevention: Tasks will only be created if they don't exist")


if __name__ == "__main__":
    main()
