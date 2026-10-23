
import os
from pypdf import PdfReader

RAW = "data/raw"
OUTPUT = "data/processed"

os.makedirs(OUTPUT, exist_ok=True)

total_pages = 0

for filename in os.listdir(RAW):

    if filename.lower().endswith(".pdf"):

        pdf_path = os.path.join(
            RAW,
            filename
        )

        reader = PdfReader(pdf_path)

        text = ""

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            page_text = page.extract_text()

            if page_text:

                text += (
                    f"\n--- Page {page_number} ---\n"
                    + page_text
                )

        output_name = os.path.splitext(
            filename
        )[0] + ".txt"

        output_path = os.path.join(
            OUTPUT,
            output_name
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(text)

        pages = len(reader.pages)

        total_pages += pages

        print("PDF:", filename)

        print("Pages:", pages)

        print("Text saved:", output_path)

        print("-" * 40)

print("Total PDF pages:", total_pages)

print("Text extraction completed!")
