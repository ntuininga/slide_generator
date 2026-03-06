from PIL import Image
import os
import uuid
import six


def add_center_cropped_background(slide, image_path, prs):
    img = Image.open(image_path)

    target_width_px = prs.slide_width // 9525  
    target_height_px = prs.slide_height // 9525

    cropped = center_crop_width_to_fit(img, target_width_px, target_height_px)

    temp_path = os.path.join("slide_data", f"temp_bg_{uuid.uuid4().hex}.jpg")
    cropped.save(temp_path)

    bg = slide.shapes.add_picture(
        temp_path,
        0,
        0,
        width=prs.slide_width,
        height=prs.slide_height
    )

    os.remove(temp_path)

def center_crop_width_to_fit(img, target_width_px, target_height_px, crop_center=False, crop_offset=1067):

    img_width, img_height = img.size
    target_ratio = target_width_px / target_height_px

    new_width = int(img_height * target_ratio)

    crop_offset = img_width / 4

    # Ensure we don't go beyond image bounds
    if new_width >= img_width:
        left = 0
        right = img_width
    else:
        if crop_center:
            left = (img_width - new_width) // 2
        else:
            left = crop_offset
            left = max(0, min(left, img_width - new_width))  # clamp to valid range
        right = left + new_width

    top = 0
    bottom = img_height

    return img.crop((left, top, right, bottom))