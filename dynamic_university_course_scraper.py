import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

# ==================================================
# GLOBAL SETTINGS (DO NOT CHANGE OFTEN)
# ==================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

REQUEST_DELAY = 2


# ==================================================
# HELPER FUNCTIONS (REUSABLE)
# ==================================================

def fetch_page(url):
    """Download HTML of a page"""
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.text


def clean_text(element):
    return element.get_text(strip=True) if element else "Not found"


# ==================================================
# 🔑 UNIVERSITY CONFIGURATION SECTION
# THIS IS WHERE YOU CHANGE CODE FOR EACH UNIVERSITY
# ==================================================

UNIVERSITY_CONFIG = {
    "course_name": {
        "tag": "h1",
        "class": None
    },
    "degree_type": {
        "tag": "span",
        "class": "degree-award"
    },
    "duration": {
        "tag": "div",
        "class": "course-duration"
    },
    "fees": {
        "tag": "div",
        "class": "course-fees"
    },
    "start_date": {
        "tag": "div",
        "class": "course-start"
    }
}

"""
📌 WHEN YOU CHANGE UNIVERSITY:
--------------------------------
You ONLY update UNIVERSITY_CONFIG

Example:
- Change class names
- Change tag names
- Add/remove fields
"""


# ==================================================
# CORE SCRAPER LOGIC (DO NOT CHANGE)
# ==================================================

def scrape_course(url):
    html = fetch_page(url)
    soup = BeautifulSoup(html, "lxml")

    data = {
        "Course URL": url
    }

    for field, selector in UNIVERSITY_CONFIG.items():
        element = soup.find(selector["tag"], class_=selector["class"])
        data[field.replace("_", " ").title()] = clean_text(element)

    return data


def scrape_multiple_courses(urls):
    all_courses = []

    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{len(urls)}] Scraping: {url}")

        try:
            course_data = scrape_course(url)
            all_courses.append(course_data)
            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"❌ Failed: {e}")

    return pd.DataFrame(all_courses)


# ==================================================
# RUN SCRIPT
# ==================================================

if __name__ == "__main__":

    print("Paste course URLs (one per line).")
    print("Press ENTER twice to start:\n")

    urls = []
    while True:
        line = input()
        if not line.strip():
            break
        urls.append(line.strip())

    if not urls:
        print("❌ No URLs provided.")
        exit()

    df = scrape_multiple_courses(urls)
    df.to_excel("scraped_courses.xlsx", index=False)

    print("\n✅ Scraping completed.")
    print("📁 Output file: scraped_courses.xlsx")
