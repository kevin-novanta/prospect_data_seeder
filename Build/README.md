# Prospect Data Seeder

A tool to seed prospect company data by scraping Clutch profiles, extracting public info, and enriching with LinkedIn URLs. Designed to be robust, portable, and usable by others.

## Table of Contents

- [What It Does](#what-it-does)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Limits & Caveats](#limits--caveats)
- [Schema & Data Fields](#schema--data-fields)
- [Testing & Validation](#testing--validation)
- [Contributing](#contributing)
- [License](#license)

## What It Does

- Collects company profiles from Clutch based on defined filters.
- Parses public website pages to extract key firmographic information (company name, industry, website URL, email, phone, address).
- Looks up the LinkedIn company profile URL.
- Stores normalized records into a database (or storage) for future use.

## Features

- Portable and packageable: designed so others can clone and run out of the box.
- Robust parsing with basic validation.
- Deduplication of records.
- Environment‐variable-based configuration — no secrets hardcoded.
- Sample data included for quick testing.

## Quick Start

> _Placeholder: fill this in with actual steps once built_

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in required values
3. Install dependencies (e.g. `npm install` or `pip install ‐r requirements.txt`)
4. Run the scraper locally: `make run` (or `docker run …`)
5. Inspect output database or storage

## Configuration


| Env Variable      | Description                                                | Example Value                  |
| ----------------- | ---------------------------------------------------------- | ------------------------------ |
| `DATABASE_URL`    | Connection string or URI for database                      | `postgres://user:pass@host/db` |
| `CLUTCH_FILTERS`  | Filters for which Clutch categories or locations to scrape | e.g.`web development, USA`     |
| `REQUEST_TIMEOUT` | HTTP request timeout in seconds                            | `10`                           |
| `MAX_CONCURRENT`  | Number of parallel requests allowed                        | `5`                            |
| `USER_AGENT`      | HTTP user agent string to use                              | `Mozilla/5.0 …`               |

## Limits & Caveats

- Only uses publicly available data; fields like email or phone might be missing.
- Clutch page layout changes may break parsing.
- Rate limiting or site blocks may occur — use conservative concurrency.
- LinkedIn lookup is done via public search; might result in false positives.
- Not designed for large scale scraping (yet) — best for a few hundred to a few thousand records per run.

## Schema & Data Fields


| Field            | Type      | Description                               |
| ---------------- | --------- | ----------------------------------------- |
| `company_name`   | String    | Name of the company                       |
| `website_url`    | String    | Main website URL                          |
| `industry`       | String    | Industry classification (Clutch + manual) |
| `email_public`   | String    | Public email if available                 |
| `phone_public`   | String    | Public phone number if available          |
| `address_public` | String    | Office or location address                |
| `linkedin_url`   | String    | Discovered LinkedIn company page URL      |
| `source_page`    | String    | URL of the Clutch or source profile       |
| `collected_at`   | Timestamp | When the record was collected             |

## Testing & Validation

- Include sample input files and expected output in `sample/` directory.
- Basic smoke tests for field parsing.
- Manual inspection of a small random subset for correctness.

## Contributing

Contributions welcome: bug reports, pull requests, and feature suggestions. Please respect the [Code of Conduct](./CODE_OF_CONDUCT.md) when contributing.

## License

MIT License – see `LICENSE` file for details.
