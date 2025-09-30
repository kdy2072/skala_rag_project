# 라이브러리 설치 필요시
# pip install pdfplumber annotated-types certifi anyio

#ToDo
# input 하드코딩상태에서 checkpoint/.json load하는 것으로 바꾸기 ================= 완료
# 기 구현된 json 저장로직 checkpoint/디렉터리에 저장하는 것으로 바꾸기 ============= 완료
# 리턴 json타입 디벨롭=> 

from __future__ import annotations
from langchain_teddynote.tools.tavily import TavilySearch
import os
import json
import uuid
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_teddynote.evaluator import GroundednessChecker

load_dotenv()



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

        #Tavily 검색툴
        self.tavily_tool = TavilySearch()
        
        # 오픈ai모델 
        self.relevance_checker = GroundednessChecker(
            llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
            target="question-retrieval"
        ).create()
    



    # 관련성 평가 yes or no
    def _filter_relevant(self, company: str, results: list, query: str, limit: int = 3) -> list:
        """검색 결과에서 회사 시장성 관련성이 높은 것만 필터링 (최대 limit개만 검사)"""
        filtered = []
        for i, r in enumerate(results):
            if i >= limit:  # 루프 제한
                break

            # 문자열/딕셔너리 안전 처리
            if isinstance(r, dict):
                title = r.get("title") or ""
                context = r.get("snippet") or title
            else:
                title, context = str(r), str(r)

            # 관련성 체크
            response = self.relevance_checker.invoke(
                {"question": f"{company} {query}", "context": context}
            )

            if str(response.score).lower().startswith("y"):  # "yes"
                filtered.append(r)

        return filtered

    def generate_market_data(self, tech: Dict[str, Any]) -> Dict[str, Any]:
        """Tavily 검색을 활용한 시장성 데이터 생성"""
        tech_summery = tech.get("tech_summery", "핵십기술")
        tech_core = tech.get("core_tech", "핵십기술")
        tech_compony = tech.get("compony_name", "기엄명")


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
            "industry_trends": [r.get("content") for r in result_trends],

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

    
    def save_results(self, results: List[Dict[str, Any]], path: str) -> None:
        """
        동일한 JSON 파일에 덮어쓰기 (업데이트 저장)
        :param results: run() 실행 결과
        :param path: 입력/출력 파일 경로 (예: ./checkpoint/01_company_desc_semantic.json)
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


# -------------------------------
# 실행 예시
# -------------------------------
if __name__ == "__main__":
    evaluator = MarketEvalAgent()
    
    # 입력 파일 경로
    input_path = "./checkpoint/01_company_desc_semantic.json"

    # JSON 파일 읽기
    with open(input_path, "r", encoding="utf-8") as f:
        input_json = json.load(f)

    # 테스트용 input_json 직접 실행
    results = evaluator.run(input_json)

    # 결과 출력
    print(json.dumps(results, ensure_ascii=False, indent=2))

    # 결과 저장
    evaluator.save_results(results, input_path)
    # print("✅ 회사별 결과 JSON이 ./outputs 폴더에 저장되었습니다.")