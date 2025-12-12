from utils import get_first_link_on_search, extract_links, get_ext_job, get_html_from_url, is_job_posting, extract_job_title

"""
Output must be in form [dict]
{
    "website": f"{name}_site",
    "description": f"{desc}",
    "linkedin": f"{name}_linkedin",
    "job1": f"{name}_job1",

    Website URL,Linkedin URL,Careers Page URL,
    Job listings page URL,job post1 URL,job post1 title,job post2 URL,job post2 title,job post3 URL,job post3 title
}
"""
career_page_keywords = ["careers","career","join us","joinus","opportunities","open positions","openings","vacancies","hiring"]
job_page_keywords = ["open positions","jobs_list" ,"jobs", "job", "openings", "positions", "listings", "opportunities", "search", "apply", "join us", "work with us", "hiring",
                     "/job"]

def get_compamny_data(name, desc):
    print(f'SEARCHING INFO FOR COMPANY : {name}\n\n')

    query = name + desc
    # ---------------------------COMPANY WEBSITE DATA---------------------------
    COMPANY_URL_WITH_HTML = get_first_link_on_search(query + " official website",True)
    COMPANY_URL = COMPANY_URL_WITH_HTML['url']
    COMPANY_WEBSITE_HTML = COMPANY_URL_WITH_HTML['html_str']

    # ---------------------------COMPANY LINKDEN DATA---------------------------
    COMPANY_LINKDEN = extract_links(
        html_str = COMPANY_WEBSITE_HTML,
        base_url = COMPANY_URL,
        to_extract = "linkedin",
        number_of_matches_to_find = 1,
        multiple_strings_to_extract = False
    )
    if not COMPANY_LINKDEN:
        # print('FINDING LINKDEN ONLINE')
        COMPANY_LINKDEN = get_first_link_on_search(query + " linkedin", False)

    # ---------------------------COMPANY CARRER PAGE DATA---------------------------
    COMPANY_CARRER_PAGE = extract_links(
        html_str = COMPANY_WEBSITE_HTML,
        base_url = COMPANY_URL,
        to_extract = career_page_keywords,
        multiple_strings_to_extract = True,
        number_of_matches_to_find = 1
    )
    if not COMPANY_CARRER_PAGE:
        # print('FINDING CARRER PAGE ONLINE')
        COMPANY_CARRER_PAGE = get_first_link_on_search(query + " official carrers page", False)

    COMPANY_CARRER_PAGE_HTML = get_html_from_url(COMPANY_CARRER_PAGE)

    # ---------------------------COMPANY JOBS PAGE DATA---------------------------
    COMPANY_JOB_PAGE = extract_links(
        html_str = COMPANY_CARRER_PAGE_HTML,
        base_url = COMPANY_CARRER_PAGE,
        to_extract = job_page_keywords,
        multiple_strings_to_extract = True,
        number_of_matches_to_find = 1
    )
    if not COMPANY_JOB_PAGE:
        # print('FINDING JOB PAGE ONLINE')
        COMPANY_JOB_PAGE = get_first_link_on_search(query + " official job posting", False)

    COMPANY_JOB_PAGE_HTML = get_html_from_url(COMPANY_JOB_PAGE)

    # ---------------------------COMPANY JOBS PAGE DATA---------------------------
    INITIAL_JOB_POSTINGS = extract_links(
        html_str = COMPANY_JOB_PAGE_HTML,
        base_url = COMPANY_JOB_PAGE,
        to_extract = job_page_keywords,
        multiple_strings_to_extract = True,
        number_of_matches_to_find = 3
    )
    JOB_POSTINGS = []
    for i in range(len(INITIAL_JOB_POSTINGS)):
        if(is_job_posting(INITIAL_JOB_POSTINGS[i]) and INITIAL_JOB_POSTINGS[i] != COMPANY_JOB_PAGE):
            # print(f"JOB {[i]} -- ", INITIAL_JOB_POSTINGS[i])
            JOB_POSTINGS.append(INITIAL_JOB_POSTINGS[i])
        # else:
            # print(f'INVALID POSTING:{INITIAL_JOB_POSTINGS[i]}')


    # ---------------------------BACKUP: JOBS ON EXTERNAL SITES---------------------------
    num_of_ext_job_to_find = 3 - len(JOB_POSTINGS)

    if num_of_ext_job_to_find > 0:
        EXT_JOBS = get_ext_job(name, num_of_ext_job_to_find)
        for url in EXT_JOBS:
            # JOB_POSTINGS.append({"url": url})
            JOB_POSTINGS.append(url)

    # -------------------------NEED TO EXCTRACT TITLES-------------------------
    JOB_1 = JOB_POSTINGS[0] if len(JOB_POSTINGS) > 0 else None
    JOB_2 = JOB_POSTINGS[1] if len(JOB_POSTINGS) > 1 else None
    JOB_3 = JOB_POSTINGS[2] if len(JOB_POSTINGS) > 2 else None

    JOB_1_TITLE = extract_job_title(JOB_1) if JOB_1 != None else None
    JOB_2_TITLE = extract_job_title(JOB_2) if JOB_1 != None else None
    JOB_3_TITLE = extract_job_title(JOB_3) if JOB_1 != None else None

    COMPANY_DATA = {
        "Website URL" : COMPANY_URL,
        "Linkedin URL" : COMPANY_LINKDEN,
        "Careers Page URL" : COMPANY_CARRER_PAGE,
        "Job Page URL": COMPANY_JOB_PAGE,
        "Job post1" : JOB_1,
        "Job title1" : JOB_1_TITLE,
        "Job post2" : JOB_2,
        "Job title2" : JOB_2_TITLE,
        "Job post3" : JOB_3,
        "Job title3" : JOB_3_TITLE,
    }
    return COMPANY_DATA

# name = 'Forest Stewardship Council'
# desc = 'Promoting sustainable forestry to combat climate and biodiversity crises globally.'

# print(get_compamny_data(name, desc))