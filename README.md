## Introduction
This project is a practical web scraping pipeline built to enrich basic company information and collect recent job postings from official career pages. It focuses on using primary sources and common ATS platforms to ensure the extracted data is accurate, consistent, and easy to verify.

---

## Tech Stack

- **Language**: Python  
- **Web Scraping**: Requests, BeautifulSoup  
- **Data Processing**: Pandas  
- **Excel Handling**: OpenPyXL  
- **Concurrency**: concurrent.futures (ThreadPoolExecutor)  
- **HTTP / Proxy Layer**: ScraperAPI  
- **Utilities**: Standard Python libraries (re, json, urllib)


---

## Input
- **Excel file** containing the following base fields:
  - `company_name`
  - `company_description`

These fields are used as the starting point for all discovery and enrichment steps.

---
## How I created this pipline: 

### Step 1: Core Utilities and ATS Abstractions
Reusable utility functions were implemented to support the pipeline.

**Core utilities**
- `first_link_on_search`: Returns the first valid link for a given search query.
- `get_html_from_url`: Fetches raw HTML content from a URL.
- `extract_links`: Extracts links from anchors, iframes, and embedded references.
- `clean_url`: Normalizes URLs by removing search wrappers and noise.

**Job extraction utilities**
- `detect_ats`: Identifies which ATS provider a careers page uses.
- ATS-specific extractors:
  - `extract_lever_jobs`
  - `extract_greenhouse_jobs`
  - `extract_zoho_jobs`
  - `extract_personio_jobs`
  - `extract_teamtailor_jobs`
- `extract_generic_jobs`: Handles non-ATS or custom job pages.
- `is_valid_job_url`: Filters valid job posting URLs.
- `extract_jobs_from_listing`: Routes extraction to the appropriate extractor.
- `indeed_jobs`: Limited fallback when insufficient jobs are found.

---

### Step 2: Company Metadata Discovery
For each company row:
- The official website is identified using `first_link_on_search`.
- LinkedIn and careers pages are extracted from the website HTML when present.
- If unavailable, a controlled fallback search is used.

Only company-owned or clearly associated pages are accepted.

---

### Step 3: Job Listings Page Identification
- The careers page is analyzed to detect ATS usage.
- If an ATS is detected, the corresponding job listings page is extracted.
- If not, the careers page itself is treated as the listings page.

---

### Step 4: Job Extraction
- Job postings are extracted using `extract_jobs_from_listing`.
- ATS-specific logic is used when applicable.
- Generic extraction is applied for non-ATS pages.
- If fewer than 3 jobs are found, a constrained fallback is used.

Extraction is limited to the **most recent 3 job postings per company**.

---

### Step 5: Data Processing and Output Generation
- The input Excel file is loaded into a dataframe.
- Each row is processed concurrently using multithreading (5 workers).
- Newly extracted fields are aligned with the original rows.
- The final dataset is written to a new Excel file.

---

### Output
The generated Excel file contains the following columns:

- `company_name`
- `company_description`
- `Website URL`
- `Linkedin URL`
- `Careers Page URL`
- `Job Page URL`
- `Job post1`
- `Job title1`
- `Job post2`
- `Job title2`
- `Job post3`
- `Job title3`

Each job post column contains a verifiable job posting URL.

---

### Step 6: Output Verification
- Random checks are performed to ensure URLs are reachable.
- Invalid or broken links are excluded from the final output.

---

## Notes
- The pipeline prioritizes accuracy over coverage.
- Not all companies are expected to have open job postings.
- The system is deterministic and reproducible.

---

## Setup and Usage

### Download
Clone the repository locally:

```bash
git clone https://github.com/JeetVasani/WebScrapping-assignment.git
cd WebScrapping-assignment
```

### Run

``` bash
python main_final.py
```

> Note: The pipeline requires a `SCRAPERAPI_KEY` to be set as an environment variable before running.
