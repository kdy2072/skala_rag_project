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
## 2. TechSummaryAgent (김민제)

### 2-1. 요약
- **구현 목적**: IR PDF 등 내부 문서를 기반으로 분석된 초기 기업 정보 JSON을 입력받아, Agentic RAG 워크플로우를 통해 기업의 기술력을 심층 분석하고 요약 리포트를 자동 생성합니다. 이 에이전트는 정보가 불충분할 경우 스스로 판단하여 검색을 재시도하는 자가 교정(Self-Correcting) 기능이 핵심입니다.
- **분석 항목**:
  - 기술 요약 (`tech_summary`)
  - 강점과 약점 (`strengths_and_weaknesses`)
  - 차별화 요소 (`differentiation_points`)
  - 기술적 리스크 (`technical_risks`)
  - 특허 및 논문 관련 정보 (`patents_and_papers`)
- **산출물**: 분석이 완료된 후, 기존 입력 JSON 파일(`01_company_desc_semantic.json`)에 상기 분석 항목들을 추가하여 덮어쓰기 방식으로 저장합니다.

---
### 2-2. 실행 파이프라인
- **입력**: 분석할 기업의 기본 정보가 담긴 JSON 파일
- **처리 흐름** (LangGraph `StateGraph` 기반, 동적/조건부 실행):
  1. **Agent (에이전트 노드)**: 초기 질문을 바탕으로 RAG, 웹 검색, 특허 검색 중 가장 적합한 도구를 동적으로 선택하고 호출합니다.
  2. **Tools (도구 실행 노드)**: 선택된 도구를 실행하여 정보를 수집합니다.
  3. **Grade Documents (정보 충분성 평가 노드)**: 수집된 정보가 분석에 충분한지 LLM이 평가합니다.
  4. **Conditional Routing (조건부 분기)**:
      - **정보 충분 시**: 최종 요약 생성 노드로 이동합니다.
      - **정보 부족 시**: **Rewrite Query (쿼리 재작성 노드)**로 이동하여 검색어를 개선한 후, 다시 Agent 노드로 돌아가 정보 수집을 재시도하는 **루프(Loop)**를 형성합니다.
  5. **Generate Summary (최종 요약 생성 노드)**: 루프를 통해 충분히 수집된 정보를 바탕으로 5가지 분석 항목에 대한 최종 보고서를 생성합니다.
  6. **JSON 저장**: 최종 결과를 입력 파일에 덮어쓰기하여 저장합니다.

---
### 2-3. 클래스 및 구성 요소
- **`TechAnalysisState` (BaseModel)**
  - LangGraph 파이프라인의 전체 상태(State)를 저장하는 데이터 구조입니다. 기업명, 핵심 기술, 누적된 메시지(검색 결과), 최종 출력 항목들을 관리합니다.
- **`TechSummaryAgentV3` (메인 클래스)**
  - LangGraph 그래프를 정의, 초기화하고 실행을 관리하는 핵심 클래스입니다. 에이전트, 정보 평가, 쿼리 재작성 등 각 단계에 해당하는 노드 함수들을 포함합니다.
- **`KIPRISPatentTool`**
  - 기업명/기술 키워드를 기반으로 KIPRIS에서 특허 데이터를 수집하는 클래스입니다. `@tool` 데코레이터가 붙은 `kipris_search_tool` 함수를 통해 에이전트가 활용합니다.
- **`RelevanceGrade` (BaseModel)**
  - `_grade_documents` 노드에서 LLM이 정보의 충분성을 평가한 후, 그 결과를 'yes' 또는 'no' 형태의 구조화된 데이터로 출력하기 위한 Pydantic 모델입니다.
- **LangGraph `StateGraph`**
  - 위 컴포넌트들을 **조건부 엣지(Conditional Edge)**로 연결하여, 단순 순차 실행이 아닌 동적이고 지능적인 에이전트 워크플로우를 구성합니다.

---
### 2-4. RAG 사용 맥락
- **FAISS VectorDB 활용**: `nlpai-lab/KURE-v1` 임베딩 모델 기반으로 구축된 FAISS VectorDB에서 기업 관련 내부 문서 청크를 검색합니다.
- **RAG 구조**: `rag_search_tool`은 에이전트가 사용할 수 있는 여러 도구 중 하나로 정의됩니다. 에이전트가 내부 문서 검색이 필요하다고 판단할 때 이 도구를 호출하며, 검색 결과는 LLM 프롬프트에 컨텍스트로 포함되어 답변 생성을 강화합니다.
- **웹/특허 데이터와 혼합**: 에이전트는 RAG 검색 결과뿐만 아니라, Tavily 웹 검색 결과와 KIPRIS 특허 API 데이터를 종합적으로 수집합니다. 최종 요약 단계에서는 이 모든 출처의 정보를 결합하여 다층적인 근거를 확보합니다.

---
### 2-5. 기술 스택 및 구현 요소
- **LLM**: OpenAI GPT-4o-mini (분석, 요약, 동적 도구 선택)
- **VectorDB**: FAISS + HuggingFace `nlpai-lab/KURE-v1` 임베딩
- **검색/특허 API**: Tavily Web Search, KIPRIS 특허 검색
- **워크플로우 엔진**: LangGraph `StateGraph` (조건부 분기 및 루프 포함)
- **Infra**: Python, dotenv, JSON 입출력

---
### 2-6. 최종 구현
- **LangGraph 기반 동적 실행 파이프라인**: 정해진 순서가 아닌, 에이전트의 판단에 따라 도구를 선택하고 정보의 질을 평가하며, 필요 시 쿼리를 수정해 재탐색하는 지능형 워크플로우를 구현했습니다.
- **실제 기능**: 입력된 JSON의 기업 정보를 바탕으로 5개의 심층 분석 항목을 생성하고, 그 결과를 원본 JSON 파일에 업데이트하여 저장합니다.
- **특징**: Agent라는 이름에 걸맞게 LLM이 직접 다음 행동(Tool Call)을 결정하는 동적 툴 선택 기능을 `bind_tools`와 `tools_condition`을 통해 구현했습니다. 이는 정해진 순서대로 함수를 실행하는 구조가 아닙니다.
- **RAG 통합**: RAG는 파이프라인의 고정된 단계가 아니라, 에이전트가 필요에 따라 호출하는 하나의 핵심 도구로서 시스템의 분석 능력을 강화하는 역할을 수행합니다.

---
### 3. MarketEvalAgent (조영우)
### 3-1. 요약
- **구현 목적**: 기업의 핵심 기술 정보를 입력받아 Tavily 검색 + LLM 기반으로 **산업 동향 / 시장 규모 / 규제 환경 / 고객 세그먼트**를 자동 수집 및 요약  
- **검색 도구**: TavilySearch (최대 5건, advanced 모드) 활용  
- **연관성 검증**: GroundednessChecker(LLM 기반 relevance 평가)와 중복 제거(set) 적용  
- **증강 검색(RAG)**: 초기 검색 결과에서 키워드 추출 → 추가 검색으로 보강  
- **출력 구조**: 각 카테고리별 200자 이내 요약(summary) + evidence(제목, URL, 날짜) 포함  


### 3-2. 실행 파이프라인
1. **입력**: 기존 기업 정보 JSON (`checkpoint/01_company_desc_semantic.json`)  
2. **처리 흐름**:
   - Tavily로 카테고리별 검색 실행
   - `_filter_relevant` → LLM으로 연관성 검증 및 중복 제거, 최대 2개만 채택
   - `_rag_search` → 초기 검색에서 키워드 추출 후 재검색, 결과 보강
   - `_validate_and_format` → 결과 요약(200자 이내) 및 evidence 생성
3. **출력**: 기업 dict에 시장성 정보 병합 후 동일 JSON 파일로 overwrite 저장  
4. **주요 함수**:
   - `_filter_relevant()` → 연관성 검증 + 중복 제거
   - `_rag_search()` → 초기 검색 → 키워드 추출 → 재검색
   - `_validate_and_format()` → 요약 생성 + evidence 2개 포함
   - `generate_market_data()` → 4개 카테고리(산업·시장·규제·고객) 순차 실행
   - `run()` / `save_results()` → 전체 실행 및 JSON 저장  

---

### 3-3. 기술 스택 및 구현 요소
- **LLM**: OpenAI GPT-4o-mini (GroundednessChecker, 요약 체인)  
- **검색**: TavilySearch (advanced 모드, 다중 카테고리)  
- **RAG Flow**: 초기 Tavily 검색 → 키워드 추출 → 재검색 → 결과 요약  
- **특징**: **증강 검색 + 파이프라인** 구현  

### 3-4. 최종 구현
- **시장성 평가 모듈**: 산업 동향, 시장 규모, 규제 환경, 고객 세그먼트 자동 분석  
- **증거 수집(Evidence)**: URL·제목·날짜 기반으로 최대 3개 근거 저장  
- **자동 저장 로직**: 결과를 기존 checkpoint JSON에 덮어쓰기 방식으로 업데이트  
- **차별점**: 초기 버전 대비 → RAG 기반 증강 검색, 고객 세그먼트 분석, 요약 생성 등 기능 확장  

---
### 4. CompetitorAgent (김유진)

#### 4-1. 요약
- **구현 목적**: 기업명과 핵심 기술을 state로 전달받아, Tavily 검색과 LLM을 활용해 가장 직접적인 경쟁사 1개를 도출  
- **검색 도구**: TavilyClient (`crunchbase`, `reuters`, `bloomberg`, `techcrunch` 도메인 제한) 활용, 상위 5개 결과 및 자동 요약(answer) 수집  
- **Agent 구성**: LangChain `create_openai_functions_agent` + `ChatOpenAI (gpt-4o-mini)`  
- **출력 스키마**: 경쟁사 분석 결과를 state에 저장 (main_competitors, competitor_profiles, market_positioning, product_comparison, unique_value_props, threat_analysis, market_share, reference_urls)  
- **보완 로직**: LLM 응답 문자열을 JSON 객체로 파싱하여 state에 저장, 실패 시 fallback 스키마 적용  

#### 4-2. 실행 파이프라인
- **입력**: 이전 에이전트로부터 state 전달 (company_name, core_tech)  
- **처리**: state 기반 경쟁사 분석 실행 (`find_competitor` → JSON parsing → state 업데이트)  
- **출력**: 분석 결과를 state에 저장하여 다음 에이전트로 전달  
- 주요 함수:  
  - `search_competitor()` → Tavily 검색 및 결과 요약  
  - `find_competitor()` → Agent 기반 경쟁사 분석  
  - `parse_competitor_analysis()` → JSON 파싱 / fallback  
  - `run()` → state 입력 및 업데이트 처리  

#### 4-3. 기술 스택 및 구현 요소
- **LLM**: OpenAI GPT-4o-mini (functions agent 기반)  
- **검색**: Tavily API (고정 도메인 필터 + advanced search)  
- **에이전트**: LangChain AgentExecutor (competitor_search tool 포함)  
- **Pipeline**: State 기반 RAG Pipeline, 에이전트 간 state 전달  
- **Infra**: Python, InvestmentState 클래스, 정규식 기반 파서  

#### 4-4. 최종 구현
- **State 기반 경쟁사 분석 모듈**: Tavily 기반 경쟁사 후보 탐색 후 Agent를 통한 심층 분석  
- **자동 JSON 스키마화**: 경쟁사 프로필, 포지셔닝, 위협 요인, 시장점유율 포함  
- **에이전트 연결**: 이전 에이전트에서 state를 받아 분석 후 다음 에이전트로 전달

---

### 5. InvestmentAgent (고대영)

#### 5-1. 요약
- **목적**: Explorer → TechSummary → MarketEval → Competitor 단계에서 채워진 InvestmentState를 종합해 투자 적합성 점수와 최종 의사결정을 산출  
- **방식**: Scorecard Method. 창업자, 시장성, 제품/기술력, 경쟁력, 실적, 딜 조건을 정량화해 가중 합산  
- **출력**: 항목별 점수, 가중치 총점, 최종 판단(“투자 추천”/“보류”). “투자 추천”인 경우 자동으로 ReportAgent 호출  

#### 5-2. 실행 파이프라인
1. 입력: 이전 단계 에이전트들이 채운 InvestmentState  
2. LLM 평가: 상태에 담긴 회사 정보를 프롬프트로 보내 각 항목 점수를 정수(0–100)로 산출  
3. 가중치 합산  
   - Owner 30%  
   - Market 25%  
   - Product 15%  
   - Competitor 10%  
   - Performance 10%  
   - Deal 10%  
4. 최종 판정: 총점 80점 이상이면 “투자 추천”, 아니면 “보류”  
5. 자동 보고서 트리거: “투자 추천”이면 ReportAgent.run(state) 호출 → PDF 생성  

#### 5-3. 기술 스택 및 구현 요소
- **LLM**: OpenAI GPT-4o-mini (정량 점수 산출)  
- **평가 방식**: Scorecard Method (가중치 기반 합산)  
- **구현 요소**:  
  - `score_company()` : LLM 프롬프트 기반 점수 산출  
  - `calculate_weighted_score()` : 가중치 총점 계산  
  - `run(state: InvestmentState)` : 점수 계산 → 최종 판단 → ReportAgent 연동  

#### 5-4. 최종 구현
- **LLM 기반 정량 점수화**: 기업 정보를 입력받아 0~100 점수 산출  
- **가중치 총점 계산**: Scorecard Method 적용  
- **자동 투자 판단**: 80점 이상이면 "투자 추천", 아니면 "보류"  
- **보고서 생성 자동화**: 투자 추천일 경우 ReportAgent 호출 → PDF 보고서 생성  

---

### 6. ReportAgent (고대영)

#### 6-1. 요약
- **목적**: InvestmentAgent가 “투자 추천”으로 판정한 기업에 대해 투자 평가 보고서 PDF를 자동 생성  
- **폰트 처리**: 프로젝트 `font/` 폴더의 한글 폰트(Malgun, HYSMyeongJo 등)를 등록해 깨짐 방지  
- **출력 결과**: PDF는 `reports/{회사명}_llm_report.pdf`로 저장, 경로는 `state.report_path`에 기록  

#### 6-2. 실행 파이프라인
1. 입력: InvestmentState (회사명, 기술 요약, 시장성, 경쟁사 비교, 점수 및 최종 판단 등)  
2. LLM 프롬프트: 투자 보고서 양식(표지/목차/본문/결론)에 맞춘 한국어 문단 생성  
3. PDF 생성: ReportLab로 문단 단위 출력, 한글 폰트 적용  
4. 출력: 생성된 PDF 경로를 `state.report_path`에 저장하고 반환  

#### 6-3. 기술 스택 및 구현 요소
- **LLM**: OpenAI GPT-4o-mini (투자 보고서 텍스트 생성)  
- **PDF 생성**: ReportLab (Paragraph, Spacer 활용)  
- **폰트 처리**: Malgun / HYSMyeongJo / HYGothic 폰트 지원  
- **구현 요소**:  
  - `run(state: InvestmentState, output_path=None)` : 보고서 생성 함수  
  - LLM 프롬프트 기반 텍스트 생성  
  - ReportLab 기반 PDF 저장  
  - 경로를 `state.report_path`에 기록  

#### 6-4. 최종 구현
- **투자 추천 기업 전용 보고서 생성**  
- **구조화된 출력**: 표지, 목차, 본문(개요/기술/시장성/경쟁사/투자판단), 결론  
- **산출물 자동 저장**: `reports/{회사명}_llm_report.pdf`  
- **한글 폰트 안정화**: ReportLab + 폰트 등록으로 깨짐 없는 PDF 출력  

---

### 7. TotalAgentGraph ()

#### 7-1. 요약
- **목적**: 전체 에이전트 파이프라인(Explorer → TechSummary → MarketEval → Competitor → Investment → Report)을 시각화  
- **방식**: LangGraph `StateGraph` 정의 후 Mermaid 다이어그램으로 변환 및 PNG 저장  

#### 7-2. 실행 파이프라인
1. StateGraph(GraphState) 정의  
2. 각 에이전트 노드를 순차적으로 연결: Explorer → TechSummary → MarketEval → Competitor → Investment → Report → END  
3. `app.get_graph().draw_mermaid_png("reports/total_agent_graph.png")` 으로 다이어그램 저장  

#### 7-3. 최종 구현
- **전체 워크플로우 시각화**: 실제 실행 흐름과 동일하게 반영  
- **결과 산출물**: `reports/total_agent_graph.png`  
- **활용성**: README, 보고서, 프레젠테이션에 포함 가능 

실제 실행 흐름과 동일하게 반영된 다이어그램.
---
E.D
