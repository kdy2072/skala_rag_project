# AI Startup Investment Evaluation Agent
본 프로젝트는 헬스케어 스타트업에 대한 투자 가능성을 자동으로 평가하는 에이전트를 설계하고 구현한 실습 프로젝트입니다.

## Overview

- Objective : 헬스케어 스타트업의 핵심 기술력, 시장성, 경쟁사 비교 등을 기준으로 투자 적합성 분석
- Method : AI Agent ReAct + Agentic RAG + Agentic Tool Calling
- Tools : tavily, Custom Tool : Rag Research, TechExistenceValidatorTool, CoreTechAnalyzerTool, IP_ResearchValidatorTool

## Features

- PDF 자료 기반 정보 추출
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
├── data/                  # 스타트업 PDF 문서
├── agents/                # 평가 기준별 Agent 모듈
├── font/                  # 폰트 템플릿
├── reports/               # 평가 결과 저장
├── checkpoint/            # json 저장
├── faiss_db               # faiss db 저장
├── main.py                # 실행 스크립트
└── README.md

## Contributors 
- 고대영 : 투자 판단 에이전트, 보고서 생성 에이전트 개발
- 김민제 : 기술 요약 에이전트 개발
- 김유진 : 경쟁사 비교 에이전트 개발
- 장주한 : 스타트업 탐색 에이전트 개발
- 조영우 : 시장성 평가 에이전트 개발
