#!/usr/bin/env python3
import argparse
import json
import re
from collections import OrderedDict
from pathlib import Path

from pypdf import PdfReader


GROUP_NAMES = {
    "1": "Accessories",
    "2": "Front Suspension",
    "3": "Rear Axle",
    "5": "Brakes",
    "6": "Clutch",
    "7": "Cooling",
    "8": "Electrical",
    "9": "Engine",
    "10": "Engine Oiling",
    "11": "Exhaust",
    "13": "Frame",
    "14": "Fuel",
    "15": "Propeller Shaft",
    "16": "Springs",
    "17": "Hood",
    "18": "Standard Parts",
    "19": "Steering",
    "21": "Transmission",
    "22": "Wheels",
    "23": "Body / Interior Trim",
    "24": "Air Conditioning",
}

CODE_RE = re.compile(r"\b([1-9]|1[0-9]|2[0-4])-(\d{2,3})-(\d{1,4})\b")
PART_RE = re.compile(r"\b(\d{4})\s+([A-Z0-9]{3})\b")
NOISE_WORDS = {
    "PAGE",
    "PART",
    "CODE",
    "NUMBER",
    "CATALOG",
    "PASSENGER",
    "PRINTED",
    "MOPAR",
    "CONT",
    "GROUP",
}


def clean_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_part_number(prefix, suffix):
    return f"{prefix}{suffix}".upper()


def description_from_lines(lines, index):
    window = lines[max(0, index - 2) : min(len(lines), index + 3)]
    text = clean_space(" ".join(window))
    text = re.sub(r"\b\d{3,4}\s+[A-Z0-9]{3}\b", " ", text)
    text = re.sub(r"\b([1-9]|1[0-9]|2[0-4])-\d{2,3}-\d{1,4}\b", " ", text)
    text = re.sub(r"\.{2,}", " ", text)
    text = clean_space(text)
    return text[:220]


def looks_like_noise(description):
    if not description:
        return True
    words = re.findall(r"[A-Z]{3,}", description.upper())
    if not words:
        return False
    noisy = sum(1 for word in words if word in NOISE_WORDS)
    return noisy >= max(3, len(words) // 2)


def confidence_for(entry):
    score = 0.55
    if entry.get("code"):
        score += 0.25
    if entry.get("description") and not looks_like_noise(entry["description"]):
        score += 0.15
    if entry.get("source") == "group-page":
        score += 0.05
    return min(round(score, 2), 0.98)


def scan_pdf(pdf_path, page_start=None, page_end=None):
    reader = PdfReader(str(pdf_path))
    start = page_start or 1
    end = page_end or len(reader.pages)
    records = OrderedDict()

    for page_number in range(start, end + 1):
        text = reader.pages[page_number - 1].extract_text() or ""
        raw_lines = [clean_space(line) for line in text.splitlines()]
        lines = [line for line in raw_lines if line]
        current_code = ""

        for line_index, line in enumerate(lines):
            code_match = CODE_RE.search(line)
            if code_match:
                current_code = code_match.group(0)

            for part_match in PART_RE.finditer(line):
                part_number = normalize_part_number(part_match.group(1), part_match.group(2))
                if part_number.startswith("0") or part_number.startswith("1964") or part_number.startswith("1965"):
                    continue

                code = current_code
                tail = line[part_match.end() : part_match.end() + 40]
                inline_code = CODE_RE.search(tail)
                if inline_code:
                    code = inline_code.group(0)

                group = code.split("-", 1)[0] if code else ""
                if group and group not in GROUP_NAMES:
                    continue

                description = description_from_lines(lines, line_index)
                source = "group-page" if page_number < 1289 else "numerical-index"
                key = (part_number, code or "", page_number)

                if key in records:
                    continue

                entry = {
                    "partNumber": part_number,
                    "code": code,
                    "group": group,
                    "groupName": GROUP_NAMES.get(group, ""),
                    "pdfPage": page_number,
                    "description": description,
                    "source": source,
                }
                entry["confidence"] = confidence_for(entry)
                records[key] = entry

    return list(records.values()), len(reader.pages)


def write_catalog_js(entries, output_path, pdf_name, total_pages):
    payload = json.dumps(entries, indent=2, ensure_ascii=False)
    groups = json.dumps(GROUP_NAMES, indent=2)
    output = f"""// Hillbilly Deluxe Mopar Catalog Index
// Generated from {pdf_name}.
// Source PDF pages scanned: {total_pages}
// Records: {len(entries)}

window.MOPAR_CATALOG_INDEX = {payload};

window.MOPAR_GROUP_NAMES = {groups};
"""
    output_path.write_text(output, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build Hillbilly Deluxe Mopar catalog lookup index from a PDF.")
    parser.add_argument("pdf", help="Path to the Mopar parts catalog PDF")
    parser.add_argument("--output", default="catalog-index.js", help="Output JavaScript file")
    parser.add_argument("--page-start", type=int, default=None, help="First PDF page to scan")
    parser.add_argument("--page-end", type=int, default=None, help="Last PDF page to scan")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser()
    output_path = Path(args.output)

    entries, total_pages = scan_pdf(pdf_path, args.page_start, args.page_end)
    entries.sort(key=lambda item: (item["partNumber"], item.get("code", ""), item["pdfPage"]))
    write_catalog_js(entries, output_path, pdf_path.name, total_pages)
    print(f"wrote {len(entries)} catalog records to {output_path}")


if __name__ == "__main__":
    main()
