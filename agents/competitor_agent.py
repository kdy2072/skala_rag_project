# -*- coding: utf-8 -*-

import os
import sys
import json
import re
from typing import List, Dict, Any
from tavily import TavilyClient
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage

if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

os.environ['PYTHONIOENCODING'] = 'utf-8'

tavily_client = TavilyClient(api_key="")

def search_competitor(query: str) -> str:
    try:
        if isinstance(query, bytes):
            query = query.decode('utf-8')
        
        response = tavily_client.search(
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


competitor_search_tool = Tool(
    name="competitor_search",
    func=search_competitor,
    description="""회사이름과 핵심기술을 기반으로 경쟁사를 검색합니다. 
    입력 예시: 'EverEx 헬스케어 AI 기술 전문 기업 경쟁사' 등.
    이 도구는 시장에서 유사한 기술이나 제품을 제공하는 경쟁사를 찾는데 사용됩니다."""
)

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
    "main_competitors": "경쟁사 회사 명",
    "competitor_profiles": "경쟁사의 설립연도, 규모, 자금 조달현황 & 주요 제품/서비스",
    "market_positioning": "타겟 기업 vs 경쟁사들의 포지셔닝 맵, 업계 순위",
    "product_comparison": "기능, 가격, 타겟 고객 비교, 기술적 우위 요소",
    "unique_value_props": "타겟 기업만의 강점, 경쟁우위",
    "threat_analysis": "경쟁사의 위협 요소",
    "MarketShare": "타겟 기업 및 경쟁사의 시장 점유율",
    "reference_urls": ["참고 URL 목록"]
}
"""

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_message),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=""
)

tools = [competitor_search_tool]
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
    return_intermediate_steps=True
)


def find_competitor(company_name: str, core_technology: str) -> Dict[str, Any]:
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
    
    result = agent_executor.invoke({"input": query})
    
    return {
        "query": query,
        "competitor_analysis": result["output"],
        "intermediate_steps": result.get("intermediate_steps", [])
    }


def parse_competitor_analysis(analysis_text: str) -> Dict[str, Any]:
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
                "MarketShare": "N/A",
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
            "MarketShare": "N/A",
            "reference_urls": []
        }


def load_companies_from_json(json_file_path: str) -> List[Dict[str, str]]:
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"JSON 파일 로드 오류: {e}")
        return []


def save_results_to_json(json_file_path: str, companies: List[Dict[str, Any]]):
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(companies, f, ensure_ascii=False, indent=4)
        print(f"\n결과가 {json_file_path}에 저장되었습니다.")
    except Exception as e:
        print(f"JSON 파일 저장 오류: {e}")


def analyze_multiple_companies(companies: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    updated_companies = []
    
    for idx, company in enumerate(companies, 1):
        company_name = company.get("company_name", "")
        core_technology = company.get("core_tech", "")
        
        print("\n" + "="*80)
        print(f"[{idx}/{len(companies)}] 분석 중: {company_name}")
        print("="*80)
        
        try:
            result = find_competitor(company_name, core_technology)
            analysis_output = result["competitor_analysis"]
            
            competitor_data = parse_competitor_analysis(analysis_output)
            
            updated_company = company.copy()
            updated_company.update(competitor_data)
            
            updated_companies.append(updated_company)
            
            print(f"\n✓ {company_name} 분석 완료")
            
        except Exception as e:
            print(f"\n✗ {company_name} 분석 실패: {e}")
            updated_company = company.copy()
            updated_company.update({
                "main_competitors": "분석 실패",
                "competitor_profiles": str(e),
                "market_positioning": "N/A",
                "product_comparison": "N/A",
                "unique_value_props": "N/A",
                "threat_analysis": "N/A",
                "MarketShare": "N/A",
                "reference_urls": []
            })
            updated_companies.append(updated_company)
    
    return updated_companies


if __name__ == "__main__":
    
    json_file_path = "C:/Users/SKAX/Desktop/WORKBOOK/0929 RAG practice/skala_rag_project/checkpoint/01_company_desc_semantic.json"
    
    companies = load_companies_from_json(json_file_path)
    
    if not companies:
        print("JSON 파일에서 회사 정보를 로드할 수 없습니다.")
    else:
        print(f"\n총 {len(companies)}개 회사 정보를 로드했습니다.")
        
        updated_companies = analyze_multiple_companies(companies)
        
        save_results_to_json(json_file_path, updated_companies)
        
        print("\n" + "="*80)
        print("전체 경쟁사 분석 결과")
        print("="*80)
        
        for idx, company in enumerate(updated_companies, 1):
            print(f"\n[{idx}] {company['company_name']}")
            print("-" * 80)
            print(f"경쟁사: {company.get('main_competitors', 'N/A')}")
            print(f"경쟁사 프로필: {company.get('competitor_profiles', 'N/A')[:100]}...")
            print(f"시장 포지셔닝: {company.get('market_positioning', 'N/A')[:100]}...")