import os
from pptx import Presentation
from slide_generator.logic.parse_bulletin import parse_bulletin
from slide_generator import generate_powerpoint_slides
from tracker import update_tracker

BASE_DIR = os.path.dirname(__file__)
FORMATTING_FILE = os.path.join(BASE_DIR, "slide_data","song_slide_formatting.json")
SONG_DIR = os.path.join(BASE_DIR, "song_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "powerpoints")
BULLETIN_DIR = os.path.join(BASE_DIR, "bulletins")


def generate_powerpoint(service_data):
    generate_powerpoint_slides(service_data)


if __name__ == "__main__":
    bulletin_data = parse_bulletin(BULLETIN_DIR)
    for data in bulletin_data:
        generate_powerpoint(bulletin_data[data])