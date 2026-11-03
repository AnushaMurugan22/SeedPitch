
from app.parser import parse_pdf

pdf_path = "data/raw/guidelines.pdf"

pages = parse_pdf(pdf_path)

for page in pages[:3]:
    print("\nPAGE:", page["page_number"])

    print("HEADINGS:")
    for heading in page["headings"]:
        print("-", heading)

    print("TEXT:")
    print(page["text"][:500])
