import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from main_final import get_compamny_data


def worker(row, col1, col2):
    try:
        return get_compamny_data(row[col1], row[col2])
    except Exception as e:
        return {"error": str(e)}


def process_excel(input_file, output_file):
    df = pd.read_excel(input_file)
    result = {}

    # keep original columns
    for col in df.columns:
        result[col] = []

    rows = list(df.iterrows())
    col1, col2 = df.columns[0], df.columns[1]
    outputs = [None] * len(rows)

    MAX_WORKERS = 5

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(worker, row, col1, col2): idx
            for idx, (_, row) in enumerate(rows)
        }

        for future in as_completed(futures):
            idx = futures[future]
            outputs[idx] = future.result()

    # assemble results (CORRECTLY ALIGNED)
    for i, (_, row) in enumerate(rows):
        # original columns
        for col in df.columns:
            result[col].append(row[col])

        out = outputs[i] or {}

        # pad existing dynamic columns for this row
        for k in result:
            if k not in df.columns and k not in out:
                result[k].append(None)

        # add / append current row outputs
        for k, v in out.items():
            if k not in result:
                result[k] = [None] * i
            result[k].append(v)

    pd.DataFrame(result).to_excel(output_file, index=False)


process_excel("companies.xlsx", "companies_output_output_FINAL.xlsx")
