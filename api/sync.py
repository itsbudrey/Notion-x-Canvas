#!/usr/bin/env python3
"""
Vercel Serverless Function for Canvas to Notion Sync
Triggered by Notion button via webhook
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from icalendar import Calendar
from datetime import datetime
import re


# Canvas ICS Feed URL - will be set via environment variable
CANVAS_ICS_URL = os.environ.get('CANVAS_ICS_URL', '')

# Notion API Token - will be set via environment variable
NOTION_API_TOKEN = os.environ.get('NOTION_API_TOKEN', '')

# Notion Database ID for Tasks
TASKS_DATABASE_ID = os.environ.get('TASKS_DATABASE_ID', '23e399d3-5713-805c-9c0a-000be677710c')

# Course mapping - Canvas course codes to Notion project page IDs
COURSE_MAPPING = {
    "HIST 281": "25a399d357138029a22fc5319c5d711e",
    "CS 124": "25a399d357138052ab2be817336f99b7",
    "MATH 231": "25a399d3571380a9899bfd0aa5f4d4c6",
    "ENG 100": "25a399d3571380c1a736d06745eb29af",
    "ENG 111": "25a399d35713808ba76df0511179d181",
    "TE 200": "25a399d3571380c5bd2deff44048c237",
    "PHYS 100": "25a399d35713801ca04adabfb0e0e57e",
    "CS 199": "263399d3571380c5bd2deff44048c237",
    "CS 100": "25a399d357138026a3f0f9b3f05b5454",
    "CITL": None,
}


def extract_course_code(summary, location=""):
    """Extract course code from Canvas event summary or location"""
    # Try to extract from summary first
    match = re.search(r'\[([a-z]+)_(\d+)_[\d_]+\]', summary.lower())
    if match:
        subject = match.group(1).upper()
        number = match.group(2)
        return f"{subject} {number}"

    # Try to extract from location field
    if location:
        match = re.search(r'([a-z]+)_(\d+)(?:_|$)', location.lower())
        if match:
            subject = match.group(1).upper()
            number = match.group(2)
            return f"{subject} {number}"

    return None


def fetch_canvas_assignments():
    """Fetch and parse Canvas calendar"""
    response = requests.get(CANVAS_ICS_URL)
    response.raise_for_status()
    calendar = Calendar.from_ical(response.content)

    assignments = []
    now = datetime.now()

    for component in calendar.walk():
        if component.name == "VEVENT":
            summary = str(component.get('summary', ''))
            due_date = component.get('dtstart')
            description = str(component.get('description', ''))
            location = str(component.get('location', ''))
            uid = str(component.get('uid', ''))

            if not summary:
                continue

            # Extract course code
            course_code = extract_course_code(summary, location)

            # Clean up assignment name
            assignment_name = summary
            assignment_name = re.sub(r'\s*\[[a-z_\d]+\]\s*$', '', assignment_name, flags=re.IGNORECASE)
            assignment_name = re.sub(r'\s*\([^)]*\d{5,}[^)]*\)\s*', '', assignment_name)
            assignment_name = re.sub(r'^\[([A-Z]+\s*\d+[A-Z]*)\]\s*', '', assignment_name)
            assignment_name = assignment_name.strip()

            # Convert due date
            if due_date:
                if hasattr(due_date.dt, 'isoformat'):
                    due_date_str = due_date.dt.isoformat()
                    due_date_obj = due_date.dt
                else:
                    due_date_str = due_date.dt.strftime('%Y-%m-%d')
                    due_date_obj = due_date.dt
            else:
                continue  # Skip assignments without due dates

            # Only include future assignments
            if hasattr(due_date_obj, 'date'):
                assignment_date = due_date_obj.date()
            else:
                assignment_date = due_date_obj

            if assignment_date < now.date():
                continue

            # Extract Canvas URL
            canvas_url = None
            url_match = re.search(r'https://canvas\.illinois\.edu/[^\s<>"]+', description)
            if url_match:
                canvas_url = url_match.group(0)

            assignments.append({
                'name': assignment_name,
                'course_code': course_code,
                'due_date': due_date_str.split('T')[0] if 'T' in due_date_str else due_date_str,
                'canvas_url': canvas_url,
                'uid': uid
            })

    return assignments


def get_existing_tasks():
    """Query Notion database for existing tasks to avoid duplicates"""
    url = f"https://api.notion.com/v1/databases/{TASKS_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json={})
    if response.status_code == 200:
        results = response.json().get('results', [])
        existing_names = set()
        for page in results:
            title_prop = page.get('properties', {}).get('Name', {})
            if title_prop.get('title'):
                name = title_prop['title'][0].get('plain_text', '')
                existing_names.add(name.strip())
        return existing_names
    return set()


def create_notion_task(assignment, project_id):
    """Create a task in Notion database"""
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    properties = {
        "Name": {
            "title": [{"text": {"content": assignment['name']}}]
        },
        "Status": {
            "status": {"name": "Not started"}
        }
    }

    # Add project relation
    if project_id:
        properties["💡 Project"] = {
            "relation": [{"id": project_id}]
        }

    # Add due date
    if assignment['due_date']:
        properties["Due Date"] = {
            "date": {
                "start": assignment['due_date']
            }
        }

    # Create page content with Canvas link
    children = []
    if assignment['canvas_url']:
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": "View in Canvas",
                        "link": {"url": assignment['canvas_url']}
                    }
                }]
            }
        })

    data = {
        "parent": {"database_id": TASKS_DATABASE_ID},
        "properties": properties,
        "children": children
    }

    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 200


def sync_assignments():
    """Main sync function"""
    if not CANVAS_ICS_URL:
        return {"error": "CANVAS_ICS_URL not configured"}, 500

    if not NOTION_API_TOKEN:
        return {"error": "NOTION_API_TOKEN not configured"}, 500

    try:
        # Fetch assignments from Canvas
        assignments = fetch_canvas_assignments()

        # Get existing tasks to avoid duplicates
        existing_tasks = get_existing_tasks()

        # Filter and create tasks
        created = 0
        skipped = 0
        errors = []

        for assignment in assignments:
            # Skip if already exists
            if assignment['name'] in existing_tasks:
                skipped += 1
                continue

            # Skip if no course mapping
            course_code = assignment['course_code']
            if not course_code or course_code not in COURSE_MAPPING:
                skipped += 1
                continue

            project_id = COURSE_MAPPING[course_code]
            if not project_id:
                skipped += 1
                continue

            # Create task
            success = create_notion_task(assignment, project_id)
            if success:
                created += 1
            else:
                errors.append(assignment['name'])

        return {
            "success": True,
            "total_assignments": len(assignments),
            "created": created,
            "skipped": skipped,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""

    def do_GET(self):
        """Handle GET requests"""
        result, status_code = sync_assignments()

        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        self.wfile.write(json.dumps(result, indent=2).encode())
        return

    def do_POST(self):
        """Handle POST requests (from Notion automation)"""
        result, status_code = sync_assignments()

        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        self.wfile.write(json.dumps(result, indent=2).encode())
        return
