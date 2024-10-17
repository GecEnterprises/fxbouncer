# fxbouncer

Scrape content from X by utilizing fxtwitter embed proxy! Powered by BS4+requests.

## Install
```sh
# Standard installation
pip install .

# For development (editable mode), use:
# pip install -e .
```

fxbouncer should run on anything that runs Python.

## Usage
### Single Download
```sh
fxbouncer d <URL> [OPTIONS]
```

Optionals:
- `--mosaic-merging`: Disable mosaic merging (upcoming feature, currently always disabled)
- `--meta-json`: Disable meta JSON generation (currently always enabled)
- `--output-directory` or `--output`: Specify the output directory

### Batched
```sh
fxbouncer bd <INPUT> [OPTIONS]
```

The `<INPUT>` can be either a file containing URLs (one per line) or a comma-separated list of URLs.

Optionals:
- `--mosaic-merging`: Disable mosaic merging (upcoming feature, currently always disabled)
- `--meta-json`: Disable meta JSON generation (currently always enabled)
- `--output-directory` or `--output`: Specify the output directory

### Mosaic Merging
By default, fxtwitter merges 2 or more images into one image so any embed can display it properly. fxbouncer currently splits those links and download these individually. In the future, an option to download mosaic merged images as is will be available.

### Meta JSON
Meta JSON generation is currently enabled by default for all downloads.

## More examples
```sh
# Single
fxbouncer d https://twitter.com/example/status/123456789 --output ./downloads

# Batch txt file:
fxbouncer bd urls.txt --output ./batch_downloads

# Batch directly passing links:
fxbouncer bd https://twitter.com/example1,https://twitter.com/example2 --output ./multi_downloads
```

## License
GPL-3.0 license