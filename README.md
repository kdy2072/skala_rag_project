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
- Tech Summary Agent: Agentic AI 워크플로우를 활용하여 스타트업의 기술력을 종합적으로 분석하고 투자 관점에서 평가하는 지능형 에이전트
- Market Eval Agent : 스타트업 핵심기술과 기업명을 바탕으로 시장성 및 규모를 조사 하는 에이전트
- Competitor Agent : 검색 엔진 API인 Tavily를 Tool로 활용해 타겟 회사의 경쟁 회사에 대해 조사하는 에이전트
- Investment Agent : Scorecard Method을 이용하여 기준 점수에 따라 투자 or 보류 결정 에이전트
- Report Agent : 투자로 결정난 스타트업에 대하여 보고서를 작성하는 에이전트

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
---
## Contributors 
- 고대영 : 투자 판단 에이전트, 보고서 생성 에이전트 개발
- 김민제 : 기술 요약 에이전트 개발
- 김유진 : 경쟁사 비교 에이전트 개발
- 장주한 : 스타트업 탐색 에이전트 개발, FAISS기반 벡터디비 구축
- 조영우 : 시장성 평가 에이전트 개발
---
## Detail Discription
---
## 1. explorer_agent&VectorDB구축 (장주한)
### 1-1. IR PDF, 회사소개서 기반 VectorDB 파이프라인
- **초기 시도**: `sentence-transformers/sroberta-multitask` (384-dim) + 기본 텍스트 스플릿 청킹 → 실제 IR 문서의 긴 문단/표 구조에서는 성능 한계 확인  
- **개선**: `nlpai-lab/KURE-v1` (1024-dim, 한국어 특화 고차원 임베딩 모델)로 교체하여 의미 보존 성능 향상  
- **Semantic Chunking 도입**: 단순 fixed-size chunk → 문단 단위 중심(`RecursiveCharacterTextSplitter`, chunk_size=800, overlap=150)으로 변경, 문맥 손실 최소화  
- **FAISS VectorStore 구축**: 기업명 기반 메타데이터(`company`)를 모든 청크에 추가, 기업 단위 검색/분석 가능  
- **FAISS Index**: Flat Index (IndexFlatL2 기반) 사용 → 소규모 IR PDF 분석 시 효율성과 단순성 최적화  
- **확장 가능성**: 현재 Flat Index 기반이나, 대규모 데이터셋 대응을 위해 **HNSW/IVF 인덱스로 확장 가능**한 구조로 설계  
- **자동화 스크립트**: PDF → Chunk → Embedding → VectorDB 저장까지 전 과정 자동화 (`util_vectorstore.py`)

### 1-2. Explorer Agent (RAG + WebHybrid 분석)
- **RAG 기반 1차 검색**: VectorDB에서 기업별 owner / core_tech / pros / patents / investments 추출  
- **정보 부족 시 Fallback**: `Tavily` 웹 검색 연동, 자동으로 부족 데이터 보강  
- **ReAct 기반 Agent**: LangChain `create_react_agent`로 멀티툴(RAGSearch, WebSearch) 오케스트레이션  
- **JSON 스키마 강제화**: 결과를 통일된 JSON 형식으로 산출 → 투자분석 레포트 자동화  
- **산출물 예시**: `checkpoint/01_company_desc_semantic.json`에 기업별 핵심 데이터 저장  
- **기업 리스트 자동 탐색**: VectorDB 내 저장된 기업명 메타데이터 기반으로 전체 분석 실행 가능  

### 1-3. 기술 스택 및 구현 역량
- **LLM & Embedding**: OpenAI GPT-4o, HuggingFace Embeddings (`sroberta 384-dim → KURE-v1 1024-dim 개선`)  
- **RAG Infra**: LangChain, FAISS (Flat Index, HNSW 확장 가능), Semantic Chunking  
- **에이전트**: ReAct 기반 멀티툴 Agent, JSON 스키마 검증 및 자동 저장  
- **Infra/환경**: Python, dotenv, 구조화된 모듈 설계  

### 1-4. 최종구현:  
- **PDF → VectorDB 자동화 파이프라인 (임베딩 모델/청킹/Index 구조 개선 및 확장성 반영)**  
- **RAG + WebHybrid Explorer Agent (RAGsearch, WebSearch 오케스트레이션 agent, JSON 산출)**  
---
## 2번 테크서머리(김민재) 추가해야함
---
### 3. MarketEvalAgent (조영우)
### 3-1. 요약
- **구현 목적**: 기업의 핵심 기술 정보를 입력받아, Tavily 검색을 통해 **산업 동향 / 시장 규모 / 규제 환경**을 자동 수집  
- **검색 엔진 활용**: `langchain_teddynote.tools.TavilySearch`로 최근 30~60일 뉴스 검색  
- **관련성 필터링**: `GroundednessChecker`(ChatOpenAI `gpt-4o-mini` 기반)로 검색 결과 relevance 평가, 비관련 정보 제거  
- **스키마화된 출력**: `industry_trends`, `market_size`, `regulatory_barriers`, `evidence` 필드를 포함한 dict 리턴  
- **증거(evidence) 생성**: 검색 결과의 title, url, accessed_at 날짜 기반 evidence 리스트 저장  

### 3-2. 실행 파이프라인
- 입력: 기존 기업 정보 JSON (`checkpoint/01_company_desc_semantic.json`)  
- 처리: 기업별 market data 생성 후 기존 dict에 병합  
- 출력: 동일 JSON 파일을 overwrite 방식으로 업데이트 저장  
- 주요 함수 흐름: `run()` → `generate_market_data()` → `_filter_relevant()` → `save_results()`

### 3-3. 기술 스택 및 구현 요소
- **LLM**: OpenAI GPT-4o-mini (GroundednessChecker 기반)  
- **검색**: TavilySearch (뉴스, 규제 환경 크롤링)  
- **Infra**: Python, dotenv, JSON 입출력 기반 처리  
- **특징**: 단일 Agent 클래스(`MarketEvalAgent`)로 input–process–save 일괄 처리 구조  

### 3-4. 최종 구현
- **기업별 시장성 평가 모듈**: 산업 동향, 시장 규모, 규제 환경 자동 수집 및 JSON 병합  
- **검색 결과 필터링**: GPT-기반 relevance checker 적용  
- **자동 저장 로직**: 결과를 기존 checkpoint JSON에 덮어쓰기 방식으로 저장 
---
### 4. CompetitorAgent (김유진)
### 4-1. 요약
- **구현 목적**: 기업명과 핵심 기술을 입력받아, Tavily 검색과 LLM을 활용해 가장 직접적인 경쟁사 1개를 도출  
- **검색 도구**: TavilyClient (`crunchbase`, `reuters`, `bloomberg`, `techcrunch` 도메인 제한) 활용, 상위 5개 결과 및 자동 요약(answer) 수집  
- **Agent 구성**: LangChain `create_openai_functions_agent` + `ChatOpenAI (gpt-4o-mini)`  
- **출력 스키마**: 경쟁사 분석 JSON 생성 (main_competitors, competitor_profiles, market_positioning, product_comparison, unique_value_props, threat_analysis, MarketShare, reference_urls)  
- **보완 로직**: 검색 결과를 문자열에서 JSON으로 parsing, 실패 시 fallback 스키마 채워넣기   

### 4-2. 실행 파이프라인
- 입력: 기존 기업 JSON 파일 (`checkpoint/01_company_desc_semantic.json`)  
- 처리: 기업별 경쟁사 분석 실행 (`find_competitor` → JSON parsing → `update`)  
- 출력: 같은 JSON 파일에 overwrite 저장  
- 주요 함수:  
  - `search_competitor()` → Tavily 검색 및 결과 요약  
  - `find_competitor()` → LLM 프롬프트 기반 경쟁사 분석  
  - `parse_competitor_analysis()` → JSON 파싱 / fallback  
  - `analyze_multiple_companies()` → 다수 기업 순차 실행  

### 4-3. 기술 스택 및 구현 요소
- **LLM**: OpenAI GPT-4o-mini (functions agent 기반)  
- **검색**: Tavily API (고정 도메인 필터 + advanced search)  
- **에이전트**: LangChain AgentExecutor (competitor_search tool 포함)  
- **Infra**: Python, JSON 입출력, 정규식 기반 파서  

### 4-4. 최종 구현
- **기업별 경쟁사 분석 모듈**: Tavily 기반 경쟁사 후보 탐색 후 LLM으로 정리  
- **자동 JSON 스키마화**: 경쟁사 프로필, 포지셔닝, 위협 요인, 시장점유율 포함  
- **파일 입출력 루틴**: 기존 checkpoint JSON 파일에 결과 병합 저장  

---
### 5. InvestmentAgent (고대영)
---
### 6. reportagent (고대영)
---
### 7. total_agent_graph (고대영) 

---
E.D