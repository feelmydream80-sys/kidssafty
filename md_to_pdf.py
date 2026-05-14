from fpdf import FPDF
import re

import os
BASE = os.path.dirname(os.path.abspath(__file__))
FONT_REG = os.path.join(BASE, 'malgun.ttf') if os.path.exists(os.path.join(BASE, 'malgun.ttf')) else 'C:/Windows/Fonts/malgun.ttf'
FONT_BOLD = os.path.join(BASE, 'malgunbd.ttf') if os.path.exists(os.path.join(BASE, 'malgunbd.ttf')) else 'C:/Windows/Fonts/malgunbd.ttf'

class SlidePDF(FPDF):
    def __init__(self):
        super().__init__('L', 'mm', 'A4')
        self.set_auto_page_break(False)
        self.page_w = 297
        self.page_h = 210
        self.margin = 12
        self.content_w = self.page_w - self.margin * 2

        self.add_font('NG', '', FONT_REG)
        self.add_font('NG', 'B', FONT_BOLD)

    def add_slide(self, title, items):
        self.add_page()
        y = self.margin

        self.set_font('NG', 'B', 16)
        self.set_text_color(231, 76, 60)
        self.set_xy(self.margin, y)
        self.cell(self.content_w, 10, title)
        y += 12

        for typ, val in items:
            need_y = 5
            if typ == 'table' and val:
                need_y = len(val) * 5 + 4
            if y + need_y > self.page_h - self.margin - 8:
                y = self.page_h - self.margin - 8

            self.set_xy(self.margin, y)

            if typ == 'text':
                self.set_font('NG', '', 9)
                self.set_text_color(44, 62, 80)
                self.multi_cell(self.content_w, 5, val)
                y = self.get_y()

            elif typ == 'h3':
                self.set_font('NG', 'B', 11)
                self.set_text_color(44, 62, 80)
                self.multi_cell(self.content_w, 6, val)
                y = self.get_y()

            elif typ == 'bold':
                self.set_font('NG', 'B', 10)
                self.set_text_color(44, 62, 80)
                self.multi_cell(self.content_w, 5, val)
                y = self.get_y()

            elif typ == 'check':
                self.set_font('NG', '', 9)
                self.set_text_color(39, 174, 96)
                self.multi_cell(self.content_w, 5, val)
                y = self.get_y()

            elif typ == 'bullet':
                self.set_font('NG', '', 9)
                self.set_text_color(44, 62, 80)
                self.multi_cell(self.content_w - 4, 5, '  ' + val)
                y = self.get_y()

            elif typ == 'code':
                self.set_font('NG', '', 8)
                self.set_text_color(44, 62, 80)
                self.set_fill_color(240, 240, 240)
                self.multi_cell(self.content_w, 4, val, fill=True)
                y = self.get_y()

            elif typ == 'table' and val:
                self.render_table(val)
                y = self.get_y()

    def render_table(self, rows):
        if not rows:
            return
        col_count = len(rows[0])
        col_w = self.content_w / col_count

        self.set_font('NG', 'B', 8)
        self.set_fill_color(52, 152, 219)
        self.set_text_color(255, 255, 255)
        for h in rows[0]:
            self.cell(col_w, 5.5, h, border=1, fill=True)
        self.ln()

        self.set_font('NG', '', 8)
        self.set_text_color(44, 62, 80)
        for ri in range(1, len(rows)):
            if ri % 2 == 0:
                self.set_fill_color(248, 249, 250)
            else:
                self.set_fill_color(255, 255, 255)
            for ci in range(col_count):
                txt = rows[ri][ci] if ci < len(rows[ri]) else ''
                self.cell(col_w, 5, txt, border=1, fill=True)
            self.ln()


def parse_slides(md_text):
    slides = re.split(r'\n---\n', md_text)
    result = []

    for slide_text in slides:
        if not slide_text.strip():
            continue
        lines = slide_text.strip().split('\n')

        title_match = re.search(r'# (.+)', slide_text)
        title = title_match.group(1) if title_match else ''
        if ':' in title and '슬라이드' in title:
            title = title.split(':', 1)[1].strip()

        items = []
        table_buffer = []
        code_block = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('```'):
                code_block = not code_block
                continue

            if stripped.startswith('# ') or (stripped.startswith('#') and '슬라이드' in stripped):
                continue

            # 테이블
            if stripped.startswith('|') and stripped.endswith('|') and not all(c in '| :-' for c in stripped):
                table_buffer.append(stripped)
                continue

            if table_buffer:
                rows = []
                for r in table_buffer:
                    cells = [c.strip() for c in r.split('|')[1:-1]]
                    if cells and not all(c in '| :-' for c in r):
                        rows.append(cells)
                if rows:
                    items.append(('table', rows))
                table_buffer = []

            if code_block:
                items.append(('code', stripped))
                continue

            if stripped.startswith('---') or stripped.startswith('|---') or not stripped:
                pass
            elif stripped.startswith('### '):
                items.append(('h3', stripped.replace('### ', '')))
            elif stripped.startswith('**') and stripped.endswith('**'):
                items.append(('bold', stripped.replace('**', '')))
            elif stripped.startswith('- [') or stripped.startswith('✅'):
                items.append(('check', stripped))
            elif stripped.startswith('  '):
                items.append(('sub', stripped.strip()))
            elif stripped.startswith('- '):
                items.append(('bullet', stripped))
            elif stripped:
                items.append(('text', stripped))

        # flush table buffer
        if table_buffer:
            rows = []
            for r in table_buffer:
                cells = [c.strip() for c in r.split('|')[1:-1]]
                if cells and not all(c in '| :-' for c in r):
                    rows.append(cells)
            if rows:
                items.append(('table', rows))

        result.append((title, items))

    return result


def md_to_pdf(md_file, pdf_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    slides = parse_slides(md_text)
    pdf = SlidePDF()

    for title, items in slides:
        pdf.add_slide(title, items)

    pdf.output(pdf_file)
    print('PDF 생성 완료: %s (%d페이지)' % (pdf_file, len(slides)))


if __name__ == '__main__':
    md_to_pdf('submission/ppt/KidsSafeAI_PPT_v4.md', 'submission/ppt/KidsSafeAI_PPT_v4.pdf')
