import os
import re
import pdfplumber
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(__file__)
BULLETIN_DIR = os.path.join(BASE_DIR, "bulletins")

song_pattern = re.compile(
    r"""
    (?:\*?Song|Doxology):\s*
    (\d{1,3}[A-Za-z]?)
    (?::\s*([\d,-]+))?
    :?\s*(.*)
    """,
    re.VERBOSE
)

date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
text_pattern = re.compile(r'Text:\s*(.+)')
offering_pattern = re.compile(r"Offerings:\s*1\.\s*(.+)")  # matches first line only
offering_line2_pattern = re.compile(r"2\.\s*(.+)")
title_pattern = re.compile(r'Title:\s*(.+)')


def parse_date(file_name: str):
    match = re.search(r"(\d{4}-\d{2}-\d{2})", file_name)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y-%m-%d").date()


def get_closest_bulletin(folder_path: str, target_date):
    """Return the file path of the PDF with the date closest to target_date"""
    closest_file = None
    min_diff = None

    for file_name in os.listdir(folder_path):
        if not file_name.lower().endswith(".pdf"):
            continue

        file_date = parse_date(file_name)
        if not file_date:
            continue

        diff = abs((file_date - target_date).days)
        if (min_diff is None) or (diff < min_diff):
            min_diff = diff
            closest_file = file_name

    if closest_file:
        return os.path.join(folder_path, closest_file)
    return None


def parse_verses(verse_str: str):
    result = []
    for part in verse_str.split(','):
        part = part.strip()
        if "-" in part:
            start, end = part.split('-')
            result.extend(range(int(start), int(end) + 1))
        else:
            result.append(int(part))
    return sorted(result)


def create_service(service_type: str):
    label = "Morning Service" if service_type == "morning" else "Evening Service"
    return {
        "title": None,
        "songs": [],
        "date": None,
        "service_type": service_type,
        "service_label": label,
        "scripture": None,
        "offering": None,
        "isNicene": False,
        "isLordsSupper": False,
    }


def parse_bulletin(folder_path: str):
    morning_service = create_service("morning")
    evening_service = create_service("evening")

    file_path = get_closest_bulletin(folder_path, datetime.today().date())
    if not file_path:
        print("No bulletin found in folder")
        return None

    file_date = parse_date(os.path.basename(file_path))

    with pdfplumber.open(file_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        lines = full_text.splitlines()
        current_service = None
        expecting_offering_line2 = False  # flag to catch the second offering line

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect service sections
            if "Morning Worship" in line:
                current_service = morning_service
                current_service["date"] = file_date.strftime("%B %d, %Y")
                expecting_offering_line2 = False
                continue

            if "Afternoon Worship" in line or "Evening Worship" in line:
                current_service = evening_service
                current_service["date"] = file_date.strftime("%B %d, %Y")
                expecting_offering_line2 = False
                continue

            if current_service is None:
                continue

            # Offering line 2: "2. Reformed Missions—Costa Rica" — this is the one we want
            if expecting_offering_line2:
                line2_match = offering_line2_pattern.match(line)
                if line2_match:
                    current_service["offering"] = line2_match.group(1).strip()
                expecting_offering_line2 = False
                continue

            # Title
            title_match = title_pattern.search(line)
            if title_match:
                current_service['title'] = title_match.group(1).strip()
                continue

            # Scripture
            text_match = text_pattern.search(line)
            if text_match:
                current_service["scripture"] = text_match.group(1).strip()
                continue

            # Offering line 1: "Offerings: 1. Budget" — store temporarily, we want line 2
            offering_match = offering_pattern.search(line)
            if offering_match:
                expecting_offering_line2 = True
                continue

            # Songs
            song_match = song_pattern.search(line)
            if song_match:
                verses = None
                if song_match.group(2):
                    verses = parse_verses(song_match.group(2))
                song = {
                    "number": song_match.group(1),
                    "verses": verses
                }
                current_service["songs"].append(song)
                continue

            # Nicene Creed
            if "nicene" in line.lower():
                current_service["isNicene"] = True

            # Lord's Supper
            if "communion" in line.lower():
                current_service["isLordsSupper"] = True

        return {
            "morning_service": morning_service,
            "evening_service": evening_service
        }

    return None