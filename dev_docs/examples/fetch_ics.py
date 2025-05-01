#!/usr/bin/env python3
import os
import httpx
from dotenv import load_dotenv

def main():
    load_dotenv()
    API_URL   = os.getenv('CANVAS_API_URL')
    API_KEY   = os.getenv('CANVAS_API_TOKEN')
    COURSE_ID = os.getenv('CANVAS_COURSE_ID')

    if not (API_URL and API_KEY and COURSE_ID):
        raise RuntimeError("Make sure CANVAS_API_URL, CANVAS_API_TOKEN, and CANVAS_COURSE_ID are in your .env")

    headers = {'Authorization': f'Bearer {API_KEY}'}
    client  = httpx.Client()

    # 1) Fetch course JSON to get the ICS URL
    resp_course = client.get(f"{API_URL}/api/v1/courses/{COURSE_ID}", headers=headers)
    resp_course.raise_for_status()
    course = resp_course.json()
    ics_url = course.get('calendar', {}).get('ics')
    if not ics_url:
        print("No ICS feed URL found in course JSON.")
        return

    # 2) Download the ICS feed
    print(f"Fetching ICS from: {ics_url}\n")
    resp_ics = client.get(ics_url, headers=headers)
    resp_ics.raise_for_status()
    ics_text = resp_ics.text

    # 3) Print the raw ICS
    print(ics_text)

if __name__ == "__main__":
    main()
