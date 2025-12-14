from utils import get_html_from_url, extract_links,indeed_jobs
from get_job_utils import extract_jobs_from_listing,extract_generic_jobs



# outcome = extract_links(
#     html_str = html, 
#     base_url = url,
#     to_extract =  to_exctract,
#     number_of_matches_to_find = 3,
#     multiple_strings_to_extract=True)

name = 'Climate Bonds Initiative'
outcome = indeed_jobs(name,3)

print(outcome) 
    