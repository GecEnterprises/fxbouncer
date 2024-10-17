from typing import Tuple, Literal

import click
import pathlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import os
from tqdm import tqdm

from fxbouncer.fxt import OpenGraphData


def scrape_og_tags(url, headers):
    """Scrape OpenGraph tags from a URL."""
    try:
        response = requests.get(url, headers=headers, allow_redirects=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))

        og_data = {}
        for tag in og_tags:
            property_name = tag.get('property')[3:]  # Remove 'og:' prefix
            content = tag.get('content')
            og_data[property_name] = content

        return og_data
    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return None


def download_file(filename: str, url: str, output_directory: pathlib.Path) -> bool:
    local_filename = os.path.join(output_directory, filename)

    try:
        with requests.get(url, stream=True) as r:
            if not r.ok:
                click.echo(f"Failed to download {url}: {r.status_code}")
                return False  # Non-2xx status, skip to the next URL

            content_type = r.headers.get('content-type', '')
            if 'text/' in content_type:
                click.echo(f"Skipping {url}, MIME type mismatch: {content_type}")
                return False  # MIME type is not an image or video

            r.raise_for_status()  # Raise an error for other bad responses

            total_length = int(r.headers.get('content-length', 0))
            with open(local_filename, 'wb') as f:
                if total_length == 0:  # Handle cases where content-length is not available
                    f.write(r.content)
                else:
                    for chunk in tqdm(r.iter_content(chunk_size=4096), total=total_length // 4096,
                                      desc=f"Downloading {filename}", unit='KB'):
                        if chunk:  # Filter out keep-alive new chunks
                            f.write(chunk)
        return True  # Success
    except Exception as e:
        click.echo(f"Error during download from {url}: {str(e)}")
        return False  # Skip to the next URL

def process_url(url, new_domain):
    """Process a URL to change the domain and keep only the path."""
    parsed_url = urlparse(url)

    # Extract the path from the original URL
    path = parsed_url.path

    # Create a new URL with the new domain and the extracted path
    new_url = urlparse(new_domain)

    # Ensure new_url is well-formed, and replace the path
    new_url = new_url._replace(path=path)

    return urlunparse(new_url)


def scrape_and_download(url, headers, replace_with_domain) -> tuple[Literal[b""], OpenGraphData] | tuple[
    Literal[b""], None]:
    """Helper function to process and scrape a URL."""
    processed_url = process_url(url, replace_with_domain)

    og_data = scrape_og_tags(processed_url, headers)

    if og_data:
        return processed_url, OpenGraphData(
            url=og_data.get("url", ""),
            image=og_data.get("image", ""),
            image_width=og_data.get("image:width", ""),
            image_height=og_data.get("image:height", ""),
            title=og_data.get("title", ""),
            description=og_data.get("description", ""),
            site_name=og_data.get("site_name", ""),
            video=og_data.get("video", ""),
            video_secure_url=og_data.get("video:secure_url", ""),
            video_type=og_data.get("video:type", ""),
            video_width=og_data.get("video:width", ""),
            video_height=og_data.get("video:height", "")
        )
    return processed_url, None


