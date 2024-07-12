import pandas as pd
import json


def get_json_object_by_row(file_path, row_number):
    try:
        excel_data = pd.read_excel(file_path)

        data = excel_data.to_dict(orient='records')

        if row_number < 1 or row_number > len(data):
            return f"Row number {row_number} is out of range. Valid range is 1 to {len(data)}."

        json_object = data[row_number - 1]

        json_string = json.dumps(json_object, ensure_ascii=False, indent=4)

        return json_string
    except Exception as e:
        return str(e)

