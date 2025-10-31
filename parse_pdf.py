import pdfminer
import re
import os
from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTFigure
from typing import Optional


def clean_pdf_text(text: str) -> str:
    """Очистка текста от лишних переводов строк и переносов"""
    if not text:
        return ""

    try:
        lines = text.split('\n')
        cleaned_lines = []

        i = 0
        while i < len(lines):
            current_line = lines[i].rstrip()

            if (current_line.endswith('-') and
                    i + 1 < len(lines) and
                    lines[i + 1].strip() and
                    current_line[:-1].strip()):

                next_line = lines[i + 1].lstrip()
                if next_line:
                    merged_line = current_line[:-1] + next_line
                    cleaned_lines.append(merged_line)
                    i += 2
                else:
                    cleaned_lines.append(current_line[:-1])
                    i += 1
            else:
                if current_line:
                    cleaned_lines.append(current_line)
                i += 1

        result_lines = []
        for j, line in enumerate(cleaned_lines):
            if (j < len(cleaned_lines) - 1 and
                    not re.search(r'[.!?]$', line) and
                    cleaned_lines[j + 1] and
                    cleaned_lines[j + 1][0].islower()):

                result_lines.append(line + ' ' + cleaned_lines[j + 1])
                cleaned_lines[j + 1] = ""
            else:
                if line:
                    result_lines.append(line)

        result_lines = [line for line in result_lines if line.strip()]

        final_text = '\n'.join(result_lines)

        final_text = re.sub(r'\n{3,}', '\n\n', final_text)

        return final_text.strip()

    except Exception as e:
        print(f"Ошибка при очистке текста: {e}")
        return text


def clean_pdf_text_advanced(text: str) -> str:
    """
    Продвинутая очистка текста с обработкой различных типов переносов
    """
    if not text:
        return ""

    try:
        # Удаляем мягкие переносы (дефисы в конце строк)
        # Паттерн: слово-дефис-перевод_строки-слово
        text = re.sub(r'(\b\w+)-\n\s*(\w+\b)', r'\1\2', text)

        # Удаляем дефисы переноса с разными вариантами пробелов
        text = re.sub(r'(\b\w+)-\s*\n\s*(\w+\b)', r'\1\2', text)

        # Удаляем переносы в составных словах
        text = re.sub(r'(\b\w+)-\n\s*(\w+-\w+\b)', r'\1\2', text)

        # Объединяем строки, где нет знаков препинания в конце
        # и следующая строка начинается с маленькой буквы
        lines = text.split('\n')
        result_lines = []

        i = 0
        while i < len(lines):
            current_line = lines[i].strip()

            if not current_line:
                i += 1
                continue

            # Проверяем, нужно ли объединять со следующей строкой
            if (i < len(lines) - 1 and
                    lines[i + 1].strip() and
                    not re.search(r'[.!?:]$', current_line) and
                    lines[i + 1].strip()[0].islower()):

                # Объединяем текущую строку со следующей
                combined = current_line + ' ' + lines[i + 1].strip()
                result_lines.append(combined)
                i += 2  # Пропускаем следующую строку
            else:
                result_lines.append(current_line)
                i += 1

        cleaned_text = '\n'.join(result_lines)

        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)

        cleaned_text = re.sub(r' +', ' ', cleaned_text)

        return cleaned_text.strip()

    except Exception as e:
        print(f"Ошибка при продвинутой очистке текста: {e}")
        return text


def detailed_pdf_parsing_clean(pdf_path: str) -> str:
    """Детальный парсинг PDF с очисткой текста"""

    results = {
        'text': '',  # Полный очищенный текст документа
        'text_raw': '',  # Исходный текст без очистки
        'text_by_pages': [],  # Очищенный текст по страницам
        'metadata': {},
        'fonts': set(),
        'pages': [],
        'total_pages': 0,
        'success': False,
        'error': None
    }

    try:
        raw_text = extract_text(pdf_path)
        results['text_raw'] = raw_text
        results['text'] = clean_pdf_text_advanced(raw_text)

        with open(pdf_path, 'rb') as file:
            parser = pdfminer.pdfparser.PDFParser(file)
            document = pdfminer.pdfdocument.PDFDocument(parser)
            results['metadata'] = document.info[0] if document.info else {}

        for page_num, page_layout in enumerate(extract_pages(pdf_path), 1):
            page_text_raw = ""
            page_data = {
                'page_number': page_num,
                'text_raw': '',
                'text_clean': '',
                'elements': []
            }

            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    # Текстовый элемент
                    text_content = element.get_text()
                    if text_content.strip():
                        page_text_raw += text_content

                        element_data = {
                            'type': 'text',
                            'content_raw': text_content,
                            'content_clean': clean_pdf_text_advanced(text_content),
                            'bbox': element.bbox,
                            'font': set()
                        }

                        # Извлечение информации о шрифтах
                        for text_line in element:
                            for character in text_line:
                                if isinstance(character, LTChar):
                                    element_data['font'].add(character.fontname)
                                    results['fonts'].add(character.fontname)

                        page_data['elements'].append(element_data)

                elif isinstance(element, LTFigure):
                    # Графический элемент
                    page_data['elements'].append({
                        'type': 'figure',
                        'bbox': element.bbox
                    })

            page_data['text_raw'] = page_text_raw
            page_data['text_clean'] = clean_pdf_text_advanced(page_text_raw)

            results['text_by_pages'].append({
                'page_number': page_num,
                'content_raw': page_text_raw,
                'content_clean': clean_pdf_text_advanced(page_text_raw)
            })
            results['pages'].append(page_data)

        results['total_pages'] = len(results['pages'])
        results['fonts'] = list(results['fonts'])
        results['success'] = True

    except Exception as e:
        error_msg = f"Ошибка при парсинге PDF: {e}"
        print(error_msg)
        results['error'] = error_msg
        results['success'] = False

    return results


def save_clean_text_to_file(
        pdf_path: str,
        output_file: Optional[str] = None,
        encoding: str = 'utf-8'
) -> bool:
    """
    Полный цикл парсинга PDF и сохранения очищенного текста в файл
    """

    if output_file is None:
        base_name = os.path.splitext(pdf_path)[0]
        output_file = f"{base_name}_cleaned.txt"

    print(f"Начинаем парсинг PDF: {pdf_path}")
    print("=" * 50)

    parsed_data = detailed_pdf_parsing_clean(pdf_path)

    if not parsed_data['success']:
        print(f"Ошибка при парсинге: {parsed_data['error']}")
        return False

    clean_text = parsed_data['text']

    if not clean_text.strip():
        print("Не удалось извлечь текст из PDF")
        return False

    try:
        with open(output_file, 'w', encoding=encoding) as f:
            f.write(clean_text)

        print("Парсинг завершен успешно!")

        return True

    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")
        return False


def parse(pdf_file: str, output_file: Optional[str] = None):
    """Основная функция для выполнения полного цикла парсинга"""
    if not os.path.exists(pdf_file):
        print(f"Файл {pdf_file} не найден!")
        print("Пожалуйста, укажите правильный путь к PDF-файлу")
        return

    success = save_clean_text_to_file(pdf_file, output_file)

    if success:
        print("\nПолный цикл парсинга завершен успешно!")
    else:
        print("\nПроизошла ошибка в процессе парсинга")


if __name__ == "__main__":
    pdf_file = "protocol2.pdf"
    parse(pdf_file)
