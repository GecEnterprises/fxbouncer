from datetime import datetime

import click
import os

import pathlib
from tqdm import tqdm
import sys

from fxbouncer.fxt import OpenGraphData, download_and_write_image, list_to_downloadables
from fxbouncer.scrape import scrape_and_download, download_file
import json

replace_with_domain = 'https://fxtwitter.com'

def save_json(results:[OpenGraphData], output_directory=None):
    """Save scraped OpenGraph data to a JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'og_data_{timestamp}.json'

    if output_directory:
        filename = os.path.join(output_directory, filename)

    conv = []
    for r in results:
        conv.append(r.to_dict())

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(conv, f, ensure_ascii=False, indent=4)

    return filename


@click.group()
def cli():
    """Uses fxtwitter to download content from X or other platforms."""
    pass


@cli.command(name='d')
@click.argument('url')
@click.option('--mosaic-merging', type=bool, default=False, help='Enable mosaic merging')
@click.option('--meta-json', type=bool, default=False, help='Generate meta JSON')
@click.option('--output-directory', '--output', type=click.Path(exists=True), help='Output directory')
def download(url, mosaic_merging, meta_json, output_directory):
    """Download content from a single URL."""
    headers = {"User-Agent": "TelegramBot (https://core.telegram.org/bots)"}
    click.echo(f"Downloading from: {url}")

    processed_url, og_data = scrape_and_download(url, headers, replace_with_domain)
    if og_data:
        results = {processed_url: og_data}
        save_json(results, output_directory)
    click.echo(f"Download completed.")

@cli.command(name='bd')
@click.argument('input', type=click.Path(exists=True))
@click.option('--mosaic-merging', type=bool, default=False, help='Enable mosaic merging')
@click.option('--meta-json', type=bool, default=False, help='Generate meta JSON')
@click.option('--output-directory', '--output', type=click.Path(exists=True), help='Output directory')
def batch_download(input, mosaic_merging, meta_json, output_directory):
    """Batch download content from multiple URLs."""
    headers = {"User-Agent": "TelegramBot (https://core.telegram.org/bots)"}

    # Reading URLs from input file
    if os.path.isfile(input):
        with open(input, 'r') as file:
            urls = [line.strip().split('?')[0] for line in file.readlines()]
    else:
        urls = input.split(',')

    output_directory = pathlib.Path(output_directory) if output_directory else pathlib.Path.cwd()

    results: [OpenGraphData] = []
    total_urls = len(urls)

    # Using tqdm with sys.stderr to avoid clashing with click.echo output
    with tqdm(urls, desc="Processing URLs", total=total_urls, file=sys.stderr) as progress_bar:
        for url in progress_bar:
            try:
                progress_bar.set_postfix_str(f"{url}")  # Update tqdm status
                processed_url, og_data = scrape_and_download(url, headers, replace_with_domain)
                if og_data:
                    results.append(og_data)
            except Exception as e:
                click.echo(f"Error processing URL {url}: {str(e)}", err=True)

    save_json(results, output_directory)

    downloadables = list_to_downloadables(results)

    with tqdm(downloadables, desc="Downloading Files", total=len(downloadables), file=sys.stderr) as progress_bar:
        for downloadable in progress_bar:
            filename = downloadable.title  # The title will be used as the filename
            possible_urls = downloadable.possible_urls

            success = False
            for download_url in possible_urls:
                try:
                    progress_bar.set_postfix_str(f"Trying: {download_url}")  # Update tqdm status
                    success = download_file(filename, download_url, output_directory)  # Try each possible URL
                    if success:
                        break  # If download succeeds, stop trying further URLs
                except Exception as e:
                    click.echo(f"Error downloading {filename} from {download_url}: {str(e)}", err=True)

            if not success:
                click.echo(f"Skipping {filename}, no valid URLs found.", err=True)

    click.echo(f"Scraping completed")

if __name__ == '__main__':
    cli()