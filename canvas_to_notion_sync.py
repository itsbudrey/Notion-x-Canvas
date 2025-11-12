#!/usr/bin/env python3
"""
Canvas to Notion Assignment Sync
Syncs assignments from Canvas ICS calendar to Notion Tasks database
"""

import requests
from icalendar import Calendar
from datetime import datetime
import json
import re

# Canvas ICS Feed URL
CANVAS_ICS_URL = "https://canvas.illinois.edu/feeds/calendars/user_XW4gRxHVVylnq1i5ro4T8rrecKOSXDZLip72fOf5.ics"

# Notion Project IDs - mapping Canvas course names to Notion project pages
COURSE_MAPPING = {
    "HIST 281": "https://www.notion.so/25a399d357138029a22fc5319c5d711e",
    "CS 124": "https://www.notion.so/25a399d357138052ab2be817336f99b7",
    "MATH 231": "https://www.notion.so/25a399d3571380a9899bfd0aa5f4d4c6",
    "ENG 100": "https://www.notion.so/25a399d3571380c1a736d06745eb29af",
    "ENG 111": "https://www.notion.so/25a399d35713808ba76df0511179d181",
    "TE 200": "https://www.notion.so/25a399d3571380c5bd2deff44048c237",
    "PHYS 100": "https://www.notion.so/25a399d35713801ca04adabfb0e0e57e",
    "CS 199": "https://www.notion.so/263399d3571380c5bd2deff44048c237",
    "CS 100": "https://www.notion.so/25a399d357138026a3f0f9b3f05b5454",
    "CITL": None,  # Skip CITL courses (not a class)
}

# Data source ID for the Tasks database
TASKS_DATA_SOURCE_ID = "23e399d3-5713-805c-9c0a-000be677710c"


def fetch_canvas_calendar():
    """Fetch the Canvas calendar ICS file"""
    print("Fetching Canvas calendar...")
    response = requests.get(CANVAS_ICS_URL)
    response.raise_for_status()
    return Calendar.from_ical(response.content)


def extract_course_code(summary, location=""):
    """
    Extract course code from Canvas event summary or location
    Canvas formats:
    - Summary: "Assignment Name [course_code_semester_id]"
    - Location: "course_code_semester_id" (e.g., "math_231_120258_248828")
    """
    # Try to extract from summary first - Canvas context code in brackets
    # Pattern: [subject_number_semester_id] at the end
    match = re.search(r'\[([a-z]+)_(\d+)_[\d_]+\]', summary.lower())
    if match:
        subject = match.group(1).upper()
        number = match.group(2)
        course_code = f"{subject} {number}"
        return course_code

    # Try to extract from location field (Canvas course context_code)
    if location:
        # Pattern: subject_number_other_ids (e.g., "math_231_120258_248828")
        match = re.search(r'([a-z]+)_(\d+)(?:_|$)', location.lower())
        if match:
            subject = match.group(1).upper()
            number = match.group(2)
            course_code = f"{subject} {number}"
            return course_code

    # Try to extract from summary - patterns like "[HIST 281]" or "(HIST 281)"
    match = re.search(r'[\[\(]([A-Z]+\s*\d+[A-Z]*)[\]\)]', summary)
    if match:
        return match.group(1)

    # Try course name in parentheses
    match = re.search(r'\(([A-Z]+\s+\d+[A-Z]*.*?)\)', summary)
    if match:
        course_name = match.group(1)
        # Extract just the course code part
        code_match = re.search(r'([A-Z]+\s+\d+)', course_name)
        if code_match:
            return code_match.group(1)

    # Try alternative patterns
    match = re.search(r'^([A-Z]+\s*\d+[A-Z]*)\s*[:-]', summary)
    if match:
        return match.group(1)

    return None


def parse_assignments(calendar):
    """Parse assignments from calendar events"""
    assignments = []

    for component in calendar.walk():
        if component.name == "VEVENT":
            summary = str(component.get('summary', ''))
            due_date = component.get('dtstart')
            description = str(component.get('description', ''))
            location = str(component.get('location', ''))
            uid = str(component.get('uid', ''))

            # Skip non-assignment events (like lectures, office hours, etc.)
            # Canvas usually marks assignments differently
            if not summary:
                continue

            # Extract course code from location (Canvas context_code) or summary
            course_code = extract_course_code(summary, location)

            # Clean up assignment name (remove course code brackets and course name)
            assignment_name = summary
            # Remove Canvas context code at the end like [math_231_120258_248828]
            assignment_name = re.sub(r'\s*\[[a-z_\d]+\]\s*$', '', assignment_name, flags=re.IGNORECASE)
            # Remove course name in parentheses if followed by course code
            assignment_name = re.sub(r'\s*\([^)]*\d{5,}[^)]*\)\s*', '', assignment_name)
            # Remove prefix patterns like "[COURSE] Assignment"
            assignment_name = re.sub(r'^\[([A-Z]+\s*\d+[A-Z]*)\]\s*', '', assignment_name)
            # Remove prefix patterns like "COURSE: Assignment"
            assignment_name = re.sub(r'^([A-Z]+\s*\d+[A-Z]*)\s*[:-]\s*', '', assignment_name)
            assignment_name = assignment_name.strip()

            # Convert due date to ISO format
            if due_date:
                if hasattr(due_date.dt, 'isoformat'):
                    due_date_str = due_date.dt.isoformat()
                    # Check if it's a datetime or just a date
                    is_datetime = 'T' in due_date_str
                else:
                    due_date_str = due_date.dt.strftime('%Y-%m-%d')
                    is_datetime = False
            else:
                due_date_str = None
                is_datetime = False

            # Try to extract Canvas URL from description
            canvas_url = None
            url_match = re.search(r'https://canvas\.illinois\.edu/[^\s<>"]+', description)
            if url_match:
                canvas_url = url_match.group(0)

            assignments.append({
                'name': assignment_name,
                'course_code': course_code,
                'due_date': due_date_str,
                'is_datetime': is_datetime,
                'canvas_url': canvas_url,
                'uid': uid,
                'raw_summary': summary
            })

    return assignments


def find_notion_project_url(course_code):
    """Find the Notion project URL for a given course code"""
    if not course_code:
        return None

    # Exact match
    if course_code in COURSE_MAPPING:
        return COURSE_MAPPING[course_code]

    # Try partial match (e.g., "CS124" -> "CS 124")
    for key in COURSE_MAPPING:
        if key.replace(' ', '') == course_code.replace(' ', ''):
            return COURSE_MAPPING[key]

    return None


def sync_to_notion(assignments):
    """
    Sync assignments to Notion
    This function will output JSON that can be used with Claude Code's Notion MCP
    """

    print(f"\nFound {len(assignments)} events in Canvas calendar")
    print("\n" + "="*80)
    print("ASSIGNMENTS TO SYNC")
    print("="*80)

    tasks_to_create = []
    skipped = []

    for assignment in assignments:
        course_code = assignment['course_code']
        notion_project_url = find_notion_project_url(course_code)

        if not notion_project_url:
            skipped.append({
                'assignment': assignment['name'],
                'course': course_code or 'Unknown',
                'reason': 'No matching Notion project found'
            })
            continue

        # Prepare task data for Notion
        task_data = {
            'assignment_name': assignment['name'],
            'course_code': course_code,
            'due_date': assignment['due_date'],
            'is_datetime': assignment['is_datetime'],
            'notion_project_url': notion_project_url,
            'canvas_url': assignment['canvas_url']
        }

        tasks_to_create.append(task_data)

        # Display info
        print(f"\n✓ {assignment['name']}")
        print(f"  Course: {course_code}")
        print(f"  Due: {assignment['due_date'] if assignment['due_date'] else 'No due date'}")
        if assignment['canvas_url']:
            print(f"  URL: {assignment['canvas_url']}")

    print("\n" + "="*80)
    print(f"Tasks to create: {len(tasks_to_create)}")
    print(f"Skipped: {len(skipped)}")
    print("="*80)

    if skipped:
        print("\nSKIPPED ITEMS:")
        for item in skipped:
            print(f"  - {item['assignment']} ({item['course']}): {item['reason']}")

    # Save to JSON file for review
    with open('/Users/budrey/canvas_sync_data.json', 'w') as f:
        json.dump({
            'tasks_to_create': tasks_to_create,
            'skipped': skipped,
            'sync_date': datetime.now().isoformat()
        }, f, indent=2)

    print(f"\nSync data saved to: /Users/budrey/canvas_sync_data.json")

    return tasks_to_create


def main():
    """Main function"""
    try:
        # Fetch and parse calendar
        calendar = fetch_canvas_calendar()
        assignments = parse_assignments(calendar)

        # Sync to Notion
        tasks_to_create = sync_to_notion(assignments)

        print(f"\n✓ Found {len(tasks_to_create)} assignments ready to sync")
        print("\nNext steps:")
        print("1. Review canvas_sync_data.json to see what will be synced")
        print("2. Run the sync with Claude Code to create tasks in Notion")

    except Exception as error:
        print(f"\n✗ Error: {error}")
        raise


if __name__ == "__main__":
    main()
