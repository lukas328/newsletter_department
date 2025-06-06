# Newsletter Department

This project contains a small pipeline that fetches news and other information and assembles a simple newsletter. The code is intentionally lightweight so that it can be executed locally without additional infrastructure.

## Setup

1. Create a Python virtual environment (optional but recommended).
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in the required API keys.

## Running the pipeline

Execute the entry point directly:

```bash
python main.py
```

Logging can be configured via the environment variables `LOG_LEVEL` and `LOG_FILE`.

## Tests

Tests are located in the `tests/` folder. After installing the requirements you can run them with:

```bash
pytest
```

## Environment variables

The following variables are used by the code (all are optional for testing except API keys for the fetchers you want to use):

- `OPENAI_API_KEY` – required for the LLM processors
- `OPENAI_DEFAULT_MODEL` – model name, default `gpt-3.5-turbo`
- `OPENWEATHER_API_KEY` – required for weather data
- `NEWSAPI_API_KEY` – required for news articles
- `NEWSLETTER_SOURCE_BLACKLIST` – comma separated list of sources to ignore
- `NEWSLETTER_CATEGORIES` – list of categories for the newsletter
- `NEWSLETTER_TOP_ARTICLE_COUNT` – number of articles that are fully written
- `LOG_LEVEL` – logging level, e.g. `INFO`
- `LOG_FILE` – path to a log file
- `LOG_ROTATE_SIZE_MB` – if set to a number >0, rotating log files will be used
- `LOG_ROTATE_BACKUP_COUNT` – number of rotated log files to keep (default 3)

See `.env.example` for a minimal example.
