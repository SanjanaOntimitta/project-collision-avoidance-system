import pytesseract
from pdf2image import convert_from_path
import json
import os
import re
import platform

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    POPPLER_PATH = r"C:\poppler\Library\bin"
else:
    pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
    POPPLER_PATH = None

data = []
id_counter = 1


# 🔥 CLEANER VERSION (IMPORTANT)
def clean(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


pdf_folder = "data/pdfs"

for file in os.listdir(pdf_folder):
    if file.endswith(".pdf"):
        print(f"Processing {file}")

        path = os.path.join(pdf_folder, file)

        if POPPLER_PATH:
            pages = convert_from_path(path, poppler_path=POPPLER_PATH)
        else:
            pages = convert_from_path(path)

        full_text = ""

        for page in pages:
            full_text += pytesseract.image_to_string(page)

        sections = full_text.split("ABSTRACT")

        for section in sections[1:]:
            lines = section.strip().split("\n")

            if len(lines) > 2:
                title = clean(lines[0])
                abstract = clean(" ".join(lines[1:6]))

                if len(title) < 5 or len(abstract) < 20:
                    continue

                data.append({
                    "id": id_counter,
                    "title": title,
                    "abstract": abstract
                })

                id_counter += 1


os.makedirs("data", exist_ok=True)

with open("data/projects.json", "w") as f:
    json.dump(data, f, indent=4)

print("✅ Dataset created successfully")