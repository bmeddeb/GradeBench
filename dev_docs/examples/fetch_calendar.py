#!/usr/bin/env python3
import os
import httpx
import json
from dotenv import load_dotenv
from datetime import date

def main():
    load_dotenv()
    api_url   = os.getenv('CANVAS_API_URL')
    api_key   = os.getenv('CANVAS_API_TOKEN')
    course_id = os.getenv('CANVAS_COURSE_ID')

    if not (api_url and api_key and course_id):
        raise RuntimeError(
            "Make sure CANVAS_API_URL, CANVAS_API_TOKEN & CANVAS_COURSE_ID are set in your .env"
        )

    headers = {'Authorization': f'Bearer {api_key}'}
    client  = httpx.Client()

    # ---- adjust these to whatever window you need ----
    start = date(2025, 5, 1).isoformat()
    end   = date(2025, 5, 31).isoformat()

    params = {
        'context_codes[]': f'course_{course_id}',
        'type[]':          ['event','assignment'],  # both manual events and assignment due-dates
        'all_events':      'true',                  # include everything
        'start_date':      start,
        'end_date':        end,
        'per_page':        100
    }

    resp = client.get(
        f"{api_url}/api/v1/calendar_events",
        headers=headers,
        params=params
    )
    resp.raise_for_status()

    events = resp.json()
    print(json.dumps(events, indent=2) or "[] (none)")

    client.close()

if __name__ == "__main__":
    main()
