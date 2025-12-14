import os
import requests
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse, parse_qs, unquote, urlunparse, urlencode

from urllib.parse import urljoin
from typing import Dict, Union, List, Optional

load_dotenv()
API_KEY = os.getenv("SCRAPERAPI_KEY")
if not API_KEY:
    raise RuntimeError("SCRAPERAPI_KEY missing in .env")

JOB_KEYWORDS = [
    "job", "careers", "career", "opening", "position",
    "vacancy", "opportunity", "hiring", "recruit",
]
career_keywords = [
        "careers","career","jobs","job",
        "join-us","joinus","join",
        "work-with-us","workwithus","work",
        "opportunities","open-positions",
        "openings","vacancies","hiring","apply"
    ]
job_patterns = ["/jobs/", "/job/", "/positions/", "/position/", "/careers/", "/opening/", "/vacancy/", "/opportunity/"]

_session = requests.Session()

# get the html contents of a url
def get_html_from_url(url: str) -> str:
    if not API_KEY:
        return "API ERROR"

    try:
        r = _session.get(
            "http://api.scraperapi.com",
            params={
                "api_key": API_KEY,
                "url": url,
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.text
    except requests.RequestException:
        return ""
    
def clean_url(url):
        if not url:
            return url

        parsed = urlparse(url)

        # Case 1: DuckDuckGo redirect wrapper
        if parsed.hostname and "duckduckgo.com" in parsed.hostname:
            qs = parse_qs(parsed.query)
            encoded = qs.get("uddg", [None])[0]
            if encoded:
                return unquote(encoded)  # return the REAL URL

        # Case 2: normal URL → remove noise params
        qs = parse_qs(parsed.query)
        for junk in ("norw", "kp", "kl", "ia"):
            qs.pop(junk, None)

        clean_query = urlencode(qs, doseq=True)

        cleaned = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            clean_query,
            parsed.fragment,
        ))

        return cleaned

def get_first_link_on_search(query: str, return_html: bool):
        ddg = "https://lite.duckduckgo.com/lite/?q=" + requests.utils.quote(query)

        # Step 1: fetch DuckDuckGo results
        r = requests.get(
            "http://api.scraperapi.com",
            params={"api_key": API_KEY, "url": ddg},
            timeout=30
        )
        soup = BeautifulSoup(r.text, "html.parser")

        # Step 2: find the outbound link
        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Case 1: redirect link /l/?uddg=...
            if "uddg=" in href:
                parsed = urlparse(href)
                qs = parse_qs(parsed.query)
                encoded = qs.get("uddg", [None])[0]
                if encoded:
                    final_url = clean_url(unquote(encoded))
                    break

            # Case 2: direct external link
            if href.startswith("http"):
                final_url = clean_url(href)
                break
        else:
            return None

        # Step 3: fetch REAL WEBSITE HTML
        if return_html:
            real_html = requests.get(
                "http://api.scraperapi.com",
                params={"api_key": API_KEY, "url": final_url},
                timeout=30
            ).text

            return {
                "url": final_url,
                "html_str": real_html
            }

        return clean_url(final_url)

def extract_links(
    html_str: str, 
    base_url: str, 
    to_extract: Union[str, List[str]], 
    number_of_matches_to_find: int = 1, 
    multiple_strings_to_extract: bool = False
) -> Union[Optional[str], List[str]]:
    
    soup = BeautifulSoup(html_str, "html.parser")
    matches = []
    
    if multiple_strings_to_extract and isinstance(to_extract, list):
        search_terms = [term.lower() for term in to_extract if term]
    elif not multiple_strings_to_extract and isinstance(to_extract, str):
        search_terms = [to_extract.lower()]
    else:

        if isinstance(to_extract, list) and len(to_extract) > 0:
             search_terms = [str(to_extract[0]).lower()]
        else:
             return None if number_of_matches_to_find == 1 else []

    TAGS_TO_SEARCH = {
        "a": ["href"],
        "iframe": ["src"],
        "link": ["href"], 
    }

    all_target_tags = soup.find_all(list(TAGS_TO_SEARCH.keys()))    

    for tag in all_target_tags:
        hit = False
        full_url = None
        
        attrs_to_check = TAGS_TO_SEARCH.get(tag.name, [])
        
        
        for attr in attrs_to_check:
            if tag.has_attr(attr):
                attr_value = tag[attr].lower()
                
               
                for t in search_terms:
                    if t in attr_value:
                        hit = True
                        full_url = urljoin(base_url, tag[attr])
                        break
                if hit:
                    break
        
        if not hit and tag.name == "a":
            anchor_text = tag.get_text(strip=True).lower()
            
            for t in search_terms:
                if t in anchor_text:
                    hit = True
                    if tag.has_attr("href"):
                        full_url = urljoin(base_url, tag["href"])
                    break
        
        if hit and full_url:
            full_url = clean_url(full_url)
            matches.append(full_url)
            
            if len(matches) >= number_of_matches_to_find:
                break

    if number_of_matches_to_find == 1:
        return matches[0] if matches else None

    return matches


def indeed_jobs(
    company_name: str, 
    limit: int = 3
) -> List[Dict]:

    indeed_search_url = f"https://www.indeed.com/jobs?q={requests.utils.quote(company_name)}"
    indeed_html_content = get_html_from_url(indeed_search_url)
    soup = BeautifulSoup(indeed_html_content, 'html.parser')
    
    divs = soup.find_all('div', class_ = "cardOutline")   

    jobs = {}

    for item in divs:
        a = item.find("a")
        if not a:
            continue

        title = a.get_text(strip=True)
        job_link = a.get("href")
        url = f"https://www.indeed.com{job_link}"
        jobs[url] = title
        # jobs.setdefault(url, []).append(title)
           
       
    return(jobs)