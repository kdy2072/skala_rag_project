from InvestmentState import InvestmentState
from langchain_openai import ChatOpenAI
import json, re

class CompetitorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def run(self, state: InvestmentState) -> InvestmentState:
        company_name = state.company_name or "알 수 없는 회사"
        core_tech = state.core_tech or "핵심 기술"

        prompt = f"""
        당신은 헬스케어 스타트업 경쟁 분석 전문가입니다.
        회사명: {company_name}
        핵심 기술: {core_tech}

        아래 항목을 한국어 JSON 형식으로 작성하세요:
        {{
            "main_competitors": "...",
            "competitor_profiles": "...",
            "market_positioning": "...",
            "product_comparison": "...",
            "unique_value_props": "...",
            "threat_analysis": "...",
            "market_share": "...",
            "reference_urls": ["...", "..."]
        }}
        """

        response = self.llm.invoke(prompt)
        raw_content = response.content.strip()
        cleaned = re.sub(r"```json|```", "", raw_content).strip()

        try:
            parsed = json.loads(cleaned)
        except Exception as e:
            print(f"⚠️ CompetitorAgent JSON 파싱 실패: {e}")
            parsed = {}

        # ✅ state 업데이트
        state.main_competitors = parsed.get("main_competitors", "")
        state.competitor_profiles = parsed.get("competitor_profiles", "")
        state.market_positioning = parsed.get("market_positioning", "")
        state.product_comparison = parsed.get("product_comparison", "")
        state.unique_value_props = parsed.get("unique_value_props", "")
        state.threat_analysis = parsed.get("threat_analysis", "")
        state.market_share = parsed.get("market_share", "")
        state.reference_urls = parsed.get("reference_urls", [])

        return state
