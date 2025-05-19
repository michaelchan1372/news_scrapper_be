import csv
import os
import zipfile

def write_to_text(str, path):
    with open(path, "w", encoding='utf-8-sig') as f:
        f.write(str)

def save_to_csv(news_items, filename, fieldnames, append=False):
    mode = 'w'
    if append:
        mode = 'a'
    # Write to CSV
    with open(filename, mode=mode, newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not append:
            writer.writeheader()
        for item in news_items:
            writer.writerow(item)

def create_folder_if_not_exist(str):
    if not os.path.exists(str):
        os.makedirs(str)
        return True
    return False

def read_from_csv(filename, fieldnames):
    items = []
    with open(filename, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            obj = {}
            for fieldname in fieldnames:
                obj[fieldname] = row[fieldname]
            items.append(obj)
    return items

def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                filepath = os.path.join(root, file)
                # Write file to zip with relative path
                arcname = os.path.relpath(filepath, start=folder_path)
                zipf.write(filepath, arcname)