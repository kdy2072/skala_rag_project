import json
import re
from agents.report_agent import ReportAgent
from langchain_openai import ChatOpenAI
from InvestmentState import InvestmentState

class InvestmentAgent:
    def __init__(self, llm_client=None):
        self.client = llm_client or ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.weights = {
            "owner_score": 0.30,
            "market_score": 0.25,
            "product_score": 0.15,
            "competitor_score": 0.10,
            "performance_score": 0.10,
            "deal_score": 0.10,
        }

    def score_company(self, company: dict) -> dict:
        """
        여러 필드를 종합해서 LLM에 넘겨 점수를 산출
        """
        prompt = f"""
        당신은 스타트업 투자 심사역입니다. 
        아래 회사 정보를 바탕으로 Scorecard Method 기준으로 평가하세요.
        각 항목은 0~100 정수 점수로 주고 반드시 JSON으로 출력하세요.

        회사명: {company.get("company_name")}

        [창업자 관련]
        - Owner: {company.get("owner")}
        - Pros: {company.get("pros")}

        [시장성 관련]
        - Market Size: {company.get("market_size")}
        - Industry Trends: {company.get("industry_trends")}
        - Customer Segments: {company.get("customer_segments")}
        - Regulatory Barriers: {company.get("regulatory_barriers")}

        [제품/기술력]
        - Core Tech: {company.get("core_tech")}
        - Tech Summary: {company.get("tech_summary")}
        - Differentiation Points: {company.get("differentiation_points")}
        - Technical Risks: {company.get("technical_risks")}
        - Patents/Papers: {company.get("patents_and_papers")}

        [경쟁 우위]
        - Main Competitors: {company.get("main_competitors")}
        - Competitor Profiles: {company.get("competitor_profiles")}
        - Market Positioning: {company.get("market_positioning")}
        - Product Comparison: {company.get("product_comparison")}
        - Threat Analysis: {company.get("threat_analysis")}

        [실적]
        - Performance: {company.get("performance")}

        [투자조건]
        - Investments: {company.get("investments")}
        - Funding: {company.get("performance", {}).get("funding")}

        반드시 JSON만 출력:
        {{
          "owner_score": <int>,
          "market_score": <int>,
          "product_score": <int>,
          "competitor_score": <int>,
          "performance_score": <int>,
          "deal_score": <int>
        }}
        """

        response = self.client.invoke(prompt)
        raw_content = response.content.strip()
        cleaned = re.sub(r"```json|```", "", raw_content).strip()

        try:
            scores = json.loads(cleaned)
        except Exception:
            print("⚠️ JSON 파싱 실패:", raw_content)
            scores = {k: 50 for k in self.weights}

        return scores

    def calculate_weighted_score(self, scores: dict) -> float:
        return sum(scores[k] * self.weights[k] for k in self.weights)

    def run(self, state: InvestmentState) -> InvestmentState:
        # state → dict 변환
        company_dict = state.model_dump()

        # 점수 계산
        scores = self.score_company(company_dict)
        total_score = self.calculate_weighted_score(scores)

        # state 업데이트
        state.scores = scores
        state.total_score = total_score
        state.decision = "투자 추천" if total_score >= 80 else "보류"

        if state.total_score >= 74:
            print(f"📊 {state.company_name} {state.total_score:.1f}점 → 보고서 생성 시작")
            report_agent = ReportAgent()
            report = report_agent.run(state)   # PDF 저장
            state.report_path = report.report_path
        else:
            print(f"📉 {state.company_name} {state.total_score:.1f}점 → 보고서 생략")


        return state

