import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

import requests
from utils import get_html_from_url


# -------------------- CONSTANTS --------------------

ATS_DOMAINS = [
    "teamtailor.com",
    "lever.co",
    "greenhouse.io",
    "zohorecruit.com",
    "workable.com",
    "smartrecruiters.com",
    "personio.com"
]

JOB_KEYWORDS = [
    "job", "careers", "career", "opening", "position",
    "vacancy", "opportunity", "hiring", "recruit",
]

# -------------------- URL VALIDATION --------------------

def is_valid_job_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False

    u = url.lower()

    # ATS domain → valid job
    if any(ats in u for ats in ATS_DOMAINS):
        return True

    # Strict /job/ or /jobs/ with slug or id
    if "/job/" in u or "/jobs/" in u:
        parts = u.split("/job/") if "/job/" in u else u.split("/jobs/")
        return len(parts) > 1 and len(parts[1]) > 3

    return False


# -------------------- ATS DETECTION --------------------

def detect_ats(url: str, html: str) -> str:
    u = url.lower()
    h = html.lower()


    if "personio" in u or "personio" in h:
        return "personio"
    if "teamtailor" in u or "teamtailor" in h:
        return "teamtailor"
    if "lever.co" in u or "lever" in h:
        return "lever"
    if "greenhouse.io" in u or "greenhouse" in h:
        return "greenhouse"
    if "zohorecruit.com" in u or "zoho" in h:
        return "zoho"

    print("No ATS found, trying generic exctraction")
    return "generic"



# -------------------- TEAMTAILOR --------------------

def extract_teamtailor_jobs(html: str, base_url: str, limit: int = 3):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for a in soup.select("a[href*='/jobs/']"):
        title = a.get_text(strip=True)
        href = a.get("href")

        if not href or not title or len(title) < 3:
            continue

        full_url = urljoin(base_url, href)
        if not is_valid_job_url(full_url):
            continue

        jobs.append({"url": full_url, "title": title})

        if len(jobs) == limit:
            break

    return jobs


# -------------------- ZOHO RECRUIT --------------------

def extract_zoho_jobs(html: str, base_url: str, limit: int = 3):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]

        if not text or len(text) < 3:
            continue

        full_url = urljoin(base_url, href)
        if not is_valid_job_url(full_url):
            continue

        jobs.append({"url": full_url, "title": text})

        if len(jobs) == limit:
            break

    return jobs


# -------------------- PERSONIO --------------------

def extract_personio_jobs(html: str, base_url: str, limit: int = 3):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    job_elements = soup.find_all("a", class_=["job-box-link", "job-box"])

    for job_link in job_elements:
        title_element = job_link.find("div", class_="job-box-title")
        
        if title_element:
            text = title_element.get_text(strip=True)
        else:
            text = job_link.get_text(strip=True)
            
        href = job_link.get("href")

        if not text or len(text) < 5:
            continue
        
        if not href or href.startswith(('#', 'javascript')):
            continue

        full_url = urljoin(base_url, href)
        
        jobs.append({"url": full_url, "title": text})

        if len(jobs) == limit:
            break

    return jobs

# -------------------- LEVER --------------------

def extract_lever_jobs(html: str, base_url: str, limit: int = 3):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for div in soup.select("div.posting"):
        a = div.find("a", href=True)
        h2 = div.find("h5")

        if not a or not h2:
            continue

        title = h2.get_text(strip=True)
        full_url = urljoin(base_url, a["href"])

        if not is_valid_job_url(full_url):
            continue

        jobs.append({"url": full_url, "title": title})

        if len(jobs) == limit:
            break

    return jobs


# -------------------- GREENHOUSE --------------------

def extract_greenhouse_jobs(html: str, base_url: str, limit: int = 3):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for a in soup.select("a[href*='/jobs/']"):
        title = a.get_text(strip=True)
        href = a["href"]

        if not title or len(title) < 3:
            continue

        full_url = urljoin(base_url, href)
        if not is_valid_job_url(full_url):
            continue

        jobs.append({"url": full_url, "title": title})

        if len(jobs) == limit:
            break

    return jobs


# -------------------- GENERIC FALLBACK --------------------

JOB_CONTAINER_KEYWORDS = [
    "job", "posting", "opening", "listing", "position", "vacancy", "career"
]

# Define words that are often *not* job titles, even if in a link
NON_TITLE_WORDS = [
    "apply", "view", "details", "learn more", "read more", "click here"
]


def extract_generic_jobs(html: str, base_url: str, limit: int = 4) -> list:
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    
    # --- Step 1 & 2: Identify Potential Job Containers ---
    potential_containers = []
    
    search_tags = ["div", "li", "section", "article"]
    
    for tag in search_tags:
        for keyword in JOB_CONTAINER_KEYWORDS:
            for element in soup.find_all(tag, class_=True):
                if keyword in element["class"]:
                    potential_containers.append(element)
                    
            for element in soup.find_all(tag, id=True):
                if keyword in element["id"]:
                    potential_containers.append(element)
                    
    # Use a set to handle duplicates from searching multiple tags/keywords
    unique_containers = list(set(potential_containers))
    
    # --- Step 3: Extract Data from Valid Containers ---
    
    for container in unique_containers:
        link_element = container.find('a', href=True)
        
        if not link_element:
            continue
            
        full_url = urljoin(base_url, link_element["href"])

        title_element = container.find(["h2", "h3"])
        
        if title_element:
            title = title_element.get_text(strip=True)
        else:
            title = link_element.get_text(strip=True)
            
        # Basic Title Validation
        if len(title) < 10 or any(word in title.lower() for word in NON_TITLE_WORDS):
             continue 
        
        location_element = container.find(text=lambda t: t and ("," in t or "remote" in t.lower()))
        job_location = location_element.strip() if location_element else "N/A"

        
        jobs.append({
            "job_posting_url": full_url,
            "job_title": title,
            "job_location": job_location
        })

        if len(jobs) == limit:
            break

    return jobs



# -------------------- MAIN --------------------

def extract_jobs_from_listing(job_page_url: str, html: str, limit: int = 3):
    ats = detect_ats(job_page_url, html)

    if ats == "personio":
        return extract_personio_jobs(html, job_page_url, limit)
    if ats == "teamtailor":
        return extract_teamtailor_jobs(html, job_page_url, limit)
    if ats == "zoho":
        return extract_zoho_jobs(html, job_page_url, limit)
    if ats == "lever":
        return extract_lever_jobs(html, job_page_url, limit)
    if ats == "greenhouse":
        return extract_greenhouse_jobs(html, job_page_url, limit)

    return extract_generic_jobs(html, job_page_url, limit)
