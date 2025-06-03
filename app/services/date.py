import re
def find_date(text):
    # Regex to match dd/mm/yyyy or dd-mm-yyyy
    date_pattern = r'\b(?:\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4})\b'
    dates = re.findall(date_pattern, text)
    return dates