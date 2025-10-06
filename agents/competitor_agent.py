# competitor_agent.py

from InvestmentState import InvestmentState
from tavily import TavilyClient
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
from dotenv import load_dotenv
import os
import sys
import json
import re
from typing import Dict, Any

# 윈도우 인코딩 설정 (기존 유지)
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

os.environ['PYTHONIOENCODING'] = 'utf-8'

load_dotenv()


class CompetitorAgent:
    def __init__(self):
        # Tavily 클라이언트
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        # LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Tool 설정
        self.competitor_search_tool = Tool(
            name="competitor_search",
            func=self.search_competitor,
            description="""회사이름과 핵심기술을 기반으로 경쟁사를 검색합니다. 
            입력 예시: 'EverEx 헬스케어 AI 기술 전문 기업 경쟁사' 등.
            이 도구는 시장에서 유사한 기술이나 제품을 제공하는 경쟁사를 찾는데 사용됩니다."""
        )
        
        # System Message (기존 그대로)
        system_message = """당신은 경쟁사 분석 전문가입니다. 
        주어진 회사이름과 핵심기술을 바탕으로 가장 적합한 경쟁사 1개를 찾아야 합니다.

        분석 절차:
        1. 회사이름과 핵심기술을 조합하여 경쟁사를 검색합니다
        2. 검색 결과에서 가장 관련성 높은 경쟁사 후보들을 파악합니다
        3. 필요시 각 후보 회사에 대한 상세 정보를 추가 검색합니다
        4. 다음 기준으로 최종 경쟁사 1개를 선정합니다:
           - 핵심기술의 유사성
           - 시장 포지션의 직접적 경쟁 관계
           - 제품/서비스의 중복도
           - 타겟 고객층의 유사성

        최종 결과는 반드시 다음 JSON 형식으로만 제공하세요 (다른 설명 없이):
        {
            "main_competitors": "경쟁사 회사명 (1개만)",
            "competitor_profiles": "경쟁사의 설립연도, 규모, 자금 조달현황 & 주요 제품/서비스",
            "market_positioning": "타겟 기업 vs 경쟁사의 포지셔닝 맵, 업계 순위",
            "product_comparison": "기능, 가격, 타겟 고객 비교, 기술적 우위 요소",
            "unique_value_props": "타겟 기업만의 강점, 경쟁우위",
            "threat_analysis": "경쟁사의 위협 요소",
            "market_share": "타겟 기업 및 경쟁사의 시장 점유율",
            "reference_urls": ["참고 URL 목록"]
        }
        """
        
        # Prompt (기존 그대로)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Agent 생성 (기존 그대로)
        tools = [self.competitor_search_tool]
        agent = create_openai_functions_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            return_intermediate_steps=True
        )
    
    def search_competitor(self, query: str) -> str:
        """Tavily로 경쟁사 검색 (기존 로직 100% 유지)"""
        try:
            if isinstance(query, bytes):
                query = query.decode('utf-8')
            
            response = self.tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_domains=["crunchbase.com", "reuters.com", "bloomberg.com", "techcrunch.com"],
                include_answer=True
            )
            
            results = []
            
            if response.get('answer'):
                answer = str(response['answer'])
                results.append(f"요약: {answer}\n")
            
            results.append("검색 결과:")
            for idx, result in enumerate(response.get('results', []), 1):
                title = str(result.get('title', 'N/A'))
                url = str(result.get('url', 'N/A'))
                content = str(result.get('content', 'N/A'))[:200]
                score = str(result.get('score', 'N/A'))
                
                results.append(f"\n{idx}. {title}")
                results.append(f"   URL: {url}")
                results.append(f"   내용: {content}...")
                results.append(f"   점수: {score}")
            
            return "\n".join(results)
        
        except Exception as e:
            error_msg = str(e)
            return f"검색 중 오류 발생: {error_msg}"
    
    def find_competitor(self, company_name: str, core_technology: str) -> Dict[str, Any]:
        """Agent 실행 (기존 로직 100% 유지)"""
        if isinstance(company_name, bytes):
            company_name = company_name.decode('utf-8')
        if isinstance(core_technology, bytes):
            core_technology = core_technology.decode('utf-8')
        
        query = f"""
        회사: {company_name}
        핵심기술: {core_technology}
        
        위 회사의 가장 직접적인 경쟁사 1개를 찾아주세요.
        답변은 반드시 한국어로 작성해주세요.
        """
        
        result = self.agent_executor.invoke({"input": query})
        
        return {
            "query": query,
            "competitor_analysis": result["output"],
            "intermediate_steps": result.get("intermediate_steps", [])
        }
    
    def parse_competitor_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """JSON 파싱 (기존 로직 100% 유지)"""
        try:
            json_match = re.search(r'\{[\s\S]*\}', analysis_text)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                return {
                    "main_competitors": "N/A",
                    "competitor_profiles": analysis_text,
                    "market_positioning": "N/A",
                    "product_comparison": "N/A",
                    "unique_value_props": "N/A",
                    "threat_analysis": "N/A",
                    "market_share": "N/A",
                    "reference_urls": []
                }
        except:
            return {
                "main_competitors": "N/A",
                "competitor_profiles": analysis_text,
                "market_positioning": "N/A",
                "product_comparison": "N/A",
                "unique_value_props": "N/A",
                "threat_analysis": "N/A",
                "market_share": "N/A",
                "reference_urls": []
            }
    
    def run(self, state: InvestmentState) -> InvestmentState:
        """✨ State 기반 실행 (새로 추가된 유일한 메서드)"""
        company_name = state.company_name or "알 수 없는 회사"
        core_technology = state.core_tech or "핵심 기술"
        
        print("\n" + "="*80)
        print(f"🔍 경쟁사 분석 중: {company_name}")
        print("="*80)
        
        try:
            # 기존 find_competitor 사용
            result = self.find_competitor(company_name, core_technology)
            analysis_output = result["competitor_analysis"]
            
            # 기존 parse_competitor_analysis 사용
            competitor_data = self.parse_competitor_analysis(analysis_output)
            
            # State 업데이트
            state.main_competitors = competitor_data.get("main_competitors", "")
            state.competitor_profiles = competitor_data.get("competitor_profiles", "")
            state.market_positioning = competitor_data.get("market_positioning", "")
            state.product_comparison = competitor_data.get("product_comparison", "")
            state.unique_value_props = competitor_data.get("unique_value_props", "")
            state.threat_analysis = competitor_data.get("threat_analysis", "")
            state.market_share = competitor_data.get("market_share", "")
            state.reference_urls = competitor_data.get("reference_urls", [])
            
            print(f"\n✓ {company_name} 분석 완료")
            
        except Exception as e:
            print(f"\n✗ {company_name} 분석 실패: {e}")
            state.main_competitors = "분석 실패"
            state.competitor_profiles = str(e)
            state.market_positioning = "N/A"
            state.product_comparison = "N/A"
            state.unique_value_props = "N/A"
            state.threat_analysis = "N/A"
            state.market_share = "N/A"
            state.reference_urls = []
        
        return state