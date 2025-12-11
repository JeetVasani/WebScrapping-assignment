# import os
# import requests
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from fake_useragent import UserAgent
# import urllib

# load_dotenv() 

# API_KEY = os.getenv("SCRAPERAPI_KEY")

# if not API_KEY:
#     raise RuntimeError("SCRAPERAPI_KEY missing in .env")

# def extract_and_clean(url: str) -> str:
#     if "uddg=" in url:
#         encoded = url.split("uddg=")[1].split("&")[0]
#         url = urllib.parse.unquote(encoded)

#     url = url.split("?")[0].split("&")[0]
#     return url

# def ddg_single_search(query):
#     ddg_url = f"https://lite.duckduckgo.com/lite/?q={requests.utils.quote(query)}"

#     scraper_url = "https://api.scraperapi.com"
#     payload = {
#         "api_key": API_KEY,
#         "url": ddg_url,
#         "keep_headers": "true"
#     }

#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
#         "Accept-Language": "en-US,en;q=0.9"
#     }

#     r = requests.get(scraper_url, params=payload, headers=headers, timeout=30)
#     open("debug_ddg.html", "w", encoding="utf-8").write(r.text)
#     soup = BeautifulSoup(r.text, "html.parser")

#     # TRY MULTIPLE SELECTORS
#     links = soup.select(
#         "a.result-link, a.result__a, a.result-link.js-result-title-link"
#     )
    

#     # FALLBACK: ANY http link
#     if not links:
#         all_links = soup.find_all("a")
#         links = []
#         for a in all_links:
#             href = a.get("href", "")
#             if href.startswith("http"):
#                 links.append(a)

#     extracted = []
#     for a in links:
#         href = a.get("href", "")
#         if not href:
#             continue

#         title = a.get_text(strip=True)
#         clean = extract_and_clean(href)
#         extracted.append((title, clean))

#     return extracted



# # -------------------------------
# # CAREER PAGE EXTRACTION (LIGHT VERSION)
# # -------------------------------
# def get_career_page(company_name, company_desc, website):
#     career_keywords = ["career", "careers", "job", "jobs", "hiring", "join"]

#     # PASS 1 (1 API call)
#     query = f"{company_name} {company_desc} careers"
#     results = ddg_single_search(query)

#     for url in results:
#         lower = url.lower()
#         if any(k in lower for k in career_keywords):
#             return url

#     # PASS 2 (1 API call)
#     # domain = get_domain(website)
#     # if domain:
#     #     query = f"site:{domain} careers"
#     #     results = ddg_single_search(query)

#     #     for title, url in results:
#     #         lower = url.lower()
#     #         if any(k in lower for k in career_keywords):
#     #             return url

#     return ""


# # -------------------------------
# # JOB POSTINGS (2 SITES = 2 API CALLS)
# # -------------------------------
# def get_job_postings(company_name, company_desc, max_jobs=3):

#     job_sites = [
#         "indeed.com"
#         # "naukri.com"
#     ]

#     job_links = []

#     for site in job_sites:
#         query = f"{company_name} {company_desc} jobs site:{site}"
#         results = ddg_single_search(query)

#         for title, url in results:
#             if site in url.lower():
#                 job_links.append(url)

#             if len(job_links) >= max_jobs:
#                 break

#         if len(job_links) >= max_jobs:
#             break

#     while len(job_links) < max_jobs:
#         job_links.append("")

#     return job_links


# # -------------------------------
# # MAIN EXTRACTOR (1 API CALL)
# # -------------------------------
# def extract_company_data(company_name, company_desc):
#     # ONE SEARCH ONLY
#     query = f"{company_name} {company_desc} official website linkedin"
#     results = ddg_single_search(query)

#     website = ""
#     linkedin = ""

#     for title, url in results:
#         lower = url.lower()

#         # WEBSITE
#         if website == "" and any(ext in lower for ext in [".com", ".org", ".in", ".net"]):
#             website = url

#         # LINKEDIN
#         if linkedin == "" and "linkedin.com" in lower:
#             linkedin = url

#     # CAREER PAGE (1–2 API calls)
#     career_page = get_career_page(company_name, company_desc, website)

#     # JOB POSTINGS (1–2 API calls)
#     jobs = get_job_postings(company_name, company_desc)

#     return {
#         "website": website,
#         "linkedin": linkedin,
#         "career_page": career_page,
#         "jobs": jobs
#     }
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import urllib

load_dotenv()

API_KEY = os.getenv("SCRAPERAPI_KEY")
if not API_KEY:
    raise RuntimeError("SCRAPERAPI_KEY missing in .env")


# ---------------------------------------
# CLEAN URL
# ---------------------------------------
def extract_and_clean(url: str) -> str:
    if "uddg=" in url:
        encoded = url.split("uddg=")[1].split("&")[0]
        url = urllib.parse.unquote(encoded)

    url = url.split("?")[0].split("&")[0]
    return url


# ---------------------------------------
# DDG SEARCH
# ---------------------------------------
def ddg_single_search(query):
    ddg_url = f"https://lite.duckduckgo.com/lite/?q={requests.utils.quote(query)}"

    scraper_url = "https://api.scraperapi.com"
    payload = {
        "api_key": API_KEY,
        "url": ddg_url,
        "keep_headers": "true"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9"
    }

    r = requests.get(scraper_url, params=payload, headers=headers, timeout=30)

    # DEBUG MUST BE AFTER FETCHING r
    with open("debug_ddg.html", "w", encoding="utf-8") as f:
        f.write(r.text)

    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.select("a.result-link")

    if not links:
        links = soup.find_all("a")

    extracted = []
    for a in links:
        href = a.get("href", "")
        if not href:
            continue
        title = a.get_text(strip=True)
        clean = extract_and_clean(href)
        extracted.append((title, clean))

    return extracted



# ---------------------------------------
# CAREER PAGE
# ---------------------------------------
def get_career_page(company_name, company_desc, website):
    career_keywords = ["career", "careers", "job", "jobs", "hiring", "join"]

    # PASS 1
    query = f"{company_name} {company_desc} careers"
    results = ddg_single_search(query)

    for title, url in results:
        if not isinstance(url, str):
            continue
        lower = url.lower()

        if any(k in lower for k in career_keywords):
            return url

    return ""


# ---------------------------------------
# JOB POSTINGS
# ---------------------------------------
def get_job_postings(company_name, company_desc, max_jobs=3):

    job_sites = ["indeed.com"]
    job_links = []

    for site in job_sites:
        query = f"{company_name} {company_desc} jobs site:{site}"
        results = ddg_single_search(query)

        for title, url in results:
            if not isinstance(url, str):
                continue

            if site in url.lower():
                job_links.append(url)

            if len(job_links) >= max_jobs:
                break

        if len(job_links) >= max_jobs:
            break

    while len(job_links) < max_jobs:
        job_links.append("")

    return job_links


# ---------------------------------------
# MAIN EXTRACTOR
# ---------------------------------------
def extract_company_data(company_name, company_desc):

    query = f"{company_name} {company_desc} official website linkedin"
    results = ddg_single_search(query)

    website = ""
    linkedin = ""

    for title, url in results:
        if not isinstance(url, str):
            continue

        lower = url.lower()

        if not website and any(ext in lower for ext in [".com", ".org", ".net", ".in"]):
            website = url

        if not linkedin and "linkedin.com" in lower:
            linkedin = url

    # Career (1 call)
    career_page = get_career_page(company_name, company_desc, website)

    # Jobs (1 call)
    jobs = get_job_postings(company_name, company_desc)

    return {
        "website": website,
        "linkedin": linkedin,
        "career_page": career_page,
        "jobs": jobs
    }
