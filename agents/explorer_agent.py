import os
import json
from dotenv import load_dotenv
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain import hub
from langchain.agents import Tool, AgentExecutor, create_react_agent
from tavily import TavilyClient


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAISS_DIR = os.path.join(BASE_DIR, "faiss_db/unicorns_sementic")
CHECKPOINT_DIR = os.path.join(BASE_DIR, "checkpoint")


class ExplorerAgent:
    def __init__(self,
                 faiss_path=FAISS_DIR,
                 model_name="gpt-4o",
                 embedding_model="nlpai-lab/KURE-v1"):

        load_dotenv()

        # ✅ 환경변수 확인
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("⚠️ OPENAI_API_KEY가 .env에 설정되어 있지 않습니다.")
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise ValueError("⚠️ TAVILY_API_KEY가 .env에 설정되어 있지 않습니다.")

        # ✅ LLM + 임베딩 초기화
        self.llm = ChatOpenAI(model=model_name, temperature=0, max_retries=3)
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

        # ✅ VectorDB 로드
        self.vectordb = FAISS.load_local(
            faiss_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        print(f"✅ Faiss DB 로드 완료: {faiss_path}")

        # ✅ Tavily Client
        self.web_client = TavilyClient(api_key=tavily_api_key)

    # -----------------------------
    # Tool 정의
    # -----------------------------
    def rag_search(self, query: str, company_name: str) -> str:
        """FAISS DB에서 특정 기업의 관련 청크를 메타데이터 필터링을 통해 검색"""
        retriever = self.vectordb.as_retriever(
            search_kwargs={'filter': {'company': company_name}}
        )
        docs = retriever.invoke(query)
        if not docs:
            return "부족"
        return "\n\n".join([d.page_content for d in docs])

    def web_search(self, query: str) -> str:
        """Tavily로 웹 검색"""
        try:
            resp = self.web_client.search(query=query, search_depth="advanced", max_results=3)
            results = [item.get("content", "") for item in resp.get("results", [])]
            return "\n".join(results) if results else "부족"
        except Exception as e:
            print(f"웹 검색 중 오류 발생: {e}")
            return "부족"

    def save_json(self, data: dict, path: str) -> str:
        """결과 JSON 저장"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return f"✅ 저장 완료: {path}"

    # -----------------------------
    # DB에서 분석할 회사 목록 가져오기
    # -----------------------------
    def get_available_companies(self) -> List[str]:
        """Faiss DB에 저장된 모든 고유한 회사 이름을 가져옵니다."""
        if not self.vectordb.docstore:
            return []

        unique_companies = set()
        for doc_id in self.vectordb.index_to_docstore_id.values():
            metadata = self.vectordb.docstore.search(doc_id).metadata
            if "company" in metadata:
                unique_companies.add(metadata["company"])

        print(f"🔍 분석 대상 기업 목록: {list(unique_companies)}")
        return list(unique_companies)

    # -----------------------------
    # 단일 기업 분석
    # -----------------------------
    def analyze_single_company(self, company_name: str) -> dict:
        print("-" * 50)
        print(f"🚀 '{company_name}' 기업 분석을 시작합니다...")

        tools = [
            Tool(
                name="RAGSearch",
                func=lambda query: self.rag_search(query=query, company_name=company_name),
                description=f"'{company_name}'에 대한 질문에 FAISS 벡터DB에서 관련 정보를 찾는다."
            ),
            Tool(
                name="WebSearch",
                func=self.web_search,
                description="RAG에서 정보가 부족하면 웹 검색을 수행한다."
            )
        ]

        prompt = hub.pull("hwchase17/react")
        agent = create_react_agent(self.llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

        final_prompt = f"""
        당신은 차세대 유니콘을 조기에 발굴해내야 하는 공격적 투자 분석가입니다.
        단순한 기술 설명이 아니라, 이 기업이 시장 지배력을 확보할 수 있는지, 자본 효율성이 얼마나 높은지, 경쟁사 대비 절대적 우위가 무엇인지를 집요하게 파고듭니다.
        투자 판단에 직결되는 핵심 기술, 재무적 체력, 특허 방어력, 성장 리스크를 냉정하게 검증하고, 투자자의 시각에서 기회와 위험을 동시에 드러내는 것이 당신의 임무입니다.
                
        분석 대상 기업은 전부 한국계 기업 '{company_name}'입니다.

        아래 5가지 주제에 대해 반드시 정보를 수집하고 JSON으로 정리해야 합니다:
        - owner: 기업 소유자 업력 사항
        - core_tech: 기업의 핵심 기술
        - pros: 기업의 강점
        - patents: 기업의 보유 특허 정보
        - investments: 기업의 기 투자 정보

        규칙:
        1. 각 항목마다 먼저 RAGSearch를 사용해 정보를 찾습니다.
        2. RAGSearch 결과가 '부족'이라면 WebSearch를 사용합니다.
        3. 두 방법 모두 실패하면 '정보 확인 불가'이라고 기록합니다.
        4. 최종 출력은 반드시 JSON 형식으로만 출력하며,
           아래 예시 스키마를 따라야 합니다.
        5. 내용은 반드시 한글로만 작성합니다.

        출력 예시:
        ```json
            {{
                "owner": "...",
                "core_tech": "...",
                "pros": "...",
                "patents": "...",
                "investments": "..."
            }}
        ```
        """

        try:
            response = agent_executor.invoke({"input": final_prompt})
            raw_output = response.get("output", "") if isinstance(response, dict) else str(response)
            cleaned = raw_output.strip().replace("```json", "").replace("```", "")

            try:
                parsed = json.loads(cleaned)
            except Exception:
                parsed = {
                    "core_tech": "없음",
                    "pros_cons": {"pros": "없음", "cons": "없음"},
                    "patents": "없음",
                    "investments": "없음",
                    "raw_output": cleaned
                }

            return parsed

        except Exception as e:
            return {"company": company_name, "error": str(e)}

    # -----------------------------
    # 전체 분석 실행
    # -----------------------------
    def run_full_analysis(self) -> List[Dict]:
        print("🚀 run_full_analysis() 시작")

        companies_to_analyze = self.get_available_companies()
        print(f"📝 get_available_companies 결과: {companies_to_analyze}")

        all_results = []

        if not companies_to_analyze:
            print("⚠️ 분석할 기업이 VectorDB에 없습니다.")
            return []

        for idx, company in enumerate(companies_to_analyze, start=1):
            print(f"\n[{idx}/{len(companies_to_analyze)}] 현재 기업 분석 중: {company}")

            result_json = self.analyze_single_company(company)
            print(f"🔍 analyze_single_company 반환 타입: {type(result_json)}")
            print(f"📦 analyze_single_company 결과 일부: {str(result_json)[:200]}")

            # 🚨 dict 보장
            if not isinstance(result_json, dict):
                print("⚠️ 반환값이 dict가 아님 → dict로 래핑")
                result_json = {"error": "Invalid return type", "raw": str(result_json)}

            result_json["company_name"] = company
            all_results.append(result_json)
            print(f"✅ {company} 분석 완료, 결과 리스트에 추가됨")

        print("\n\n🎉 모든 기업 분석 완료!")
        print(f"📊 최종 결과 개수: {len(all_results)}")
        return all_results



# --- 여기가 실제 코드를 실행하는 부분입니다 ---
if __name__ == "__main__":
    # 1. 에이전트 인스턴스 생성
    agent = ExplorerAgent()
    
    # 2. 전체 분석 실행
    final_results_list = agent.run_full_analysis()
    
    # 3. 최종 결과 출력
    print("\n--- 최종 분석 결과 (List[JSON]) ---")
    # pretty printing
    # 저장 경로

    output_path = os.path.join(CHECKPOINT_DIR, "01_company_desc_semantic.json")


    # 디렉토리 생성 (없으면 자동 생성)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # JSON 저장
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_results_list, f, indent=4, ensure_ascii=False)

    print(json.dumps(final_results_list, indent=4, ensure_ascii=False))