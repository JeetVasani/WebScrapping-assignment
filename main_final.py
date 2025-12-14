from utils import (
    get_first_link_on_search,
    extract_links,
    indeed_jobs,
    get_html_from_url
)
from get_job_utils import extract_jobs_from_listing


career_page_keywords = [
    "careers", "career", "join us", "joinus",
    "opportunities", "open positions",
    "openings", "vacancies", "hiring"
]

job_page_keywords = [
    "jobs", "job", "openings",
    "positions", "apply", "/job"
]

ats_keywords = ["personio","teamtailor", "lever", "greenhouse",]


# -------------------- HELPERS --------------------

def normalize_url(x):
    if isinstance(x, dict):
        return x.get("url")
    return x


def get_compamny_data(name, desc):
    print(f"SEARCHING INFO FOR COMPANY : {name}\n")

    query = f"{name} {desc}"

    # ---------------- COMPANY WEBSITE ----------------
    company_res = get_first_link_on_search(query + " official website", True)
    COMPANY_URL = company_res["url"]
    COMPANY_WEBSITE_HTML = company_res["html_str"]

    # ---------------- LINKEDIN ----------------
    COMPANY_LINKDEN = extract_links(
        html_str=COMPANY_WEBSITE_HTML,
        base_url=COMPANY_URL,
        to_extract="linkedin",
        multiple_strings_to_extract=False,
        number_of_matches_to_find=1
    )
    COMPANY_LINKDEN = normalize_url(COMPANY_LINKDEN)

    if not COMPANY_LINKDEN:
        COMPANY_LINKDEN = get_first_link_on_search(query + " linkedin", False)

    # ---------------- CAREER PAGE ----------------
    COMPANY_CARRER_PAGE = extract_links(
        html_str=COMPANY_WEBSITE_HTML,
        base_url=COMPANY_URL,
        to_extract=career_page_keywords,
        multiple_strings_to_extract=True,
        number_of_matches_to_find=1
    )
    COMPANY_CARRER_PAGE = normalize_url(COMPANY_CARRER_PAGE)

    if not COMPANY_CARRER_PAGE:
        COMPANY_CARRER_PAGE = get_first_link_on_search(query + " careers page", False)

    COMPANY_CARRER_PAGE_HTML = get_html_from_url(COMPANY_CARRER_PAGE)

    
    # ISSUE : WRONG JOB PAGE IS BEING EXCTRACTED

    # ---------------- ATS DETECTION ----------------
    ATS_PAGE = extract_links(
        html_str=COMPANY_CARRER_PAGE_HTML,
        base_url=COMPANY_CARRER_PAGE,
        to_extract=ats_keywords,
        multiple_strings_to_extract=True,
        number_of_matches_to_find=1
    )

    ATS_PAGE = normalize_url(ATS_PAGE)
    print("ATS PAGE:---->",ATS_PAGE)
    if ATS_PAGE:
        COMPANY_JOB_PAGE = ATS_PAGE
        COMPANY_JOB_PAGE_HTML = get_html_from_url(ATS_PAGE)
    # else:
    #     COMPANY_JOB_PAGE = extract_links(
    #         html_str=COMPANY_CARRER_PAGE_HTML,
    #         base_url=COMPANY_CARRER_PAGE,
    #         to_extract=job_page_keywords,
    #         multiple_strings_to_extract=True,
    #         number_of_matches_to_find=1
    #     )
    #     COMPANY_JOB_PAGE = normalize_url(COMPANY_JOB_PAGE)
    else:
        COMPANY_JOB_PAGE = None

    if not COMPANY_JOB_PAGE:
        COMPANY_JOB_PAGE = COMPANY_CARRER_PAGE
        COMPANY_JOB_PAGE_HTML = COMPANY_CARRER_PAGE_HTML
    else:
        COMPANY_JOB_PAGE_HTML = get_html_from_url(COMPANY_JOB_PAGE)

    # ---------------- INTERNAL JOB EXTRACTION ----------------
    INTERNAL_JOBS = extract_jobs_from_listing(
        COMPANY_JOB_PAGE,
        COMPANY_JOB_PAGE_HTML,
        limit=3
    )

    # ---------------- PORTAL FALLBACK (USING get_ext_job) ----------------
    if len(INTERNAL_JOBS) < 3:
        needed = 3 - len(INTERNAL_JOBS)
        EXT_JOBS = indeed_jobs(name)

        count = 0
        for url,title in EXT_JOBS.items():
                if title == None: continue 

                # job = {url: title}
                INTERNAL_JOBS.append({
                        "url": url,
                        "title": title
                    })
                # print(title)
                count += 1

                if count == needed: break

    # ---------------- NORMALIZE TO 3 JOBS ----------------
    def get_job(i):
        if i < len(INTERNAL_JOBS):
            return INTERNAL_JOBS[i]["url"], INTERNAL_JOBS[i]["title"]
        return None, None

    JOB_1, JOB_1_TITLE = get_job(0)
    JOB_2, JOB_2_TITLE = get_job(1)
    JOB_3, JOB_3_TITLE = get_job(2)
    
    if not INTERNAL_JOBS:
        print(f"No valid job postings found for {name}")

    # ---------------- FINAL OUTPUT ----------------
    return {
        "Website URL": COMPANY_URL,
        "Linkedin URL": COMPANY_LINKDEN,
        "Careers Page URL": COMPANY_CARRER_PAGE,
        "Job Page URL": COMPANY_JOB_PAGE,
        "Job post1": JOB_1,
        "Job title1": JOB_1_TITLE,
        "Job post2": JOB_2,
        "Job title2": JOB_2_TITLE,
        "Job post3": JOB_3,
        "Job title3": JOB_3_TITLE,
    }

# name = 'Climate Bonds Initiative'
# desc = 'Mobilizing $100 trillion bond market for global climate solutions.'
# print(get_compamny_data(name, desc))
