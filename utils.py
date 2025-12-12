import os
import requests
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse, parse_qs, unquote, urlunparse, urlencode

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
job_patterns = [
            "/jobs/",
            "/job/",
            "/positions/",
            "/position/",
            "/careers/",
            "/opening/",
            "/vacancy/",
            "/opportunity/"
        ]

_session = requests.Session()

def get_html_from_url(url: str) -> str:
    if not API_KEY:
        return ""

    try:
        r = _session.get(
            "http://api.scraperapi.com",
            params={
                "api_key": API_KEY,
                "url": url,
            },
            timeout=15,
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
            ).text

            return {
                "url": final_url,
                "html_str": real_html
            }

        return clean_url(final_url)

def extract_links(html_str, base_url, to_extract, number_of_matches_to_find=1, multiple_strings_to_extract=False):
    soup = BeautifulSoup(html_str, "html.parser")
    matches = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        anchor_text = a.get_text(strip=True)
        text_lower = anchor_text.lower()
        full_url = urljoin(base_url, href)

        hit = False

        if multiple_strings_to_extract:
            for term in to_extract:
                t = term.lower()
                if t in href.lower() or t in text_lower:
                    hit = True
                    break
        else:
            t = to_extract.lower()
            if t in href.lower() or t in text_lower:
                hit = True

        if hit:
            matches.append(full_url)

            if len(matches) >= number_of_matches_to_find:
                break

    if number_of_matches_to_find == 1:
        return matches[0] if matches else None

    return matches

# def is_job_posting(url: str, timeout: int = 15) -> bool:
#     url_l = url.lower()

#     # 1. ATS hard allow (deterministic)
#     ATS_PATTERNS = [
#         r"/jobs/\d+-",                          # Teamtailor
#         r"greenhouse\.io/.*/jobs/\d+",          # Greenhouse
#         r"lever\.co/.+/\d+",                    # Lever
#         r"workdayjobs\.com/.+/job/",            # Workday
#         r"personio\.com/job/",                  # Personio
#     ]

#     for p in ATS_PATTERNS:
#         if re.search(p, url_l):
#             return True

#     # 2. Fetch page
#     try:
#         r = requests.get(
#             url,
#             timeout=timeout,
#             headers={"User-Agent": "Mozilla/5.0"}
#         )
#         if r.status_code != 200:
#             return False
#     except Exception:
#         return False

#     html = r.text
#     soup = BeautifulSoup(html, "html.parser")
#     text = soup.get_text(" ", strip=True).lower()

#     score = 0

#     # 3. Single job title signal
#     if len(soup.find_all("h1")) == 1:
#         score += 1

#     # 4. Job specific language
#     if any(k in text for k in [
#         "responsibilities",
#         "requirements",
#         "qualifications",
#         "job description",
#         "role overview",
#     ]):
#         score += 1

#     # 5. Apply action (exactly one)
#     apply_elems = soup.find_all(
#         ["a", "button"],
#         string=lambda s: s and "apply" in s.lower()
#     )
#     if len(apply_elems) == 1:
#         score += 1

#     # 6. Listing page blockers
#     if not any(k in text for k in [
#         "view all jobs",
#         "open positions",
#         "search jobs",
#         "filter by",
#         "job listings",
#     ]):
#         score += 1

#     # 7. Page size sanity
#     if len(text) < 15000:
#         score += 1

#     return score >= 3

def is_job_posting(url: str, timeout: int = 10) -> bool:
    url_l = url.lower()

    # 1. ATS hard allow (deterministic)
    ATS_PATTERNS = [
        r"/jobs/\d+-",                          # Teamtailor
        r"greenhouse\.io/.*/jobs/\d+",          # Greenhouse
        r"lever\.co/.+/\d+",                    # Lever
        r"workdayjobs\.com/.+/job/",            # Workday
        r"personio\.com/job/",                  # Personio
    ]
    for p in ATS_PATTERNS:
        if re.search(p, url_l):
            return True

    # 2. Fetch page
    try:
        r = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if r.status_code != 200:
            return False
    except Exception:
        return False

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    # 3. Extract title candidates
    candidates = []

    for h1 in soup.find_all("h1"):
        t = h1.get_text(strip=True)
        if 3 <= len(t) <= 120:
            candidates.append(t)

    for attr, key in [("property", "og:title"), ("name", "twitter:title")]:
        tag = soup.find("meta", {attr: key})
        if tag and tag.get("content"):
            t = tag["content"].strip()
            if 3 <= len(t) <= 120:
                candidates.append(t)

    if soup.title:
        t = soup.title.get_text(strip=True)
        if 3 <= len(t) <= 120:
            candidates.append(t)

    if not candidates:
        return False

    # 4. Title validation (THIS blocks FSC-like pages)
    ROLE_KEYWORDS = [
        "engineer","developer","manager","analyst","designer",
        "intern","lead","director","officer","coordinator",
        "specialist","consultant","associate"
    ]

    TITLE_BLACKLIST = [
        "awareness","search","certificate","data","report",
        "publication","policy","resource","tool","campaign",
        "initiative","program"
    ]

    valid_title = False
    for title in candidates:
        t_l = title.lower()

        if not any(r in t_l for r in ROLE_KEYWORDS):
            continue

        if any(b in t_l for b in TITLE_BLACKLIST):
            continue

        valid_title = True
        break

    if not valid_title:
        return False

    # 5. Heuristic page checks
    score = 0

    if len(soup.find_all("h1")) <= 2:
        score += 1

    if any(k in text for k in [
        "responsibilities",
        "requirements",
        "qualifications",
        "job description",
    ]):
        score += 1

    apply_elems = soup.find_all(
        ["a", "button"],
        string=lambda s: s and "apply" in s.lower()
    )
    if len(apply_elems) == 1:
        score += 1

    if not any(k in text for k in [
        "view all jobs",
        "search jobs",
        "open positions",
        "filter by",
    ]):
        score += 1

    if len(text) < 15000:
        score += 1

    return score >= 3



def extract_job_title(url: str, timeout: int = 15) -> str:
    try:
        r = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if r.status_code != 200:
            return ""
    except Exception:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")

    # 1. Strongest signal: single H1
    h1_tags = soup.find_all("h1")
    if len(h1_tags) == 1:
        title = h1_tags[0].get_text(strip=True)
        if title:
            return title

    # 2. Common job-title classes / attributes
    selectors = [
        '[data-testid*="job"]',
        '[class*="job-title"]',
        '[class*="position"]',
        '[class*="role"]',
        '[id*="job"]',
        '[id*="position"]',
    ]

    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            if 3 <= len(text) <= 120:
                return text

    # 3. Title tag fallback (cleaned)
    if soup.title:
        title = soup.title.get_text(strip=True)

        # Remove common junk
        for junk in [
            "careers",
            "jobs",
            "job",
            "openings",
            "at ",
            "|",
            "-",
        ]:
            title = title.replace(junk, "").strip()

        if 3 <= len(title) <= 120:
            return title

    return ""

def get_ext_job(company_name: str, number_of_jobs: int):
    job_sites = ["indeed.com", "linkedin.com/jobs", "glassdoor.com"]
    seen_jobs = set()
    results = []

    for site in job_sites:
        if len(results) >= number_of_jobs:
            break

        try:
            query = f"{company_name} jobs site:{site}"
            url = get_first_link_on_search(query, False)
        except Exception:
            continue

        if not isinstance(url, str):
            continue

        url_l = url.lower()

        if site.split(".")[0] not in url_l:
            continue

        if url in seen_jobs:
            continue

        seen_jobs.add(url)
        results.append(url)

    return results

def commented():
    # simpler version for simple cases
# def get_first_link_in_html_page(html_str, base_url, keyword):
#     soup = BeautifulSoup(html_str, "html.parser")
#     keyword = keyword.lower()

#     for a in soup.find_all("a", href=True):
#         href = a["href"].strip()
#         text = a.get_text(strip=True)

#         if keyword in href.lower() or keyword in text.lower():
#             return urljoin(base_url, href)

#     return None
# def extract_job_posts(html_str, base_url, max_jobs=2):
#     soup = BeautifulSoup(html_str, "html.parser")
#     results = []

#     # scan all anchors
#     for a in soup.find_all("a", href=True):
#         href = a["href"].strip()
#         text = a.get_text(strip=True)

#         if not text or not href:
#             continue

#         # URL must look like a job post
#         href_l = href.lower()
#         if any(k in href_l for k in ["job", "careers", "open", "position", "vacanc"]):
#             job = {
#                 "title": clean_title(text),
#                 "url": urljoin(base_url, href)
#             }
#             results.append(job)

#             if len(results) == max_jobs:
#                 break

#     return results

# def clean_title(text):
#     # remove junk words commonly found on listing links
#     junk = ["apply", "apply now", "learn more", "view details", "careers", "jobs"]
#     t = text
#     for j in junk:
#         if t.lower().startswith(j):
#             t = t[len(j):].strip(" -:|")
#     return t

# def format_jobs(job_list):
#         formatted = []
#         for j in job_list:
#             clean_text = " ".join(j["title"].split())  # collapse spaces/newlines
#             formatted.append(f"URL: {j['url']}\nTitle: {clean_text}")
#         return "\n\n".join(formatted)



# def genrate_company_data(company_name, company_desc):
#     print(f"---------------------------->COLLECTING COMPANY DATA FOR: {company_name} ....")
#     company_info = [company_name, company_desc]
#     short_desc = company_desc.partition("\n")[0]
#     query = company_name + short_desc


#     # ------------------->GET COMPANY URL FROM ONLINE SEARCH<-------------------
#     company_url_with_html = (get_first_link_on_search(query, True))
#     company_url = company_url_with_html["url"]
#     company_url_html_content = company_url_with_html["html_str"]
#     company_info.append(company_url)

#     # ------------------->TRY SCRAPPING COMPANY LINKDEN URL FROM WEBSITE<-------------------
#     # LinkedIn
#     linkedn_link = extract_from_html(company_url_html_content, company_url, "linkedin.com", False, 1)

#     # ------------------->FALLBACK: SEACH COMPANY LINKDEN URL ONLINE<-------------------
#     if linkedn_link is None:
#         print("Finding linkend url online")
#         to_find = query + " linkedin.com"
#         linkedn_link = (get_first_link_on_search(to_find, False))
#         company_info.append(linkedn_link)
        
#     else:
#         linkedn_link = linkedn_link['url']


#     # ------------------->TRY SCRAPPING COMPANY CARRER PAGE URL FROM WEBSITE<-------------------
#     # Career page
#     carrer_link = extract_from_html(company_url_html_content, company_url, career_keywords, True, 1)
#     # Fetch career page HTML
#     career_html = requests.get(
#         "http://api.scraperapi.com",
#         params={"api_key": API_KEY, "url": carrer_link},
#     ).text

#     # ------------------->FALLBACK: SEACH COMPANY CARRER PAGE URL ONLINE<-------------------
#     if carrer_link == None:
#         print("Finding carrer page url online")
#         to_find = query + " official career page"
#         # carrer_link = (get_first_link_on_search(to_find, False))
#         carrer_link_with_html = (get_first_link_on_search(to_find, True))
#         carrer_link = carrer_link_with_html['url']
#         career_html = carrer_link_with_html['html_str']

#     company_info.append(carrer_link)

#     print("CARRER LINK -->",carrer_link)

#     # ------------------->TRY SCRAPPING JOB POSTING PAGE URL FROM CARRER PAGE<-------------------
#     job_listing_page = (extract_from_html(to_extract = JOB_KEYWORDS,base_url = carrer_link,html_str = career_html,multiple_strings_to_extract=True,number_of_matches_to_find=2))#--->?<----
#     print("JOB LISTING PAGE ",job_listing_page)
    
#     # ------------------->COMANY MIGHT HAVE JOB LISTING PAGE = CARRER PAGE<-------------------
#     if not job_listing_page:
#         job_listing_page = carrer_link
#         company_info.append(job_listing_page)
#         print("JOB LISTING PAGE-->" ,job_listing_page)
#     else:
#         print(type(job_listing_page))
#         job_listing_page = job_listing_page[0]["url"] 
#         job_listing_page = clean_url.clean_url(job_listing_page)
#         company_info.append(job_listing_page)
#         print("JOB LISTING PAGE-->" ,job_listing_page)
        


#     # ------------------->GET HTML STRING FOR JOB LISTING PAGE WEBSITE TO EXCTRACT INDIVISUAL JOB<-------------------
#     job_listing_html_str = requests.get(
#         "http://api.scraperapi.com",
#         params={"api_key": API_KEY, "url": job_listing_page},
#     ).text

#     # ------------------->EXCTRACT INDIVISUAL JOBS FROM JOB LISTING PAGE<-------------------
#     job_listing = extract_job_posts(job_listing_html_str, job_listing_page, max_jobs=2)

#     for j in job_listing:
#         if isinstance(j, dict) and "url" in j:
#             j["url"] = clean_url.clean_url(j["url"])


#     formated_jobs_listings = format_jobs(job_listing)
#     company_info.append(formated_jobs_listings)
#     print("FORMATED JOBS LISTING-->",formated_jobs_listings)

    
#     print("FINDING JOBS ON OTHER PORTALS")

#     # ------------------->JOB LISTING FROM EXTERNAL JOB SITES FROM WEBSITE<-------------------
#     for i in range(3 - len(job_listing)):
#         ext_job = (get_ext_job(query))
#         for j in ext_job:
#             if isinstance(j, dict) and "url" in j:
#                 j["url"] = clean_url.clean_url(j["url"])
#                 job_listing_html_str = requests.get(
#                         "http://api.scraperapi.com",
#                         params={"api_key": API_KEY, "url": j["url"]},
#                     ).text
                
#                 # html_str: str, base_url: str, to_extract, multiple_strings_to_extract: bool, number_of_matches_to_find: int
#                 job_listing = extract_from_html(
#                     html_str = job_listing_html_str,
#                     base_url =  j["url"],
#                     to_extract = job_patterns,
#                     multiple_strings_to_extract = True,
#                     number_of_matches_to_find = 1)
#         company_info.append({ext_job:job_listing})
    
#     print(company_info)
#     print(f"---------------------------->COLLECTED COMPANY DATA FOR: {company_name} ....")
#     return (company_info)

# def genrate_company_data(company_name, company_desc):
#     print(f"---------------------------->COLLECTING COMPANY DATA FOR: {company_name} ....")

#     # CHANGED: list → dict with a raw list to store appended values
#     company_info = {
#         "name": company_name,
#         "desc": company_desc,
#         "raw": []
#     }

#     short_desc = company_desc.partition("\n")[0]
#     query = company_name + short_desc


#     # ------------------->GET COMPANY URL FROM ONLINE SEARCH<-------------------
#     company_url_with_html = (get_first_link_on_search(query, True))
#     company_url = company_url_with_html["url"]
#     company_url_html_content = company_url_with_html["html_str"]
#     company_info["raw"].append(company_url)


#     # ------------------->TRY SCRAPPING COMPANY LINKDEN URL FROM WEBSITE<-------------------
#     linkedn_link = extract_from_html(company_url_html_content, company_url, "linkedin.com", False, 1)

#     # ------------------->FALLBACK: SEACH COMPANY LINKDEN URL ONLINE<-------------------
#     if linkedn_link is None:
#         print("Finding linkend url online")
#         to_find = query + " linkedin.com"
#         linkedn_link = (get_first_link_on_search(to_find, False))
#         company_info["raw"].append(linkedn_link)
#     else:
#         linkedn_link = linkedn_link['url']


#     # ------------------->TRY SCRAPPING COMPANY CARRER PAGE URL FROM WEBSITE<-------------------
#     carrer_link = extract_from_html(company_url_html_content, company_url, career_keywords, True, 1)

#     # Fetch career page HTML
#     career_html = requests.get(
#         "http://api.scraperapi.com",
#         params={"api_key": API_KEY, "url": carrer_link},
#     ).text

#     # ------------------->FALLBACK: SEACH COMPANY CARRER PAGE URL ONLINE<-------------------
#     if carrer_link == None:
#         print("Finding carrer page url online")
#         to_find = query + " official career page"
#         carrer_link_with_html = (get_first_link_on_search(to_find, True))
#         carrer_link = carrer_link_with_html['url']
#         career_html = carrer_link_with_html['html_str']

#     company_info["raw"].append(carrer_link)

#     print("CARRER LINK -->", carrer_link)


#     # ------------------->TRY SCRAPPING JOB POSTING PAGE URL<-------------------
#     job_listing_page = (
#         extract_from_html(
#             to_extract=JOB_KEYWORDS,
#             base_url=carrer_link,
#             html_str=career_html,
#             multiple_strings_to_extract=True,
#             number_of_matches_to_find=2
#         )
#     )
#     print("JOB LISTING PAGE ", job_listing_page)

#     if not job_listing_page:
#         job_listing_page = carrer_link
#         company_info["raw"].append(job_listing_page)
#         print("JOB LISTING PAGE-->", job_listing_page)
#     else:
#         job_listing_page = job_listing_page[0]["url"]
#         job_listing_page = clean_url.clean_url(job_listing_page)
#         company_info["raw"].append(job_listing_page)
#         print("JOB LISTING PAGE-->", job_listing_page)


#     # ------------------->GET JOB LISTING HTML<-------------------
#     job_listing_html_str = requests.get(
#         "http://api.scraperapi.com",
#         params={"api_key": API_KEY, "url": job_listing_page},
#     ).text


#     # ------------------->EXTRACT INTERNAL JOBS<-------------------
#     job_listing = extract_job_posts(job_listing_html_str, job_listing_page, max_jobs=2)

#     for j in job_listing:
#         if isinstance(j, dict) and "url" in j:
#             j["url"] = clean_url.clean_url(j["url"])

#     formated_jobs_listings = format_jobs(job_listing)
#     company_info["raw"].append(formated_jobs_listings)

#     print("FORMATED JOBS LISTING-->", formated_jobs_listings)


#     print("FINDING JOBS ON OTHER PORTALS")


#     # ------------------->EXTERNAL JOBS<-------------------
#     for i in range(3 - len(job_listing)):
#         ext_job = (get_ext_job(query))

#         for j in ext_job:
#             if isinstance(j, dict) and "url" in j:
#                 j["url"] = clean_url.clean_url(j["url"])
#                 job_listing_html_str = requests.get(
#                         "http://api.scraperapi.com",
#                         params={"api_key": API_KEY, "url": j["url"]},
#                     ).text

#                 job_listing = extract_from_html(
#                     html_str=job_listing_html_str,
#                     base_url=j["url"],
#                     to_extract=job_patterns,
#                     multiple_strings_to_extract=True,
#                     number_of_matches_to_find=1
#                 )

#         company_info["raw"].append({"source": ext_job, "jobs": job_listing})



#     print(company_info)



# name = "Polestar"

# # name = "Unison Infrastructure"
# desc = "Driving society forward with uncompromised electric performance and progressive innovation."

# genrate_company_data(name, desc)
    pass