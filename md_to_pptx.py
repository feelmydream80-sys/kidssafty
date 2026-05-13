from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
import re

def md_to_ppt(md_file, ppt_file):
    prs = Presentation()
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 슬라이드 구분 (---)
    slides = re.split(r'\n---\n', content)
    
    for slide_text in slides:
        if not slide_text.strip():
            continue
            
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # 빈 레이아웃
        
        # 제목 추출
        title_match = re.search(r'# (.+)', slide_text)
        if title_match:
            title = title_match.group(1)
            txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(1))
            tf = txBox.text_frame
            tf.text = title
            tf.paragraphs[0].font.size = Pt(32)
            tf.paragraphs[0].font.bold = True
            
        # 본문 텍스트
        lines = slide_text.split('\n')
        y_offset = 1.5
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
            
            # 이미지 참조 확인
            img_match = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', line)
            if img_match:
                img_path = img_match.group(2)
                try:
                    slide.shapes.add_picture(img_path, Inches(1), Inches(y_offset), Inches(8), Inches(4))
                    y_offset += 4.5
                except:
                    # 이미지 로드 실패 시 텍스트로 대체
                    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(y_offset), Inches(9), Inches(0.5))
                    tf = txBox.text_frame
                    tf.text = f"[이미지: {img_match.group(1)}]"
                    y_offset += 0.6
            else:
                # 일반 텍스트
                if line.strip():
                    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(y_offset), Inches(9), Inches(0.5))
                    tf = txBox.text_frame
                    tf.text = line.strip()
                    tf.paragraphs[0].font.size = Pt(14)
                    y_offset += 0.6
    
    prs.save(ppt_file)
    print(f"PPT 생성 완료: {ppt_file}")

if __name__ == '__main__':
    md_to_ppt('submission/ppt/KidsSafeAI_PPT_v2.md', 'submission/ppt/KidsSafeAI_PPT_v2.pptx')
