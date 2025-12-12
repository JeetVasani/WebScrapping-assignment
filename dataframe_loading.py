import pandas as pd
from main_final import get_compamny_data

def process_excel(input_file, output_file, row_func):
    df = pd.read_excel(input_file)
    result = {}

    # keep original columns
    for col in df.columns:
        result[col] = []

    # process rows
    for _, row in df.iterrows():
        # store original values
        for col in df.columns:
            result[col].append(row[col])

        # call your processor
        out = row_func(row[df.columns[0]], row[df.columns[1]])

        # store returned keys
        for k, v in out.items():
            if k not in result:
                result[k] = []
            result[k].append(v)

    # pad missing values
    n = len(df)
    for k in result:
        if len(result[k]) < n:
            result[k] += [None] * (n - len(result[k]))

    # save as new excel
    pd.DataFrame(result).to_excel(output_file, index=False)

process_excel("companies.xlsx", "companies_output_file.xlsx", get_compamny_data)