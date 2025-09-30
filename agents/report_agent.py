import os, json
from langchain_openai import ChatOpenAI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ✅ 한글 폰트 등록 (경로에 실제 폰트 파일이 있어야 함)
pdfmetrics.registerFont(TTFont("Malgun", "font/H2MJSM.TTF"))
pdfmetrics.registerFont(TTFont("Malgun-Bold", "font/H2GTRE.TTF"))

# ✅ 스타일 재정의
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="KoreanNormal", fontName="Malgun", fontSize=11, leading=14))
styles.add(ParagraphStyle(name="KoreanHeading", fontName="Malgun-Bold", fontSize=14, leading=18, spaceAfter=10))

class ReportAgent:
    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def run(self, input_json: dict, output_path=None) -> dict:
        company_name = input_json.get("company_name", "unknown").replace(" ", "_")
        if output_path is None:
            output_path = f"reports/{company_name}_llm_report.pdf"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 1. LLM 프롬프트 작성
        prompt = f"""
        당신은 전문 투자 보고서 작성자입니다.
        투자 보고서를 가지고 회사 임원들 앞에서 발표를 진행해야하는 상황입니다.
        아래 JSON 데이터를 기반으로 해당 상황에 맞는 양식으로 헬스케어 스타트업 투자 평가 보고서를 작성하세요.

        JSON 데이터:
        {json.dumps(input_json, ensure_ascii=False, indent=2)}

        보고서 구성:
        1. 표지 (회사명, 보고서 제목)
        2. 목차
        3. 본문
           - 스타트업 개요
           - 기술 요약
           - 시장성 평가
           - 경쟁사 비교
           - 투자 판단 (점수 요약 및 최종 결론)
        4. 결론

        결과는 한국어 문단 형식으로 작성해 주세요.
        """

        response = self.llm.invoke(prompt)
        report_text = response.content

        # 2. PDF 저장
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []

        # ✅ 한글 폰트 적용 스타일 사용
        for line in report_text.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), styles["KoreanNormal"]))
                story.append(Spacer(1, 10))

        doc.build(story)

        return {"status": "success", "report_path": output_path}
