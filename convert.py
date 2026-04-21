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


def is_valid_entry(title, abstract):
    combined = f"{title} {abstract}"

    if len(title) < 10 or len(abstract) < 80:
        return False

    if len(title.split()) < 3 or len(abstract.split()) < 15:
        return False

    if title.startswith(".") or any(symbol in combined for symbol in ["|", ";"]):
        return False

    alpha_chars = sum(ch.isalpha() for ch in combined)
    if alpha_chars < max(40, int(len(combined) * 0.6)):
        return False

    return True


# ---------------- PROCESS PDFs ----------------
if not os.path.isdir(pdf_folder):
    raise FileNotFoundError(f"PDF folder not found: {pdf_folder}")

for file in sorted(os.listdir(pdf_folder)):
    if file.endswith(".pdf"):
        print(f"Processing: {file}")

        path = os.path.join(pdf_folder, file)

        try:
            pages = convert_from_path(path, poppler_path=POPPLER_PATH) if POPPLER_PATH else convert_from_path(path)
        except Exception as exc:
            print(f"Skipping {file}: unable to render PDF ({exc})")
            continue

        full_text = ""

        for page in pages:
            try:
                full_text += pytesseract.image_to_string(page)
            except Exception as exc:
                print(f"Skipping {file}: OCR failed ({exc})")
                full_text = ""
                break

        if not full_text.strip():
            continue

        # 🔥 IMPROVED SPLITTING
        full_text = full_text.replace("\n", " ")

        # Try better extraction strategy
        parts = re.split(r'abstract[:\-]?', full_text, flags=re.IGNORECASE)

        if len(parts) < 2:
            continue

        title = clean(parts[0][:100])
        abstract = clean(parts[1][:500])

        # 🔥 FILTER BAD DATA
        if "copyright" in abstract or "introduction" not in abstract:
            continue

        if not is_valid_entry(title, abstract):
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
