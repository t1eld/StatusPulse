# StatusPulse

StatusPulse is a lightweight and efficient tool for scanning and monitoring HTTP status codes from multiple websites.

This project is designed for learning, testing, and basic website availability checking using Python.

---

## Features
- Scan HTTP status codes from multiple URLs
- Automatically adds `https://` when no protocol is provided
- Automatically removes duplicate URLs from the input file
- Simple and easy-to-use command-line interface (CLI)
- Clean and readable output format
- Designed to be extended with asynchronous scanning

---

## Requirements
- Python 3.8 or higher
- Dependencies:
  - aiohttp

---

## Installation
Clone the repository and install required dependencies:

```bash
pip install -r requirements.txt
```

---
## Usage

```bash
# Run the scanner with an input file
python3 scanner.py -u <your_path_file>

# Show help and available options
python3 scanner.py -h
```

## Options

```text
-u, --url <file>          Path to a file containing target URLs (required)
-o, --output <file>       Save successful (2xx) URLs to a file inside the result/ directory
-r, --retry <number>      Number of retry attempts on failure (default: 2)
-c, --concurrency <num>   Number of concurrent tasks (default: 10)
-t, --timeout <seconds>   Timeout in seconds for each request (default: 20)
--no-redirect             Disable following HTTP redirects (301, 302, etc)
-h, --help                Show this help message and exit
```

## Result

StatusPulse automatically creates a `result/` directory to store scan results.

If the `-o` or `--output` option is used, all successful URLs (HTTP status 2xx) will be saved into a file inside the `result/` directory.

Example command:

```bash
python3 scanner.py -u urls.txt -o live.txt
```
