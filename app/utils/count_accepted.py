import pandas as pd


def count_accepted(file_path):
    excel_data = pd.read_excel(file_path)

    empty_count = int(excel_data["Accepted"].isna().sum())
    true_count = int((excel_data["Accepted"] == True).sum())
    false_count = int((excel_data["Accepted"] == False).sum())
    return empty_count, true_count, false_count


print(count_accepted('Updated_Hackathon_nf2024_incubator.xlsx'))
