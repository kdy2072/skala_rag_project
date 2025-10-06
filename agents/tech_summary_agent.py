import json
import os
from typing import Dict, List, Annotated, Sequence, Literal, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from tavily import TavilyClient
import requests
import xml.etree.ElementTree as ET

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from InvestmentState import InvestmentState
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAISS_DIR = os.path.join(BASE_DIR, "faiss_db/unicorns_sementic")
CHECKPOINT_DIR = os.path.join(BASE_DIR, "checkpoint")


class TechAnalysisState(BaseModel):
    """진짜 Agent 상태"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    company_name: str = ""
    core_tech: str = ""
    patents: str = ""
    investments: str = ""
    pros: str = ""
    owner: str = ""
    
    # 최종 출력
    tech_summary: str = ""
    strengths_and_weaknesses: Union[str, Dict] = ""   # ✅ dict도 허용
    differentiation_points: Union[str, List[str]] = "" # ✅ list도 허용
    technical_risks: Union[str, List[str]] = "" 
    patents_and_papers: List[str] = []
    
    confidence_score: float = 0.0


class RelevanceGrade(BaseModel):
    """관련성 평가"""
    binary_score: str = Field(description="'yes' if relevant, 'no' if not")


class TechSummaryAgent:
    """진짜 Agent 기반 기술 분석 시스템"""
    
    def __init__(self, faiss_path=FAISS_DIR, embedding_model="nlpai-lab/KURE-v1"):
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self.vectordb = FAISS.load_local(
            folder_path=faiss_path,
            embeddings=self.embeddings,
            allow_dangerous_deserialization=True
        )
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.web_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        # 전역 변수로 저장 (tool 함수에서 접근)
        global _vectordb, _web_client, _kipris_tool
        _vectordb = self.vectordb
        _web_client = self.web_client
        _kipris_tool = KIPRISPatentTool()
        
        print(f"✅ 진짜 Agent 초기화 완료")
        
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """진짜 Agent 패턴 그래프"""
        workflow = StateGraph(TechAnalysisState)
        
        # 도구 정의
        tools = [rag_search_tool, web_search_tool, kipris_search_tool]
        
        # ToolNode 생성 (진짜 Agent의 핵심)
        tool_node = ToolNode(tools)
        
        # 노드 추가
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", tool_node)  # ToolNode 사용
        workflow.add_node("grade_documents", self._grade_documents)
        workflow.add_node("rewrite", self._rewrite_query)
        workflow.add_node("generate", self._generate_summary)
        
        # 시작
        workflow.add_edge(START, "agent")
        
        # Agent가 도구 선택 (tools_condition 사용)
        workflow.add_conditional_edges(
            "agent",
            tools_condition,  # 진짜 Agent의 핵심
            {
                "tools": "tools",  # Agent가 도구 호출
                END: END
            }
        )
        
        # 도구 실행 후 관련성 평가
        workflow.add_edge("tools", "grade_documents")
        
        # 관련성 평가 후 분기
        workflow.add_conditional_edges(
            "grade_documents",
            self._decide_next_step,
            {
                "rewrite": "rewrite",
                "generate": "generate"
            }
        )
        
        # 쿼리 재작성 후 다시 Agent로
        workflow.add_edge("rewrite", "agent")
        
        # 최종 요약 후 종료
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    def _agent_node(self, state: TechAnalysisState) -> TechAnalysisState:
        """진짜 Agent - 도구를 bind하고 자동 선택"""
        print(f"\n🤖 Agent 실행 중...")
        
        # MVP: 간단한 무한루프 방지
        if len(state.messages) > 6:
            return {"messages": [HumanMessage(content="정보 수집 완료")]}
        
        tools = [rag_search_tool, web_search_tool, kipris_search_tool]
        model_with_tools = self.llm.bind_tools(tools)
        
        system_msg = f"""기술 분석 전문가로서 {state.company_name}의 {state.core_tech} 기술을 분석하세요.

2-3회 도구 사용 후 "정보 수집 완료"라고 답하세요."""
        
        messages = [HumanMessage(content=system_msg)] + list(state.messages[1:])
        response = model_with_tools.invoke(messages)
        
        print(f"💭 Agent 응답: {response.content if response.content else '도구 호출'}")
        
        return {"messages": [response]}
    
    def _grade_documents(self, state: TechAnalysisState) -> TechAnalysisState:
        """LLM이 정보 충분성 평가"""
        print("🔍 정보 충분성 평가 중...")
        
        # 마지막 도구 실행 결과 추출
        last_message = state.messages[-1]
        retrieved_docs = last_message.content if hasattr(last_message, 'content') else ""
        
        llm_with_tool = self.llm.with_structured_output(RelevanceGrade)
        
        prompt = PromptTemplate(
            template="""다음 정보가 "{company}"의 "{tech}" 기술 분석에 충분한지 평가하세요:

검색 결과:
{docs}

평가 기준:
1. 기술의 작동 원리가 설명되어 있는가?
2. 경쟁 기술과의 차별점이 있는가?
3. 특허나 연구 성과가 언급되는가?

충분하면 'yes', 부족하면 'no'를 반환하세요.""",
            input_variables=["company", "tech", "docs"]
        )
        
        chain = prompt | llm_with_tool
        result = chain.invoke({
            "company": state.company_name,
            "tech": state.core_tech,
            "docs": str(retrieved_docs)[:1000]
        })
        
        print(f"📊 평가 결과: {result.binary_score}")
        
        state.confidence_score = 80 if result.binary_score == "yes" else 40
        
        return state
    
    def _decide_next_step(self, state: TechAnalysisState) -> Literal["rewrite", "generate"]:
        """다음 단계 결정"""
        if state.confidence_score >= 70:
            print("✅ 충분한 정보 수집됨")
            return "generate"
        else:
            print("🔄 정보 부족, 쿼리 재작성")
            return "rewrite"
    
    def _rewrite_query(self, state: TechAnalysisState) -> TechAnalysisState:
        """LLM이 검색 쿼리 개선"""
        print(f"✍️ 검색 쿼리 재작성 중...")
        
        prompt = f"""다음 기술 분석을 위해 더 나은 검색 쿼리를 작성하세요:

회사: {state.company_name}
기술: {state.core_tech}

현재까지 수집된 정보가 부족합니다. 
기술의 핵심 원리, 경쟁 기술과의 차별점, 특허 및 연구 성과를 찾을 수 있는 개선된 검색 쿼리를 제안하세요.

개선된 검색 쿼리:"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        improved_query = response.content.strip()
        
        print(f"💡 개선된 쿼리: {improved_query}")
        
        return {"messages": [HumanMessage(content=improved_query)]}
    
    def _generate_summary(self, state: TechAnalysisState) -> TechAnalysisState:
        """최종 요약 생성"""
        print("📝 최종 요약 생성 중...")
        
        # 모든 메시지에서 도구 실행 결과 추출
        all_evidence = []
        for msg in state.messages:
            if hasattr(msg, 'content') and msg.content:
                all_evidence.append(str(msg.content))
        
        combined_evidence = "\n\n".join(all_evidence[-5:])  # 최근 5개
        
        prompt = PromptTemplate(
            template="""다음 정보를 바탕으로 투자 관점의 기술 요약을 JSON 형식으로 생성하세요:

회사: {company}
핵심 기술: {tech}
강점: {pros}

수집된 정보:
{evidence}

JSON 형식으로 출력:
{{
    "tech_summary": "기술 요약 (300-500자)",
    "strengths_and_weaknesses": "강점/약점 분석",
    "differentiation_points": "차별점",
    "technical_risks": "기술 리스크",
    "patents_and_papers": ["특허1", "논문1"]
}}""",
            input_variables=["company", "tech", "pros", "evidence"]
        )
        
        chain = prompt | self.llm | StrOutputParser()
        summary = chain.invoke({
            "company": state.company_name,
            "tech": state.core_tech,
            "pros": state.pros,
            "evidence": combined_evidence[:2000]
        })
        
        try:
            cleaned = summary.strip().replace('```json', '').replace('```', '')
            parsed = json.loads(cleaned)
            
            state.tech_summary = parsed.get("tech_summary", "")
            state.strengths_and_weaknesses = parsed.get("strengths_and_weaknesses", "")
            state.differentiation_points = parsed.get("differentiation_points", "")
            state.technical_risks = parsed.get("technical_risks", "")
            state.patents_and_papers = parsed.get("patents_and_papers", [])
            
            print("✅ 요약 생성 완료")
        except Exception as e:
            state.tech_summary = f"{state.company_name}의 {state.core_tech} 기술 분석"
            print(f"⚠️ JSON 파싱 실패: {e}")
        
        return state


    def run(self, state: InvestmentState) -> InvestmentState:
        print(f"\n🚀 TechSummaryAgent 시작: {state.company_name} - {state.core_tech}")

        initial_state = TechAnalysisState(
            messages=[HumanMessage(content=f"기술 분석 시작: {state.company_name} - {state.core_tech}")],
            company_name=state.company_name,
            core_tech=state.core_tech,
            patents=state.patents,
            investments="",
            pros=state.pros,
            owner=state.owner
        )

        # graph.invoke → dict 반환
        final_state_dict = self.graph.invoke(initial_state, {"recursion_limit": 15})

        # dict → Pydantic 모델 변환
        final_state = TechAnalysisState(**final_state_dict)

        # ✅ 결과를 InvestmentState에 반영
        state.tech_summary = final_state.tech_summary
        state.strengths_and_weaknesses = final_state.strengths_and_weaknesses
        state.differentiation_points = final_state.differentiation_points
        state.technical_risks = final_state.technical_risks
        state.patents_and_papers = final_state.patents_and_papers
        state.confidence_score = final_state.confidence_score

        return state
# ============================================
# 도구 정의 (진짜 Agent의 핵심)
# ============================================

@tool
def rag_search_tool(query: str) -> str:
    """
    내부 문서에서 기술 정보를 검색합니다.
    
    Args:
        query: 검색할 기술 키워드 (예: "AI 기반 신약 개발 기술")
    
    Returns:
        검색된 문서 내용
    """
    print(f"📚 RAG 검색: {query}")
    
    try:
        retriever = _vectordb.as_retriever(search_kwargs={'k': 5})
        docs = retriever.invoke(query)
        
        if docs:
            result = "\n\n".join([doc.page_content for doc in docs])
            print(f"✅ {len(docs)}개 문서 발견")
            return result
        else:
            print("⚠️ 결과 없음")
            return "검색 결과 없음"
    except Exception as e:
        print(f"❌ 오류: {e}")
        return f"검색 오류: {str(e)}"


@tool
def web_search_tool(query: str) -> str:
    """
    웹에서 최신 기술 정보를 검색합니다.
    
    Args:
        query: 검색할 기술 키워드 (예: "Qgenetics QG3030 신약 개발")
    
    Returns:
        검색된 웹 페이지 내용
    """
    print(f"🌐 웹 검색: {query}")
    
    try:
        response = _web_client.search(query=query, search_depth="advanced", max_results=5)
        results = response.get("results", [])
        
        if results:
            content = "\n\n".join([
                f"제목: {r.get('title', '')}\n내용: {r.get('content', '')[:300]}"
                for r in results
            ])
            print(f"✅ {len(results)}개 결과 발견")
            return content
        else:
            print("⚠️ 결과 없음")
            return "검색 결과 없음"
    except Exception as e:
        print(f"❌ 오류: {e}")
        return f"검색 오류: {str(e)}"


class KIPRISPatentTool:
    def __init__(self):
        self.service_key = os.getenv("KIPRIS_SERVICE_KEY")
        self.base_url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchService/getAdvancedSearch"
    
    def search_patents(self, keyword: str, max_results: int = 5) -> List[Dict]:
        try:
            if not self.service_key:
                return [{'title': f'{keyword} 관련 특허', 'applicant': '기술개발회사'}]
            
            params = {
                'inventionTitle': keyword,
                'patent': 'true',
                'numOfRows': max_results,
                'ServiceKey': self.service_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            if response.status_code != 200:
                return []
            
            root = ET.fromstring(response.content)
            patents = []
            
            for item in root.findall('.//item'):
                patent = {
                    'title': self._get_text(item, 'inventionTitle'),
                    'applicant': self._get_text(item, 'applicantName'),
                    'register_number': self._get_text(item, 'registerNumber')
                }
                patents.append(patent)
            
            return patents
        except:
            return []
    
    def _get_text(self, element, tag):
        found = element.find(tag)
        return found.text if found is not None and found.text else ""


@tool
def kipris_search_tool(query: str) -> str:
    """
    KIPRIS에서 특허 정보를 검색합니다.
    
    Args:
        query: 검색할 특허 키워드 (예: "QG3030 신약")
    
    Returns:
        검색된 특허 정보
    """
    print(f"🏛️ KIPRIS 특허 검색: {query}")
    
    try:
        patents = _kipris_tool.search_patents(query, 5)
        
        if patents:
            content = "\n\n".join([
                f"특허명: {p.get('title', '')}\n출원인: {p.get('applicant', '')}\n등록번호: {p.get('register_number', '')}"
                for p in patents
            ])
            print(f"✅ {len(patents)}개 특허 발견")
            return content
        else:
            print("⚠️ 특허 없음")
            return "특허 검색 결과 없음"
    except Exception as e:
        print(f"❌ 오류: {e}")
        return f"특허 검색 오류: {str(e)}"


if __name__ == "__main__":
    checkpoint_path = os.path.join(CHECKPOINT_DIR, "01_company_desc_semantic.json")
    
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        agent = TechSummaryAgent()
        
        for company_data in data[:1]:  # 테스트용 1개만
            result = agent.run(company_data)
            print(f"\n결과:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 파일 없음: {checkpoint_path}")
