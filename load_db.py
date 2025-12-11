import pandas as pd
import main

def commented():
#     df = pd.read_excel(input_file)

#     # normalize columns
#     df.columns = [c.strip().lower() for c in df.columns]

#     if "company_name" not in df or "company_description" not in df:
#         raise ValueError("Excel must contain columns: company_name, company_description")

#     # create output columns
#     df["website"] = ""
#     df["company_linkedin"] = ""
#     df["career_page"] = ""
#     df["job_posting_1"] = ""
#     df["job_posting_2"] = ""
#     df["job_posting_3"] = ""

#     for idx, row in df.iterrows():

#         name = str(row["company_name"])
#         desc = str(row["company_description"])

#         print(f"Processing {idx}: {name}")

#         try:
#             data = main.extract_company_data(name, desc)
#         except Exception as e:
#             print(f"Error at row {idx}: {e}")
#             data = {
#                 "website": "",
#                 "linkedin": "",
#                 "career_page": "",
#                 "jobs": ["", "", ""]
#             }

#         # assign into dataframe
#         df.at[idx, "website"] = data["website"]
#         df.at[idx, "company_linkedin"] = data["linkedin"]
#         df.at[idx, "career_page"] = data["career_page"]

#         df.at[idx, "job_posting_1"] = data["jobs"][0]
#         df.at[idx, "job_posting_2"] = data["jobs"][1]
#         df.at[idx, "job_posting_3"] = data["jobs"][2]

#     df.to_excel(output_file, index=False)
#     print("Saved:", output_file)
    pass


import pandas as pd

def process_excel(input_file, output_file):
    df = pd.read_excel(input_file)

    # normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    if "company_name" not in df or "company_description" not in df:
        raise ValueError("Excel must contain columns: company_name, company_description")

    # create output columns if they don't exist
    output_cols = [
        "website",
        "linkedin",
        "career_page",
        "job_posting_1",
        "job_posting_2",
        "job_posting_3"
    ]

    for col in output_cols:
        if col not in df:
            df[col] = ""

    # process each row
    for idx, row in df.iterrows():
        name = str(row["company_name"])
        desc = str(row.get("company_description", ""))

        try:
            data = main.extract_company_data(name, desc)
        except Exception as e:
            print(f"Error on row {idx} ({name}): {e}")
            data = {
                "website": "",
                "linkedin": "",
                "career_page": "",
                "jobs": ["", "", ""]
            }

        df.at[idx, "website"] = data["website"]
        df.at[idx, "linkedin"] = data["linkedin"]
        df.at[idx, "career_page"] = data["career_page"]

        df.at[idx, "job_posting_1"] = data["jobs"][0]
        df.at[idx, "job_posting_2"] = data["jobs"][1]
        df.at[idx, "job_posting_3"] = data["jobs"][2]

        print(f"{idx}: {name} -> Done")

    df.to_excel(output_file, index=False)
    print("Saved:", output_file)



process_excel("companies_2.xlsx", "new-companies.xlsx")