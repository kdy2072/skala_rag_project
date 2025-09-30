import json
from report_agent import ReportAgent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

class InvestmentAgent:
    load_dotenv()
    
    def __init__(self, llm_client):
        self.client = llm_client

    def score_company(self, company: dict) -> dict:
        prompt = f"""
        당신은 스타트업 투자 심사역입니다. 
        아래 회사 정보를 읽고 Scorecard Method 기준(창업자 30%, 시장성 25%, 제품/기술 15%, 경쟁 우위 10%, 실적 10%, 투자조건 10%)에 따라 
        각 항목을 0~100점으로 평가해 주세요.

        회사 정보:
        - 창업자: {company["owner_info"]}
        - 시장성: {company["market_info"]}
        - 제품/기술: {company["product_info"]}
        - 경쟁 우위: {company["competitor_info"]}
        - 실적: {company["performance_info"]}
        - 투자조건: {company["deal_info"]}

        출력 형식(JSON):
        {{
          "owner_score": <int>,
          "market_score": <int>,
          "product_score": <int>,
          "competitor_score": <int>,
          "performance_score": <int>,
          "deal_score": <int>
        }}
        """

        import re
        response = self.client.invoke(prompt)
        print(response)
        raw_content =  response.content.strip()

        # ```json ... ``` 블록 제거
        cleaned = re.sub(r"```json|```", "", raw_content).strip()

        scores = json.loads(cleaned)

        

        return scores

    def calculate_weighted_score(self, scores: dict) -> float:
        weights = {
            "owner_score": 0.30,
            "market_score": 0.25,
            "product_score": 0.15,
            "competitor_score": 0.10,
            "performance_score": 0.10,
            "deal_score": 0.10,
        }
        return sum(scores[key] * weights[key] for key in weights)

    def run(self, input_json: dict) -> dict:
        results = []
        for company in input_json["companies"]:
            scores = self.score_company(company)
            total_score = self.calculate_weighted_score(scores)

            if total_score >= 80:
                ReportAgent().run(input_json)
                decision = "투자 추천"
            else:
                decision = "보류"

            results.append({
                "company_name": company["company_name"],
                "scores": scores,
                "total_score": total_score,
                "decision": decision,
                "details": company,
            })

        return {"investment_results": results}


if __name__ == "__main__":
    input_json = {
        "companies": [
            {
                "company_name": "헬스케어AI",
                "owner_info": "의료AI 전문의 출신, 커뮤니케이션 능력 우수",
                "market_info": "원격의료 시장, 연평균 12% 성장",
                "product_info": "딥러닝 기반 생체신호 분석",
                "competitor_info": "경쟁사 대비 특허 3건 보유, 네트워크 협력 강점",
                "performance_info": "매출 50억, 대형 병원 계약",
                "deal_info": "Valuation 200억, 지분율 10%"
            },
            {
                "company_name": "메디컬솔루션즈",
                "owner_info": "비즈니스 경험 풍부, 실행력 강함",
                "market_info": "헬스케어 SaaS 시장, 성장 가능성 높음",
                "product_info": "의료데이터 클라우드 플랫폼",
                "competitor_info": "경쟁사 다수 존재, 차별성 약함",
                "performance_info": "계약 다수 확보, 유저수 증가",
                "deal_info": "Valuation 100억, 지분율 15%"
            }
        ]
    }

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = InvestmentAgent(llm)
    result = agent.run(input_json)

    from pprint import pprint
    pprint(result)
