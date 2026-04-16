import pytesseract
from pdf2image import convert_from_path
import json
import os
import re
import platform

# ---------------- SETUP ----------------
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    POPPLER_PATH = r"C:\poppler\Library\bin"
else:
    pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
    POPPLER_PATH = None

data = []
id_counter = 1

pdf_folder = "data/pdfs"


# ---------------- CLEAN TEXT ----------------
def clean(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ---------------- PROCESS PDFs ----------------
for file in os.listdir(pdf_folder):
    if file.endswith(".pdf"):
        print(f"Processing: {file}")

        path = os.path.join(pdf_folder, file)

        pages = convert_from_path(path, poppler_path=POPPLER_PATH) if POPPLER_PATH else convert_from_path(path)

        full_text = ""

        for page in pages:
            full_text += pytesseract.image_to_string(page)

        # 🔥 IMPROVED SPLITTING
        full_text = full_text.replace("\n", " ")

        # Try better extraction strategy
        parts = re.split(r'abstract[:\-]?', full_text, flags=re.IGNORECASE)

        if len(parts) < 2:
            continue

        title = clean(parts[0][:100])
        abstract = clean(parts[1][:500])

        # 🔥 FILTER BAD DATA
        if len(title) < 5 or len(abstract) < 30:
            continue

        if "copyright" in abstract or "introduction" not in abstract:
            continue

        data.append({
            "id": id_counter,
            "title": title,
            "abstract": abstract
        })

        id_counter += 1


# ---------------- SAVE ----------------
os.makedirs("data", exist_ok=True)

with open("data/projects.json", "w") as f:
    json.dump(data, f, indent=4)

print("✅ Dataset created successfully with improved extraction!")