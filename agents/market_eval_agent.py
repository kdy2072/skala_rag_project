from InvestmentState import InvestmentState
from langchain_teddynote.tools.tavily import TavilySearch
from langchain_teddynote.evaluator import GroundednessChecker
from langchain_openai import ChatOpenAI
from datetime import datetime
import json

class MarketEvalAgent:
    def __init__(self):
        # Tavily 검색 툴
        self.tavily_tool = TavilySearch()
        # 관련성 평가기
        self.relevance_checker = GroundednessChecker(
            llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
            target="question-retrieval"
        ).create()

    def _filter_relevant(self, company: str, results: list, query: str, limit: int = 3) -> list:
        filtered = []
        for i, r in enumerate(results[:limit]):
            if isinstance(r, dict):
                title = r.get("title") or ""
                context = r.get("snippet") or title
            else:
                title, context = str(r), str(r)

            response = self.relevance_checker.invoke(
                {"question": f"{company} {query}", "context": context}
            )

            if str(response.score).lower().startswith("y"):
                filtered.append(r)
        return filtered

    def run(self, state: InvestmentState) -> InvestmentState:
        company_name = state.company_name or "알 수 없는 회사"
        core_tech = state.core_tech or "핵심기술"

        # 1. 산업 동향
        result_trends = self.tavily_tool.search(
            query=f"{company_name} {core_tech} 헬스케어 산업 동향",
            topic="news", days=30, max_results=3, format_output=False
        )

        # 2. 시장 규모
        result_market = self.tavily_tool.search(
            query=f"{company_name} {core_tech} 시장 규모",
            topic="news", days=30, max_results=2, format_output=False
        )

        # 3. 규제 환경
        result_regulation = self.tavily_tool.search(
            query=f"{company_name} {core_tech} 규제",
            topic="news", days=60, max_results=2, format_output=False
        )

        today = datetime.now().strftime("%Y-%m-%d")
        evidence = []
        for r in result_trends + result_regulation:
            evidence.append({
                "claim": r.get("title") or "검색 결과",
                "source_url": r.get("url"),
                "accessed_at": today
            })

        # 필터링 적용
        result_trends = self._filter_relevant(company_name, result_trends, "헬스케어 산업 동향")
        result_market = self._filter_relevant(company_name, result_market, "시장 규모 성장률")
        result_regulation = self._filter_relevant(company_name, result_regulation, "의료 규제")

        # ✅ state 업데이트
        state.industry_trends = " / ".join([r.get("content", "") for r in result_trends])
        state.market_size = " / ".join([r.get("content", "") for r in result_market])
        state.regulatory_barriers = " / ".join([r.get("title", "") for r in result_regulation])

        return state
