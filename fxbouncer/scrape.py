import shutil
from typing import Tuple, Literal

import click
import pathlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import os
from tqdm import tqdm

from fxbouncer.fxt import OpenGraphData
import m3u8

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6401.0 Safari/537.36'
}

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

    #  Check if the url has m3u8
    if '.m3u8' in url:
        # playlist = m3u8.load(url)
        # playlist.dump(local_filename + ".m3u8")

        # check if yt-dlp is available in the shell
        if not shutil.which("yt-dlp"):
            click.echo("Error while download m3u8 format! yt-dlp not found! Please install yt-dlp to enable m3u8 downloading")
            return False

        filename_no_ext = filename.replace(".mp4", "")

        os.system(f'yt-dlp --hls-prefer-native "{url}" --output "{filename_no_ext}_%(title)s-[%(format_id)s].mp4"')
        return True
    else:
        try:
            # Enable redirects and add custom headers
            with requests.get(url, stream=True, headers=headers, allow_redirects=True) as r:
                if not r.ok:
                    click.echo(f"Failed to download {url}: {r.status_code}")
                    return False

                content_type = r.headers.get('content-type', '')
                if 'text/' in content_type:
                    click.echo(f"Skipping {url}, MIME type mismatch: {content_type}")
                    return False

                r.raise_for_status()

                total_length = int(r.headers.get('content-length', 0))
                with open(local_filename, 'wb') as f:
                    if total_length == 0:
                        f.write(r.content)
                    else:
                        for chunk in tqdm(r.iter_content(chunk_size=4096), total=total_length // 4096,
                                          desc=f"Downloading {filename}", unit='KB'):
                            if chunk:
                                f.write(chunk)
                return True
        except Exception as e:
            click.echo(f"Error during download from {url}: {str(e)}")
            return False

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

def get_final_url(url, max_redirects=3):
    """Recursively follow redirects to get the final URL, limited to max_redirects."""
    try:
        response = requests.get(url, headers=headers, allow_redirects=True)
        if response.url != url:
            return response.url
        if response.is_redirect and max_redirects > 0:
            new_url = response.headers['Location']
            return get_final_url(new_url, headers, max_redirects - 1)
        return url
    except requests.RequestException as e:
        click.echo(f"Error following redirects for {url}: {str(e)}", err=True)
        return url

def scrape_and_download(url, headers, replace_with_domain) -> tuple[Literal[b""], OpenGraphData] | tuple[
    Literal[b""], None]:
    """Helper function to process and scrape a URL."""
    processed_url = process_url(url, replace_with_domain)

    og_data = scrape_og_tags(processed_url, headers)

    if og_data:
        video_type = og_data.get("video:type", "")
        video = og_data.get("video", "")
        video_secure_url = og_data.get("video:secure_url", "")

        if video_type == "application/x-mpegURL":
            last_redirect = get_final_url(video)
            video_secure_url = last_redirect
            video = last_redirect


        return processed_url, OpenGraphData(
            url=og_data.get("url", ""),
            image=og_data.get("image", ""),
            image_width=og_data.get("image:width", ""),
            image_height=og_data.get("image:height", ""),
            title=og_data.get("title", ""),
            description=og_data.get("description", ""),
            site_name=og_data.get("site_name", ""),
            video=video,
            video_secure_url=video_secure_url,
            video_type=video_type,
            video_width=og_data.get("video:width", ""),
            video_height=og_data.get("video:height", "")
        )
    return processed_url, None


