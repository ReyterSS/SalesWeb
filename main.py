import pdfplumber

def extract_blocks_from_pdf(pdf_path):
    blocks = []
    current_block = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split("\n")

            for line in lines:
                if line.strip().startswith("REAL ESTATE LISTING FOR"):
                    # новая секция, возможно начало страницы
                    continue
                elif line.strip() == "CH" or line.strip() == "BANKRUPTCY" or line.strip().startswith("ADJOURNED"):
                    # конец блока (разделитель)
                    if current_block:
                        blocks.append("\n".join(current_block))
                        current_block = []
                elif line.strip() != "":
                    current_block.append(line.strip())

    if current_block:  # сохранить последний блок
        blocks.append("\n".join(current_block))

    return blocks


# Пример использования
pdf_path = "3ec14ac4-25a1-41cd-8c8b-d9996a9d686c.pdf"
blocks = extract_blocks_from_pdf(pdf_path)

for i, block in enumerate(blocks[:5]):  # показать первые 5 блоков
    print(f"\n--- Block {i+1} ---\n{block}")