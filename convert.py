import pytesseract
from pdf2image import convert_from_path
import json
import os
import re

# 🔴 Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

data = []
id_counter = 1

def clean(text):
    return re.sub(r'\s+', ' ', text).strip()

pdf_folder = r"E:\GITHUB\project-collision-avoidance-system\data\pdfs"

for file in os.listdir(pdf_folder):
    if file.endswith(".pdf"):

        print(f"\n📄 Processing file: {file}")

        path = os.path.join(pdf_folder, file)

        pages = convert_from_path(
            path,
            poppler_path=r"E:\poppler-25.12.0\Library\bin"
        )

        full_text = ""

        for i, page in enumerate(pages):
            print(f"   👉 Page {i+1}")
            text = pytesseract.image_to_string(page)
            full_text += "\n" + text

        sections = full_text.split("ABSTRACT")

        for section in sections[1:]:
            lines = section.strip().split("\n")

            if len(lines) > 2:
                title = clean(lines[0])
                abstract = clean(" ".join(lines[1:6]))

                # 🔴 FILTER BAD DATA
                if len(title) < 10:
                    continue
                if len(abstract) < 50:
                    continue

                data.append({
                    "id": id_counter,
                    "title": title,
                    "abstract": abstract
                })

                id_counter += 1

# Save JSON
with open("data/projects.json", "w") as f:
    json.dump(data, f, indent=4)

print("\n✅ Clean OCR Conversion completed!")