# AI Startup Investment Evaluation Agent
본 프로젝트는 헬스케어 스타트업에 대한 투자 가능성을 자동으로 평가하는 에이전트를 설계하고 구현한 실습 프로젝트입니다.

## Overview

- Objective : AI 스타트업의 기술력, 시장성, 리스크 등을 기준으로 투자 적합성 분석
- Method : AI Agent + Agentic RAG 
- Tools : 도구A, 도구B, 도구C

## Features

- PDF 자료 기반 정보 추출 (예: IR 자료, 기사 등)
- 투자 기준별 판단 분류 (시장성, 팀, 기술력 등)
- 종합 투자 요약 출력 (예: 투자 유망 / 보류 / 회피)

## Tech Stack 

| Category   | Details                      |
|------------|------------------------------|
| Framework  | LangGraph, LangChain, Python |
| LLM        | GPT-4o-mini via OpenAI API   |
| Retrieval  | FAISS, Chroma                |

## Agents
 
- Agent A: Assesses technical competitiveness
- Agent B: Evaluates market opportunity and team capability
- Investment Agent : Scorecard Method을 이용하여 기준 점수에 따라 투자 or 보류 결정 에이전트
- Report Agent : 투자로 결정난 스타트업에 대하여 보고서를 작성하는 에이전트

## Architecture
(그래프 이미지)

## Directory Structure
├── data/                  # 스타트업 PDF 문서
├── agents/                # 평가 기준별 Agent 모듈
├── font/                  # 폰트 템플릿
├── reports/               # 평가 결과 저장
├── main.py                # 실행 스크립트
└── README.md

## Contributors 
- 고대영 : 투자 판단 에이전트, 보고서 생성 에이전트 개발
- 김민제 : 기술 요약 에이전트 개발
- 김유진 : 경쟁사 비교 에이전트 개발
- 장주한 : 스타트업 탐색 에이전트 개발
- 조영우 : 시장성 평가 에이전트 개발