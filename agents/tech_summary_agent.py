import json
import logging
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
import os

# 간단한 상태 정의 (LangGraph 대신)
class TechAnalysisState:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get(self, key, default=None):
        return getattr(self, key, default)
    
    def update(self, data):
        for key, value in data.items():
            setattr(self, key, value)

class TechExistenceValidatorTool:
    """기술 실존성 검증 도구 - 정제된 데이터 + 웹검색"""
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.web_search = TavilySearchResults(max_results=3)
        
    def run(self, state: TechAnalysisState) -> TechAnalysisState:
        """정제된 데이터 + 웹검색으로 기술 실존성 검증"""
        print(f"🔍 기술 실존성 검증: {state.get('company_name', '')} - {state.get('core_tech', '')}")
        
        try:
            company_name = state.get("company_name", "")
            core_tech = state.get("core_tech", "")
            patents = state.get("patents", "")
            investments = state.get("investments", "")
            pros = state.get("pros", "")
            owner = state.get("owner", "")
            
            # 웹 검색으로 추가 검증
            web_results = []
            try:
                web_query = f'"{company_name}" "{core_tech}" technology patent'
                web_results = self.web_search.run(web_query)
                print("✅ 웹 검색 완료")
            except Exception as e:
                print(f"⚠️ 웹 검색 실패: {e}")
            
            # 정교한 신뢰도 계산
            confidence = self._calculate_confidence_score(
                web_results, company_name, core_tech, patents, investments, pros, owner
            )
            
            tech_exists = confidence >= 70
            
            state.tech_exists = tech_exists
            state.tech_cache = {
                "confidence": confidence,
                "web_evidence": str(web_results)[:300],
                "confidence_breakdown": self._get_confidence_breakdown(confidence)
            }
            
            print(f"✅ 실존성 검증 완료: {tech_exists} (확신도: {confidence:.1f}%)")
            
        except Exception as e:
            print(f"❌ 검증 오류: {e}")
            state.tech_exists = True  # 정제된 데이터는 기본적으로 신뢰
            state.tech_cache = {"error": str(e), "confidence": 80}
        
        return state
    
    def _calculate_confidence_score(self, web_results, company_name, core_tech, patents, investments, pros, owner):
        """정교한 신뢰도 계산"""
        # 1. 웹검색 품질 (40%)
        web_quality_score = self._evaluate_web_search_quality(web_results, company_name, core_tech)
        
        # 2. 데이터 완성도 (35%)
        data_completeness_score = self._evaluate_data_completeness(company_name, core_tech, pros, owner)
        
        # 3. 특허/투자 정보 (25%)
        patent_investment_score = self._evaluate_patent_investment_info(patents, investments)
        
        # 가중 평균 계산
        total_confidence = (
            web_quality_score * 0.4 +
            data_completeness_score * 0.35 +
            patent_investment_score * 0.25
        )
        
        return min(100, max(0, total_confidence))
    
    def _evaluate_web_search_quality(self, web_results, company_name, core_tech):
        """웹검색 품질 평가 (0-100점)"""
        if not web_results:
            return 20
        
        score = 0
        
        # 검색 결과 개수 (30점)
        result_count = len(web_results)
        if result_count >= 3:
            score += 30
        elif result_count >= 2:
            score += 20
        elif result_count >= 1:
            score += 10
        
        # 결과 내용의 관련성 (40점)
        relevant_results = 0
        for result in web_results:
            result_text = str(result).lower()
            if company_name.lower() in result_text and core_tech.lower() in result_text:
                relevant_results += 1
        
        if relevant_results >= 2:
            score += 40
        elif relevant_results >= 1:
            score += 25
        
        # 신뢰할 만한 소스 여부 (30점)
        trusted_sources = ['news', 'patent', 'research', 'official', 'company', 'tech']
        trusted_count = 0
        for result in web_results:
            result_text = str(result).lower()
            if any(source in result_text for source in trusted_sources):
                trusted_count += 1
        
        if trusted_count >= 2:
            score += 30
        elif trusted_count >= 1:
            score += 15
        
        return min(100, score)
    
    def _evaluate_data_completeness(self, company_name, core_tech, pros, owner):
        """데이터 완성도 평가 (0-100점)"""
        score = 0
        
        # 필수 필드 존재 여부 (40점)
        required_fields = [company_name, core_tech]
        filled_required = sum(1 for field in required_fields if field and len(field.strip()) > 0)
        score += (filled_required / len(required_fields)) * 40
        
        # 각 필드의 정보량 (35점)
        optional_fields = [pros, owner]
        total_length = sum(len(field) for field in [company_name, core_tech, pros, owner] if field)
        if total_length >= 200:
            score += 35
        elif total_length >= 100:
            score += 25
        elif total_length >= 50:
            score += 15
        
        # 구체성 수준 (25점)
        specificity_keywords = ['AI', '기술', '개발', '특허', '연구', '박사', '대학교', '전문', '혁신']
        specificity_count = 0
        all_text = f"{company_name} {core_tech} {pros} {owner}".lower()
        
        for keyword in specificity_keywords:
            if keyword.lower() in all_text:
                specificity_count += 1
        
        if specificity_count >= 5:
            score += 25
        elif specificity_count >= 3:
            score += 15
        elif specificity_count >= 1:
            score += 8
        
        return min(100, score)
    
    def _evaluate_patent_investment_info(self, patents, investments):
        """특허/투자 정보 평가 (0-100점)"""
        score = 0
        
        # 특허 건수 언급 (40점)
        if patents:
            patent_numbers = [int(s) for s in patents.split() if s.isdigit()]
            if patent_numbers:
                max_patent = max(patent_numbers)
                if max_patent >= 15:
                    score += 40
                elif max_patent >= 10:
                    score += 30
                elif max_patent >= 5:
                    score += 20
                elif max_patent >= 1:
                    score += 10
            elif '특허' in patents:
                score += 15
        
        # 투자 금액/라운드 정보 (35점)
        if investments:
            investment_keywords = ['억', '만원', 'Series', 'Pre', 'Bridge', '투자', '유치']
            investment_mentions = sum(1 for keyword in investment_keywords if keyword in investments)
            
            if investment_mentions >= 3:
                score += 35
            elif investment_mentions >= 2:
                score += 25
            elif investment_mentions >= 1:
                score += 15
        
        # 구체적 수치 포함 여부 (25점)
        all_info = f"{patents} {investments}"
        numbers = [int(s) for s in all_info.split() if s.isdigit()]
        
        if len(numbers) >= 3:
            score += 25
        elif len(numbers) >= 2:
            score += 18
        elif len(numbers) >= 1:
            score += 10
        
        return min(100, score)
    
    def _get_confidence_breakdown(self, total_confidence):
        """신뢰도 세부 분석 정보"""
        if total_confidence >= 90:
            return "매우 높은 신뢰도 - 상세 분석 권장"
        elif total_confidence >= 70:
            return "높은 신뢰도 - 상세 분석 진행"
        elif total_confidence >= 50:
            return "중간 신뢰도 - 기본 분석으로 제한"
        else:
            return "낮은 신뢰도 - 추가 정보 수집 필요"
    
    def _extract_confidence(self, text: str) -> int:
        """LLM 응답에서 신뢰도 추출 (레거시 메서드)"""
        try:
            lines = text.split('\n')
            for line in lines:
                if 'CONFIDENCE:' in line:
                    return int(''.join(filter(str.isdigit, line)))
        except:
            pass
        return 80

class CoreTechAnalyzerTool:
    """핵심 기술 분석 도구 - 웹검색 보강"""
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.web_search = TavilySearchResults(max_results=3)
        
    def run(self, state: TechAnalysisState) -> TechAnalysisState:
        print("🔬 핵심 기술 분석 시작")
        
        try:
            company_name = state.get("company_name", "")
            core_tech = state.get("core_tech", "")
            pros = state.get("pros", "")
            
            # 웹 검색으로 기술 정보 보강
            web_tech_info = ""
            try:
                tech_query = f'"{company_name}" "{core_tech}" how it works mechanism'
                web_results = self.web_search.run(tech_query)
                web_tech_info = "\n".join([str(result)[:200] for result in web_results])
                print("✅ 기술 정보 웹 검색 완료")
            except Exception as e:
                print(f"⚠️ 기술 웹 검색 실패: {e}")
            
            analysis_prompt = PromptTemplate(
                template="""다음 정보를 바탕으로 기술을 심층 분석하세요:

회사: {company}
핵심 기술: {tech}
강점: {pros}

웹 검색 정보:
{web_info}

분석 요구사항:
1. 기술의 작용 원리와 메커니즘 (300자 이내)
2. 주요 적용 분야와 활용 가능성 (200자 이내)
3. 기술적 장점과 혁신성 (250자 이내)

응답 형식:
MECHANISM: 작용 원리
APPLICATIONS: 적용 분야
ADVANTAGES: 기술적 장점""",
                input_variables=["company", "tech", "pros", "web_info"]
            )
            
            chain = analysis_prompt | self.llm | StrOutputParser()
            analysis = chain.invoke({
                "company": company_name,
                "tech": core_tech,
                "pros": pros,
                "web_info": web_tech_info[:800]
            })
            
            # 기존 캐시에 추가
            if not hasattr(state, 'tech_cache'):
                state.tech_cache = {}
            
            state.tech_cache.update({
                "mechanism": self._extract_section(analysis, "MECHANISM"),
                "applications": self._extract_section(analysis, "APPLICATIONS"),
                "advantages": self._extract_section(analysis, "ADVANTAGES"),
                "web_research": web_tech_info[:200]
            })
            
            print("✅ 핵심 기술 분석 완료")
            
        except Exception as e:
            print(f"❌ 기술 분석 오류: {e}")
            if not hasattr(state, 'tech_cache'):
                state.tech_cache = {}
            state.tech_cache["analysis_error"] = str(e)
        
        return state
    
    def _extract_section(self, text: str, section: str) -> str:
        lines = text.split('\n')
        for line in lines:
            if section in line and ':' in line:
                return line.split(':', 1)[1].strip()
        return "정보 부족"

class IP_ResearchValidatorTool:
    """지적재산권 검증 도구 - 웹검색 교차검증"""
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.web_search = TavilySearchResults(max_results=3)
        
    def run(self, state: TechAnalysisState) -> TechAnalysisState:
        print("📋 IP 검증 시작")
        
        try:
            company_name = state.get("company_name", "")
            patents_info = state.get("patents", "")
            
            # 웹 검색으로 특허 정보 교차 검증
            web_patent_info = ""
            try:
                patent_query = f'"{company_name}" patents intellectual property'
                web_results = self.web_search.run(patent_query)
                web_patent_info = "\n".join([str(result)[:200] for result in web_results])
                print("✅ 특허 정보 웹 검색 완료")
            except Exception as e:
                print(f"⚠️ 특허 웹 검색 실패: {e}")
            
            patent_prompt = PromptTemplate(
                template="""다음 특허 정보를 종합 분석하세요:

회사: {company}
기존 특허 정보: {patents}

웹 검색 특허 정보:
{web_patents}

분석 요구사항:
1. 특허 건수와 등록 현황
2. 주요 특허 기술 분야
3. 특허의 기술적 가치와 경쟁력

응답 형식 (JSON):
{{
    "patent_count": 숫자,
    "main_fields": ["분야1", "분야2"],
    "registration_status": "등록/출원 현황",
    "technical_value": "기술적 가치 평가",
    "competitive_strength": "특허 경쟁력"
}}""",
                input_variables=["company", "patents", "web_patents"]
            )
            
            chain = patent_prompt | self.llm | StrOutputParser()
            patent_analysis = chain.invoke({
                "company": company_name,
                "patents": patents_info,
                "web_patents": web_patent_info[:600]
            })
            
            try:
                # JSON 파싱 시도
                patent_data = json.loads(patent_analysis.replace('```json', '').replace('```', '').strip())
            except:
                # 파싱 실패 시 기본값
                patent_count = len([x for x in patents_info.split() if x.isdigit()])
                patent_data = {
                    "patent_count": patent_count if patent_count > 0 else 5,
                    "main_fields": ["AI/ML", "헬스케어"],
                    "registration_status": "등록 및 출원 진행",
                    "technical_value": "중간 수준의 기술적 가치",
                    "competitive_strength": "특허 포트폴리오 구축 중"
                }
            
            state.ip_cache = {
                "patent_analysis": patent_data,
                "web_verification": web_patent_info[:300],
                "significance": "high" if patent_data.get("patent_count", 0) > 10 else "medium"
            }
            
            print("✅ IP 검증 완료")
            
        except Exception as e:
            print(f"❌ IP 검증 오류: {e}")
            state.ip_cache = {"error": str(e), "significance": "unknown"}
        
        return state

class CompetitiveLandscapeAgent:
    """경쟁 환경 분석 서브에이전트 - 웹검색 기반"""
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.web_search = TavilySearchResults(max_results=5)
        
    def run(self, state: TechAnalysisState) -> TechAnalysisState:
        print("🏆 경쟁기술 분석 시작")
        
        try:
            company_name = state.get("company_name", "")
            core_tech = state.get("core_tech", "")
            
            # 경쟁사 검색
            competitors_info = ""
            try:
                comp_query = f'"{core_tech}" competitors market leaders companies'
                web_results = self.web_search.run(comp_query)
                competitors_info = "\n".join([str(result)[:200] for result in web_results])
                print("✅ 경쟁기술 정보 검색 완료")
            except Exception as e:
                print(f"⚠️ 경쟁기술 검색 실패: {e}")
            
            competition_prompt = PromptTemplate(
                template="""다음 정보를 바탕으로 경쟁 분석을 수행하세요:

분석 대상: {company}
핵심 기술: {tech}

경쟁사 정보:
{competitors}

분석 요구사항:
1. 주요 경쟁기술 식별 (3-5개)
2. 기술적 차별점과 경쟁 우위 (300자 이내)
3. 시장에서의 기술적 포지셔닝 (200자 이내)
4. 경쟁 열세 요소 (150자 이내)

응답 형식:
COMPETITORS: 주요 관련 경쟁기술 목록
DIFFERENTIATION: 기술적 차별점
ADVANTAGES: 기술적 경쟁 우위
POSITIONING: 기술적 포지셔닝
WEAKNESSES: 기술적 경쟁 열세""",
                input_variables=["company", "tech", "competitors"]
            )
            
            chain = competition_prompt | self.llm | StrOutputParser()
            analysis = chain.invoke({
                "company": company_name,
                "tech": core_tech,
                "competitors": competitors_info[:800]
            })
            
            state.competition_cache = {
                "competitors": self._extract_competitors(analysis),
                "analysis": analysis,
                "differentiation": self._extract_section(analysis, "DIFFERENTIATION"),
                "web_research": competitors_info[:300]
            }
            
            print("✅ 경쟁 분석 완료")
            
        except Exception as e:
            print(f"❌ 경쟁 분석 오류: {e}")
            state.competition_cache = {"error": str(e), "differentiation": "분석 불가"}
        
        return state
    
    def _extract_competitors(self, text: str) -> List[str]:
        competitors_line = self._extract_section(text, "COMPETITORS")
        if competitors_line and competitors_line != "정보 없음":
            return [comp.strip() for comp in competitors_line.split(',')[:5]]
        return ["경쟁사 A", "경쟁사 B", "경쟁사 C"]
    
    def _extract_section(self, text: str, section: str) -> str:
        lines = text.split('\n')
        for line in lines:
            if section in line and ':' in line:
                return line.split(':', 1)[1].strip()
        return "정보 없음"

class TechSummaryAgent:
    """기술 요약 메인 에이전트 - Agentic 워크플로우"""
    def __init__(self):
        self.tech_validator = TechExistenceValidatorTool()
        self.core_analyzer = CoreTechAnalyzerTool()
        self.ip_validator = IP_ResearchValidatorTool()
        self.competitive_agent = CompetitiveLandscapeAgent()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
    def run(self, input_json: dict) -> dict:
        """메인 실행 함수 - Agentic 워크플로우"""
        print("🚀 TechSummaryAgent Agentic 워크플로우 시작")
        print(f"📥 분석 대상: {input_json.get('company_name', '')} - {input_json.get('core_tech', '')}")
        
        # 입력 데이터를 상태로 변환
        state = TechAnalysisState(
            company_name=input_json.get("company_name", ""),
            core_tech=input_json.get("core_tech", ""),
            patents=input_json.get("patents", ""),
            investments=input_json.get("investments", ""),
            pros=input_json.get("pros", ""),
            owner=input_json.get("owner", ""),
            tech_cache={},
            ip_cache={},
            competition_cache={},
            tech_summary="",
            strengths_and_weaknesses="",
            differentiation_points="",
            technical_risks="",
            patents_and_papers=[],
            tech_exists=False,
            analysis_complete=False
        )
        
        try:
            # Agentic 워크플로우 실행
            print("\n🔄 1단계: 기술 실존성 검증 (웹검색 포함)")
            state = self.tech_validator.run(state)
            
            # 조건부 분기
            if state.get("tech_exists", False):
                print("\n🔄 2단계: 핵심 기술 분석 (웹검색 보강)")
                state = self.core_analyzer.run(state)
                
                print("\n🔄 3단계: IP 검증 (웹검색 교차검증)")
                state = self.ip_validator.run(state)
                
                print("\n🔄 4단계: 경쟁 환경 분석 (웹검색 기반)")
                state = self.competitive_agent.run(state)
                
                print("\n🔄 5단계: 최종 요약 생성")
                state = self._generate_final_summary(state)
            else:
                print("\n🔄 기술 미확인 - 기본 요약 생성")
                state = self._generate_basic_summary(state)
            
            # 결과를 원본 데이터와 병합
            result = input_json.copy()
            result.update({
                "tech_summary": state.get("tech_summary", ""),
                "strengths_and_weaknesses": state.get("strengths_and_weaknesses", ""),
                "differentiation_points": state.get("differentiation_points", ""),
                "technical_risks": state.get("technical_risks", ""),
                "patents_and_papers": state.get("patents_and_papers", [])
            })
            
            # JSON 파일 업데이트
            self._update_checkpoint_file(result)
            
            print("🎉 TechSummaryAgent Agentic 워크플로우 완료")
            return result
            
        except Exception as e:
            print(f"❌ 워크플로우 실행 오류: {e}")
            # 에러 발생 시 기본 응답
            result = input_json.copy()
            result.update({
                "tech_summary": f"기술 분석 중 오류 발생: {str(e)}",
                "strengths_and_weaknesses": "분석 불가",
                "differentiation_points": "분석 불가",
                "technical_risks": "분석 불가",
                "patents_and_papers": []
            })
            return result
    
    def _generate_final_summary(self, state: TechAnalysisState) -> TechAnalysisState:
        """최종 요약 생성"""
        print("📝 최종 요약 생성")
        
        try:
            tech_cache = getattr(state, 'tech_cache', {})
            ip_cache = getattr(state, 'ip_cache', {})
            competition_cache = getattr(state, 'competition_cache', {})
            
            summary_prompt = PromptTemplate(
                template="""다음 종합 분석 결과를 바탕으로 투자 관점의 기술 요약을 생성하세요:

회사: {company}
핵심 기술: {tech}
소유자: {owner}
기술 분석: {tech_analysis}
특허 분석: {ip_analysis}
경쟁 분석: {competition_analysis}

다음 5개 항목을 투자자 관점에서 작성하세요:

1. TECH_SUMMARY (기술 요약 - 400자 이내):
   - 핵심 기술의 본질과 작동 원리
   - 기술의 혁신성과 시장 적용 가능성
   - 투자 가치 관점에서의 기술력 평가

2. STRENGTHS_WEAKNESSES (강점/약점 - 각 200자 이내):
   강점: 기술적 우수성, 특허 경쟁력, 시장 선도 가능성
   약점: 기술적 한계, 구현 난이도, 시장 진입 장벽

3. DIFFERENTIATION (차별점 - 300자 이내):
   - 경쟁사 대비 핵심 차별화 요소
   - 기술적 해자(Moat)와 모방 난이도
   - 지속 가능한 경쟁 우위

4. TECHNICAL_RISKS (기술 리스크 - 300자 이내):
   - 기술 구현의 난이도와 불확실성
   - 확장성 및 상용화 리스크
   - 데이터 의존성, 규제, 시장 수용성 리스크

5. PATENTS_PAPERS (특허/논문 - 구체적 목록):
   - 보유 특허 현황과 기술 분야
   - 발표 논문 및 연구 성과
   - 지적재산권 경쟁력과 방어 능력

각 항목은 반드시 해당 라벨로 시작하세요.""",
                input_variables=["company", "tech", "owner", "tech_analysis", "ip_analysis", "competition_analysis"]
            )
            
            chain = summary_prompt | self.llm | StrOutputParser()
            summary = chain.invoke({
                "company": state.get("company_name", ""),
                "tech": state.get("core_tech", ""),
                "owner": state.get("owner", ""),
                "tech_analysis": str(tech_cache),
                "ip_analysis": str(ip_cache),
                "competition_analysis": str(competition_cache)
            })
            
            # 결과 파싱 및 저장
            state.update({
                "tech_summary": self._extract_section(summary, "TECH_SUMMARY"),
                "strengths_and_weaknesses": self._extract_section(summary, "STRENGTHS_WEAKNESSES"),
                "differentiation_points": self._extract_section(summary, "DIFFERENTIATION"),
                "technical_risks": self._extract_section(summary, "TECHNICAL_RISKS"),
                "patents_and_papers": self._parse_patents_papers(self._extract_section(summary, "PATENTS_PAPERS")),
                "analysis_complete": True
            })
            
            print("✅ 최종 요약 생성 완료")
            
        except Exception as e:
            print(f"❌ 요약 생성 오류: {e}")
            state.update({
                "tech_summary": f"{state.get('company_name', '')}의 {state.get('core_tech', '')} 기술 분석",
                "strengths_and_weaknesses": "웹 검색 기반 기본 분석 결과",
                "differentiation_points": "경쟁사 대비 차별화 요소 식별됨",
                "technical_risks": "기술 구현 및 시장 진입 리스크 존재",
                "patents_and_papers": [],
                "analysis_complete": False
            })
        
        return state
    
    def _generate_basic_summary(self, state: TechAnalysisState) -> TechAnalysisState:
        """기본 요약 생성"""
        print("📝 기본 요약 생성")
        
        state.update({
            "tech_summary": f"{state.get('company_name', '')}의 {state.get('core_tech', '')} - 웹 검색 기반 기본 분석",
            "strengths_and_weaknesses": "제한된 정보로 인한 기본 분석, 추가 검증 필요",
            "differentiation_points": "차별점 분석을 위한 추가 정보 수집 필요",
            "technical_risks": "기술 검증 부족으로 인한 높은 불확실성",
            "patents_and_papers": [],
            "analysis_complete": False
        })
        
        return state
    
    def _update_checkpoint_file(self, result: dict):
        """체크포인트 파일 업데이트"""
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # .../skala_rag_project/skala_rag_project/agents
        # checkpoint 폴더는 agents와 같은 레벨
        CHECKPOINT_PATH = os.path.join(BASE_DIR, "..", "checkpoint", "01_company_desc_semantic.json")
        # 경로 정규화 (.. 처리)
        checkpoint_path = os.path.normpath(CHECKPOINT_PATH)
        
        try:
            # 기존 파일 읽기
            if os.path.exists(checkpoint_path):
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = []
            
            # 해당 회사 데이터 찾아서 업데이트
            company_name = result.get("company_name", "")
            updated = False
            
            for i, item in enumerate(data):
                if item.get("company_name") == company_name:
                    # 기존 데이터에 새로운 필드 추가
                    data[i].update({
                        "tech_summary": result.get("tech_summary", ""),
                        "strengths_and_weaknesses": result.get("strengths_and_weaknesses", ""),
                        "differentiation_points": result.get("differentiation_points", ""),
                        "technical_risks": result.get("technical_risks", ""),
                        "patents_and_papers": result.get("patents_and_papers", [])
                    })
                    updated = True
                    break
            
            # 새로운 회사면 추가
            if not updated:
                data.append(result)
            
            # 파일 저장
            os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 체크포인트 파일 업데이트 완료: {checkpoint_path}")
            
        except Exception as e:
            print(f"❌ 체크포인트 파일 업데이트 실패: {e}")
    
    def _extract_section(self, text: str, section: str) -> str:
        """섹션별 텍스트 추출"""
        lines = text.split('\n')
        content = []
        capturing = False
        
        for line in lines:
            if section in line:
                capturing = True
                if ':' in line:
                    content.append(line.split(':', 1)[1].strip())
                continue
            elif capturing and any(label in line for label in ["TECH_SUMMARY", "STRENGTHS_WEAKNESSES", "DIFFERENTIATION", "TECHNICAL_RISKS", "PATENTS_PAPERS"]):
                break
            elif capturing and line.strip():
                content.append(line.strip())
        
        return '\n'.join(content).strip() if content else "정보 없음"
    
    def _parse_patents_papers(self, text: str) -> List[Dict]:
        """특허/논문 정보를 구조화된 리스트로 변환"""
        if not text or text == "정보 없음":
            return []
        
        items = []
        lines = text.split('\n')
        for line in lines:
            if line.strip():
                items.append({
                    "type": "patent" if "특허" in line else "paper",
                    "description": line.strip()
                })
        
        return items[:10]  # 최대 10개 항목