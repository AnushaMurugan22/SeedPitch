import pymupdf


def parse_pdf(pdf_path):
    document = pymupdf.open(pdf_path)

    extracted_data = []

    for page_number, page in enumerate(document, start=1):

        blocks = page.get_text("dict")["blocks"]

        page_text = []
        headings = []

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:

                    text = span["text"].strip()

                    if not text:
                        continue

                    page_text.append(text)

                    # Detect possible headings
                    if span["size"] >= 14 or "bold" in span["font"].lower():
                        headings.append(text)

        extracted_data.append({
            "page_number": page_number,
            "headings": headings,
            "text": "\n".join(page_text)
        })

    document.close()

    return extracted_data
