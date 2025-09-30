# class MarketEvalAgent:
#     def run(self, input_json: dict) -> dict:
#         input_json.update({
#             "market_eval": "원격 의료 시장에서 연평균 12% 성장",
#             "market_size": "2025년까지 10조원 규모 예상",
#             "market_trend": "비대면 진료 수요 증가, 고령화에 따른 헬스케어 수요 확대",
#             "regulation_risk": "원격의료 관련 법안 개정 지연 가능성"
#         })
#         return input_json
    
from __future__ import annotations
from langchain_teddynote.tools.tavily import TavilySearch
import os
import json
import uuid
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from datetime import datetime
# from langchain_openai import ChatOpenAI
# from langchain_teddynote.evaluator import GroundednessChecker

load_dotenv()

# -------------------------------
# 테스트용 input 예시 (하드코딩)
# -------------------------------
input_json = [
    {
        "owner": "의료AI 전문의 출신, 실행력 우수",
        "core_tech": "근골격계 특화 AI 자세추정 모델",
        "pros": "글로벌 인재 채용, 제품 파이프라인 다수",
        "patents": "17개 특허 보유",
        "investments": "2021~2023 투자유치, 주요 투자자 LG, 삼성",
        "company_name": "EverEx",
        "tech_summary": "AI 기반 자세추정 핵심 기술",
        "differentiation_points": "정밀도 높은 모델, 특허 17개",
        "technical_risks": "데이터 품질 및 확장성 리스크",
        "patents_and_papers": "17개 특허, 논문 5개",
    },
    {
        "owner": "",
        "core_tech": "클라우드 AI  모델",
        "pros": "글로벌 인재 채용, 제품 파이프라인 다수",
        "patents": "17개 특허 보유",
        "investments": "",
        "company_name": "Oracle",
        "tech_summary": "AI",
        "differentiation_points": "",
        "technical_risks": "데이터 품질 및 확장성 리스크",
        "patents_and_papers": "17개 특허, 논문 5개",
    }
]


class MarketEvalAgent:
    """
    시장성 평가 에이전트 클래스
    - 입력: list[dict] (여러 회사 기본 정보)
    - 출력: list[dict] (각 회사 dict에 시장성 정보 병합)
    """

    def __init__(self, outdir: Optional[str] = None) -> None:
        """
        초기화: 출력 디렉토리 설정
        """
        # self.outdir = outdir or os.getenv("MARKET_OUTDIR", "./outputs")
        # os.makedirs(self.outdir, exist_ok=True)
        self.tavily_tool = TavilySearch()
        self.relevance_checker = GroundednessChecker(
            llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
            target="question-retrieval"
        ).create()
    




    def _filter_relevant(self, company_name: str, results: list, query: str) -> list:
        """검색 결과에서 회사 시장성 관련성이 높은 것만 필터링"""
        filtered = []
        for r in results:
            # 문자열/딕셔너리 안전 처리
            if isinstance(r, dict):
                title = r.get("title") or ""
                context = r.get("snippet") or title
            else:
                title, context = str(r), str(r)

            response = self.relevance_checker.invoke(
                {"question": f"{company_name} {query}", "context": context}
            )

            if response.score.lower().startswith("y"):  # "yes"
                filtered.append(r)

        return filtered

    def generate_market_data(self, tech: Dict[str, Any]) -> Dict[str, Any]:
        """Tavily 검색을 활용한 시장성 데이터 생성"""
        tech_summery = tech.get("tech_summery", "핵십기술")
        tech_core = tech.get("core_tech", "핵십기술")
        tech_compony = tech.get("tech_compony", "기엄명")


        # 1. 산업 동향
        result_trends = self.tavily_tool.search(
            query=f"{tech_summery, tech_core}과 관련된 헬스케어 산업 동향에 대해서 검색하세요. 결과는 한국어로 출력해주세요",
            topic="news", days=30, max_results=3, format_output=False
        )

        #2. 시장 규모
        result_market = self.tavily_tool.search(
            query=f"{tech_summery,tech_compony}의 시장 규모에 대해서 검색하세요. 결과는 한국어로 출력해주세요 ",
            topic="news", days=30, max_results=2, format_output=False
        )

        # 3. 규제 환경
        result_regulation = self.tavily_tool.search(
            query=f"{tech_summery} 관련 규제에 대해서 검색하세요. 결과는 한국어로 출력해주세요",
            topic="news", days=60, max_results=2, format_output=False
        )

        # evidence 생성
        today = datetime.now().strftime("%Y-%m-%d")
        evidence = []
        # for r in result_trends + result_market + result_regulation:
        for r in result_trends + result_regulation:
            evidence.append({
                "claim": r.get("title") or "검색 결과",
                "source_url": r.get("url"),
                "accessed_at": today
            })

        result_trends = self._filter_relevant({tech_summery, tech_core}, result_trends, "헬스케어 산업 동향")
        result_market = self._filter_relevant({tech_summery,tech_compony}, result_market, "시장 규모 성장률")
        result_regulation = self._filter_relevant(tech_summery, result_regulation, "의료 규제")
        # market.json 스키마 리턴
        return {
            "industry_trends": [r.get("title") for r in result_trends],

            "market_size": [r.get("content") for r in result_market],

            "regulatory_barriers": [r.get("title") for r in result_regulation],

            "evidence": evidence
        }

    def run(self, input_json: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        전체 실행 파이프라인
        """
        results = []
        for company in input_json:
            market_data = self.generate_market_data(company)
            company.update(market_data)
            results.append(company)
        return results

    def save_results(self, results: List[Dict[str, Any]]) -> None:
        """
        회사별 결과를 JSON 파일로 저장
        """
        for company in results:
            name = company.get("company_name") or f"unknown-{uuid.uuid4().hex[:6]}"
            slug = name.lower().replace(" ", "-")
            path = os.path.join(self.outdir, f"{slug}_result.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(company, f, ensure_ascii=False, indent=4)


# -------------------------------
# 실행 예시
# -------------------------------
if __name__ == "__main__":
    evaluator = MarketEvalAgent()

    # 테스트용 input_json 직접 실행
    results = evaluator.run(input_json)

    # 결과 출력
    print(json.dumps(results, ensure_ascii=False, indent=2))

    # 결과 저장
    # evaluator.save_results(results)
    # print("✅ 회사별 결과 JSON이 ./outputs 폴더에 저장되었습니다.")