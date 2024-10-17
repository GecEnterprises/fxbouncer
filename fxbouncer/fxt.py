from typing import Tuple, List

import pathlib
from dataclasses import dataclass, asdict
from datetime import datetime

import requests

from fxbouncer.structs import Downloadable


@dataclass
class OpenGraphData:
    url: str
    image: str
    image_width: str
    image_height: str
    title: str
    description: str
    site_name: str
    video: str
    video_secure_url: str
    video_height: str
    video_width: str
    video_type: str

    def to_dict(self):
        """Convert the OpenGraphData instance to a dictionary for JSON serialization, omitting empty fields."""
        return {
            key: value for key, value in {
                "url": self.url,
                "image": self.image,
                "image_width": self.image_width,
                "image_height": self.image_height,
                "title": self.title,
                "description": self.description,
                "site_name": self.site_name,
                "video": self.video,
                "video_secure_url": self.video_secure_url,
                "video_height": self.video_height,
                "video_width": self.video_width,
                "video_type": self.video_type,
            }.items() if value  # Only include non-empty values
        }

import re

def extract_username(input_string):
    # Use a regular expression to find the pattern
    match = re.search(r'@(\w+)', input_string)
    if match:
        return match.group(1)  # Return the first captured group
    return None  # Return None if no match is found

def extract_tweet_id(url):
    # Use a regular expression to find the numeric tweet ID
    match = re.search(r'/(\d+)(?:[/?]|$)', url)
    if match:
        return match.group(1)  # Return the first captured group (the tweet ID)
    return None  # Return None if no match is found

def extract_filename(url):
    # Use a regular expression to find the filename at the end of the URL
    match = re.search(r'([^/]+\.(?:jpg|mp4|png))(?:\?.*)?$', url)
    if match:
        return match.group(1)  # Return only the filename without query parameters
    return None  # Return None if no match is found


def transform_mosaic(input_url):
    # Check if the input URL contains the correct domain
    if "mosaic.fxtwitter.com" not in input_url:
        return [input_url]

    # Check the input URL to determine the format (jpeg or png)
    if "jpeg" in input_url:
        media_format = "jpg"
    elif "png" in input_url:
        media_format = "png"
    else:
        raise ValueError("Unsupported format. Please provide a URL containing 'jpeg' or 'png'.")

    # Extract the base URL and the media IDs
    base_url = "https://pbs.twimg.com/media/"
    parts = input_url.split("/")[5:]  # Split the URL and get the relevant parts

    # Construct the new media URLs
    media_urls = [f"{base_url}{media_id}.{media_format}" for media_id in parts]

    return media_urls

def compose_username_tweet_id_filename(input_string, tweet_url, media_url, part_number=None):
    username = extract_username(input_string)
    tweet_id = extract_tweet_id(tweet_url)
    filename = extract_filename(media_url)

    if username and tweet_id and filename:
        # Append part number if provided
        if part_number is not None:
            return f"{username}_{tweet_id}_Part-{part_number}_{filename}"
        return f"{username}_{tweet_id}_{filename}"

    return None

def transform_image_url_variants(url: str) -> List[str]:
    return [
        url.replace(".jpg", "?format=jpg&name=4096x4096"),
        url + ":large",
        url
    ]

def list_to_downloadables(data: List[OpenGraphData]) -> List[Downloadable]:
    arr: List[Downloadable] = []

    for d in data:
        if d.video != "":
            # Video case: only one URL
            arr.append(Downloadable(
                compose_username_tweet_id_filename(d.title, d.url, d.video),
                [d.video]
            ))
        else:
            # Image case: multiple possible URLs
            mosaics = transform_mosaic(d.image)

            # Check the number of image URLs
            if len(mosaics) > 1:
                for index, image_url in enumerate(mosaics, start=1):
                    arr.append(Downloadable(
                        compose_username_tweet_id_filename(d.title, d.url, d.image, part_number=index),
                        transform_image_url_variants(image_url)
                    ))
            else:
                # If there's only one image, don't pass part_number
                arr.append(Downloadable(
                    compose_username_tweet_id_filename(d.title, d.url, d.image),
                    transform_image_url_variants(mosaics[0])
                ))

    return arr

def download_and_write_image(data: OpenGraphData, outdir: pathlib.Path):
    # Ensure the output directory exists
    outdir.mkdir(parents=True, exist_ok=True)

    # Get the image URL
    image_url = data.image

    # Attempt to download the image
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # Raise an error for bad responses
    except requests.RequestException as e:
        print(f"Failed to download image: {e}")
        return

    # Determine the file extension from the URL
    file_extension = pathlib.Path(image_url).suffix or '.jpg'  # Default to .jpg if no suffix found

    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create the full filename
    filename = f"{timestamp}{file_extension}"

    # Write the image to the specified directory
    file_path = outdir / filename
    with open(file_path, 'wb') as f:
        f.write(response.content)

