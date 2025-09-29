import os

class ReportAgent:
    def run(self, company_name: str, product: str,
            tech_summary: str, market_eval: str,
            competitor_analysis: str, investment_decision: str,
            output_path="reports/output_report.md"):
        
        content = f"""# 투자 평가 보고서

## 스타트업 개요
- 이름: {company_name}
- 제품: {product}

## 기술 요약
{tech_summary}

## 시장성 평가
{market_eval}

## 경쟁사 비교
{competitor_analysis}

## 투자 판단
{investment_decision}
"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
