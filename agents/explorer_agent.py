from InvestmentState import InvestmentState
from langchain import hub
from langchain.agents import Tool, AgentExecutor, create_react_agent
from tavily import TavilyClient
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import os, json
from dotenv import load_dotenv


class ExplorerAgent:
    def __init__(self,
                 faiss_path,
                 model_name="gpt-4o",
                 embedding_model="nlpai-lab/KURE-v1"):
        load_dotenv()

        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("⚠️ OPENAI_API_KEY가 .env에 설정되어 있지 않습니다.")
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise ValueError("⚠️ TAVILY_API_KEY가 .env에 설정되어 있지 않습니다.")

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
    # DB에서 기업 목록 가져오기
    # -----------------------------
    def get_available_companies(self) -> list[str]:
        if not self.vectordb.docstore:
            return []
        unique_companies = set()
        for doc_id in self.vectordb.index_to_docstore_id.values():
            metadata = self.vectordb.docstore.search(doc_id).metadata
            if "company" in metadata:
                unique_companies.add(metadata["company"])
        return list(unique_companies)

    # -----------------------------
    # 단일 기업 분석 (state 반환)
    # -----------------------------
    def analyze_single_company(self, company_name: str) -> InvestmentState:

        print(f"🚀 ExplorerAgent: '{company_name}' 분석 시작")

        tools = [
            Tool(
                name="RAGSearch",
                func=lambda query: self.rag_search(query=query, company_name=company_name),
                description=f"'{company_name}' 관련 정보를 FAISS 벡터DB에서 검색"
            ),
            Tool(
                name="WebSearch",
                func=self.web_search,
                description="RAG에서 부족하면 웹 검색 수행"
            )
        ]

        prompt = hub.pull("hwchase17/react")
        agent = create_react_agent(self.llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

        final_prompt = f"""
        당신은 공격적 투자 분석가입니다.
        '{company_name}'의 핵심 기술, 소유자 업력, 강점, 특허 방어력, 투자 이력 등을 수집하여
        JSON 형식으로 정리하세요.

        출력 스키마:
        {{
            "owner": "...",
            "core_tech": "...",
            "pros": "...",
            "patents": "...",
            "investments": "..."
        }}
        """

        try:
            response = agent_executor.invoke({"input": final_prompt})
            raw_output = response.get("output", "") if isinstance(response, dict) else str(response)
            cleaned = raw_output.strip().replace("```json", "").replace("```", "")
            parsed = json.loads(cleaned)
        except Exception as e:
            print(f"⚠️ 분석 중 오류: {e}")
            parsed = {}

        # ✅ state 객체 생성 및 반환
        return InvestmentState(
            company_name=company_name,
            owner=parsed.get("owner", ""),
            core_tech=parsed.get("core_tech", ""),
            pros=parsed.get("pros", ""),
            patents=parsed.get("patents", ""),
            investments=parsed.get("investments", "")
        )

    # -----------------------------
    # 전체 기업 자동 실행 (state 리스트 반환)
    # -----------------------------
    def run(self) -> list[InvestmentState]:
        companies = self.get_available_companies()
        if not companies:
            print("⚠️ 분석할 기업이 없습니다.")
            return []

        states = []
        for company in companies:
            state = self.analyze_single_company(company)
            states.append(state)

        return states

    # -----------------------------
    # 보조 메서드 (검색 함수들)
    # -----------------------------
    def rag_search(self, query: str, company_name: str) -> str:
        retriever = self.vectordb.as_retriever(
            search_kwargs={'filter': {'company': company_name}}
        )
        docs = retriever.invoke(query)
        if not docs:
            return "부족"
        return "\n\n".join([d.page_content for d in docs])

    def web_search(self, query: str) -> str:
        try:
            resp = self.web_client.search(query=query, search_depth="advanced", max_results=3)
            results = [item.get("content", "") for item in resp.get("results", [])]
            return "\n".join(results) if results else "부족"
        except Exception as e:
            print(f"웹 검색 중 오류 발생: {e}")
            return "부족"
