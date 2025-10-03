# Health Care Startup Investment Evaluation Agent
본 프로젝트는 헬스케어 스타트업에 대한 투자 가능성을 자동으로 평가하는 에이전트를 설계하고 구현한 실습 프로젝트입니다.

## Overview

- Objective : 헬스케어 스타트업의 핵심 기술력, 시장성, 경쟁사 비교 등을 기준으로 투자 적합성 분석
- Method : AI Agent ReAct + Agentic RAG + Agentic Tool Calling
- Tools : tavily, Custom Tool : Rag Research, TechExistenceValidatorTool, CoreTechAnalyzerTool, IP_ResearchValidatorTool

## Features

- PDF 자료 기반으로 스타트업 탐색 후 정보 추출
- 스타트업 별로 기술, 시장성, 경쟁사 정보 추출
- 추출한 정보를 기반으로 투자 판단 분류 (시장성, 기술력 기반으로 Scoredcard Method 방식 채택)
- 종합 투자 요약 출력 후 보고서 작성

## Tech Stack 

| Category   | Details                              |
|------------|--------------------------------------|
| Framework  | LangChain, Python, HugginFace        |
| LLM        | GPT-4o, GPT-4o-mini  |
| Retrieval  | FAISS, semantic chunking, flat index |
| model      | nlpai-lab/KURE-v1                    |

## Agents
 
- Explorer Agent: 임베딩된 기업 IR PDF를 기반으로 신뢰성 있는 기업의 핵심정보를 파악, 부족한 경우 외부 검색을 통해 재정립
- Tech Summary Agent: Agent 및 Tool AI 워크플로우를 활용하여 스타트업의 기술력을 종합적으로 분석하고 투자 관점에서 요약하는 Agentic RAG 시스템
- Market Eval Agent : 스타트업 핵심기술과 기업명을 바탕으로 시장성 및 규모를 조사 하는 에이전트
- Competitor Agent : 검색 엔진 API인 Tavily를 Tool로 활용해 타겟 회사의 경쟁 회사에 대해 조사하는 에이전트
- Investment Agent : Scorecard Method을 이용하여 기준 점수에 따라 투자 or 보류 결정 에이전트
- Report Agent : 투자로 결정난 스타트업에 대하여 보고서를 작성하는 에이전트

## Agents Detail

1)  Tech Summary Agent
     ## 핵심요소
     ### 1. RAG 기반 지능적 특허 검색
     - 기존: 하드코딩된 키워드
     - 혁신: RAG 증거에서 기술 관련 용어 자동 추출
     - 효과: 관련성 높은 특허 발견율 향상
     
     ### 2. 다단계 신뢰도 관리
     - 초기 신뢰도 → 관련성 검증 → 최종 신뢰도
     - 동적 분석 경로 결정
     - 품질 기반 출력 차별화
     
     ### 3. API 오류 복원력
     - KIPRIS API 키 오류 시 모의 데이터 제공
     - 워크플로우 중단 방지
     - 연속적 분석 보장
     
     ### 4. 투자자 중심 분석
     - 기술적 해자(Moat) 평가
     - 상용화 리스크 분석
     - 정량적 투자 가치 평가
      ## Agentic RAG 워크플로우 상세
      
      ### 1단계: 기술 실존성 검증 (tech_existence_check)
      **목적**: 입력 데이터 품질 평가 및 분석 경로 결정
      
      **로직**:
      - 회사명, 핵심기술, 소유자 정보 품질 평가 (40%)
      - 특허/투자 정보 존재성 검증 (30%)
      - 강점 정보 품질 평가 (30%)
      - **임계값**: 60점 이상 → 상세 분석, 미만 → 기본 분석
      
      **출력**: `confidence_score`, `tech_exists`
      
      ### 2단계: 병렬 데이터 수집 (data_collection)
      **목적**: 다중 소스 기반 증거 수집
      
      #### 2-1. RAG 검색
      - **쿼리**: `"{core_tech} 기술 특허 논문 연구"`
      - **필터**: 회사명 기반 문서 필터링
      - **결과**: 최대 5개 관련 문서
      
      #### 2-2. 웹 검색 (Tavily API)
      - **쿼리**: `"{company_name}" "{core_tech}" technology research patent`
      - **모드**: Advanced search
      - **결과**: 최대 5개 웹 결과
      
      #### 2-3. KIPRIS 특허 검색 (지능적 키워드 추출)
      **혁신 포인트**: RAG 기반 키워드 추출
      ```python
      # 키워드 추출 로직
      keywords = [company_name, core_tech]
      + 정규표현식 패턴 매칭:
        - r'\b[가-힣]{2,}기술\b'  # ~기술
        - r'\b[가-힣]{2,}시스템\b'  # ~시스템  
        - r'\b[A-Za-z]{3,}\b'  # 영문 기술용어
      ```
      - **API 파라미터**: `inventionTitle` (발명의명칭 직접 검색)
      - **오류 처리**: API 키 오류 시 모의 데이터 반환
      - **결과**: 최대 15개 특허 (중복 제거)
      
      ### 3단계: 기술 정의 분석 (tech_definition_analysis)
      **목적**: 기술의 본질과 작동원리 분석
      
      **분석 항목**:
      - 기술의 명확한 정의 (200자)
      - 작동 원리 및 메커니즘 MOA (300자)
      - 핵심 구성 요소 (150자)
      - 적용 분야 및 활용 방안 (200자)
      
      ### 4단계: 경쟁기술 분석 (competitive_tech_analysis)
      **목적**: 시장 내 경쟁 구도 및 차별점 분석
      
      **추가 웹 검색**: `"{core_tech}" competitors alternative technology market leaders`
      
      **분석 항목**:
      - 주요 경쟁기술 식별 (3-5개)
      - 경쟁기술 특징 및 장단점
      - 분석 대상 기술의 차별점
      - 기술적 해자(Moat) 평가
      - 경쟁 우위 지속가능성
      
      ### 5단계: 특허 심층 분석 (patent_deep_analysis)
      **목적**: 지적재산권 경쟁력 평가
      
      **분석 항목**:
      - 특허 포트폴리오 강도 평가
      - 핵심 특허와 주변 특허 구분
      - 특허 방어력 및 공격력 평가
      - 특허 공백 영역 식별
      - 지적재산권 리스크 평가
      
      ### 6단계: 리스크 평가 분석 (risk_assessment_analysis)
      **목적**: 기술 구현 및 상용화 리스크 종합 평가
      
      **분석 항목**:
      - 기술 구현 난이도 및 불확실성
      - 확장성 및 상용화 리스크
      - 데이터 의존성 리스크
      - 규제 및 법적 리스크
      - 시장 수용성 리스크
      - 경쟁 기술 대체 리스크
      
      ### 7단계: 관련성 검증 (relevance_check)
      **목적**: 수집된 데이터의 기술 분석 관련성 검증
      
      **검증 로직**:
      - 구조화된 LLM 출력 (RelevanceGrade)
      - RAG/웹/KIPRIS 데이터 품질 평가
      - 관련성에 따른 신뢰도 조정:
        - 관련성 있음: +25점 (최대 95점)
        - 관련성 부족: -15점 (최소 30점)
      
      ### 8단계: 조건부 분기 (decide_summary_type)
      **분기 조건**: 업데이트된 신뢰도 기준
      - **신뢰도 ≥ 70점**: 상세 요약 생성
      - **신뢰도 < 70점**: 기본 요약 생성
      
      ### 9-A단계: 상세 요약 생성 (generate_summary)
      **목적**: 투자자 관점의 종합 기술 분석 보고서 생성
      
      **JSON 구조화 출력**:
      ```json
      {
        "tech_summary": "기술 요약 (300-500자)",
        "strengths_and_weaknesses": "강점/약점 분석",
        "differentiation_points": "차별점 (200-400자)",
        "technical_risks": "기술 리스크 (200-400자)",
        "patents_and_papers": ["특허1", "논문1", ...]
      }


## Architecture
(그래프 이미지)

## Directory Structure
- data/                  # 스타트업 PDF 문서
- agents/                # 평가 기준별 Agent 모듈
- font/                  # 폰트 템플릿
- reports/               # 평가 결과 저장
- checkpoint/            # json 저장
- faiss_db               # faiss db 저장
- main.py                # 실행 스크립트
- README.md

## Contributors 
- 고대영 : 투자 판단 에이전트, 보고서 생성 에이전트 개발
- 김민제 : 기술 요약 에이전트 개발
- 김유진 : 경쟁사 비교 에이전트 개발
- 장주한 : 스타트업 탐색 에이전트 개발
- 조영우 : 시장성 평가 에이전트 개발
