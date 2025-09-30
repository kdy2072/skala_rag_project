import json
import re
from agents.report_agent import ReportAgent
from langchain_openai import ChatOpenAI


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

    def run(self, input_json: list) -> dict:
        results = []
        for company in input_json:
            scores = self.score_company(company)
            total_score = self.calculate_weighted_score(scores)

            if total_score >= 74:
                decision = "투자 추천"
                ReportAgent().run({
                    **company,
                    "scores": scores,
                    "total_score": total_score,
                    "investment_decision": decision
                })
            else:
                decision = "보류"

            results.append({
                "company_name": company.get("company_name"),
                "scores": scores,
                "total_score": round(total_score, 2),
                "decision": decision,
                "details": company
            })

        return {"investment_results": results}
