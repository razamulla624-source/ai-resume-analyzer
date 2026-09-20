import fitz


def extract_text_from_pdf(pdf_path):
    extracted_text = []

    with fitz.open(pdf_path) as document:
        for page in document:
            text = page.get_text("text")

            if text:
                extracted_text.append(text)

    final_text = "\n".join(extracted_text)

    return final_text.strip()