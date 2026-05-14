from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import re

def md_to_ppt(md_file, ppt_file):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    slides_raw = re.split(r'\n---\n', content)

    for slide_text in slides_raw:
        if not slide_text.strip():
            continue

        lines = slide_text.strip().split('\n')
        title_match = re.search(r'# (.+)', slide_text)
        title = title_match.group(1) if title_match else ''

        is_first = '표지' in title
        is_last = '맺음말' in title

        body_lines = []
        code_block = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```'):
                code_block = not code_block
                continue
            if code_block:
                continue
            if stripped.startswith('#') and '슬라이드' in stripped:
                continue
            if stripped:
                body_lines.append(line)

        items = []
        for bl in body_lines:
            s = bl.strip()
            if s.startswith('|') and s.endswith('|') and not all(c in '| :-' for c in s):
                items.append(('cell', s))
            elif s.startswith('!['):
                m = re.search(r'\(([^)]+)\)', s)
                items.append(('img', m.group(1) if m else ''))
            elif s.startswith('### '):
                items.append(('h3', s.replace('### ', '')))
            elif s.startswith('**') and s.endswith('**'):
                items.append(('bold', s.replace('**', '')))
            elif s.startswith('- [') or s.startswith('✅'):
                items.append(('check', s))
            elif s.startswith('  '):
                items.append(('sub', s.strip()))
            elif s.startswith('- '):
                items.append(('bullet', s))
            elif s.startswith('|---'):
                continue
            else:
                items.append(('text', s))

        # 페이지 분할: 한 슬라이드당 내용이 너무 많으면 분할
        pages = []
        cur = []
        cur_h = 0.0

        for typ, val in items:
            h = 4.5 if typ == 'img' else 0.35
            if typ == 'cell':
                h = 0.4
            if cur_h + h > 5.0 and cur:
                pages.append(cur)
                cur = [(typ, val)]
                cur_h = h
            else:
                cur.append((typ, val))
                cur_h += h
        if cur:
            pages.append(cur)

        for pi, page in enumerate(pages):
            slide = prs.slides.add_slide(prs.slide_layouts[6])

            y = Inches(0.3)
            lm = Inches(0.5)
            mw = Inches(12.3)

            if is_first or is_last:
                t = title.replace('슬라이드 1: ', '').replace('슬라이드 15: ', '')
                add_tb(slide, lm, Inches(2.5), mw, Inches(1), t, size=30, bold=True, align=PP_ALIGN.CENTER)
                for typ, val in page:
                    if typ in ('text', 'bold', 'sub'):
                        add_tb(slide, Inches(2), y + Inches(1.8), Inches(9), Inches(0.4),
                               val, size=14, align=PP_ALIGN.CENTER)
                        y += Inches(0.35)
                continue

            # 제목
            t = title.split(':', 1)[1].strip() if ':' in title else title
            if len(pages) > 1:
                t += f' ({pi+1}/{len(pages)})'
            add_tb(slide, lm, Inches(0.3), mw, Inches(0.5), t, size=20, bold=True)

            y = Inches(1.0)

            # 테이블 버퍼
            tbuf = []

            for typ, val in page:
                if typ == 'cell':
                    tbuf.append(val)
                    continue

                if tbuf:
                    render_table(slide, tbuf, lm, y, mw)
                    y += Inches(len(tbuf) * 0.3 + 0.2)
                    tbuf = []

                if typ == 'img':
                    try:
                        slide.shapes.add_picture(val, Inches(1), y, Inches(8), Inches(4))
                        y += Inches(4.2)
                    except:
                        pass
                elif typ == 'h3':
                    add_tb(slide, lm, y, mw, Inches(0.35), val, size=15, bold=True)
                    y += Inches(0.35)
                elif typ == 'bold':
                    add_tb(slide, lm, y, mw, Inches(0.3), val, size=12, bold=True)
                    y += Inches(0.28)
                elif typ == 'check':
                    add_tb(slide, lm, y, mw, Inches(0.28), val, size=11)
                    y += Inches(0.26)
                elif typ == 'sub':
                    add_tb(slide, lm + Inches(0.3), y, mw, Inches(0.25), val, size=10)
                    y += Inches(0.22)
                elif typ == 'bullet':
                    add_tb(slide, lm, y, mw, Inches(0.28), val, size=11)
                    y += Inches(0.26)
                elif typ == 'text' and val.strip():
                    add_tb(slide, lm, y, mw, Inches(0.28), val, size=12)
                    y += Inches(0.26)

            if tbuf:
                render_table(slide, tbuf, lm, y, mw)

    prs.save(ppt_file)
    print('PPT 생성 완료: %s (%d개 슬라이드)' % (ppt_file, len(slides_raw)))


def add_tb(slide, left, top, width, height, text, size=12, bold=False, align=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(int(left), int(top), int(width), int(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.alignment = align
    return tf


def render_table(slide, rows_data, left, top, max_w):
    if len(rows_data) < 1:
        return
    data = []
    for r in rows_data:
        cells = [c.strip() for c in r.split('|')[1:-1]]
        if cells:
            data.append(cells)
    if len(data) < 1:
        return

    rows = len(data)
    cols = len(data[0])
    row_h = Inches(0.3)
    total_h = int(row_h * rows + Inches(0.1))
    col_w = int(max_w / cols)

    tbl_shape = slide.shapes.add_table(rows, cols, int(left), int(top), int(max_w), total_h)
    tbl = tbl_shape.table

    for ri in range(rows):
        tbl.rows[ri].height = row_h
        for ci in range(cols):
            cell = tbl.cell(ri, ci)
            cell.text = data[ri][ci] if ci < len(data[ri]) else ''
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(9)
                p.font.bold = (ri == 0)


if __name__ == '__main__':
    md_to_ppt('submission/ppt/KidsSafeAI_PPT_v4.md', 'submission/ppt/KidsSafeAI_PPT_v4.pptx')
