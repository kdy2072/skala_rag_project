import os

class ReportAgent:
    def run(self, input_json: dict, output_path="reports/output_report.md") -> dict:
        content = f"""# 투자 평가 보고서

## 스타트업 개요
- 이름: {input_json["company_name"]}
- 제품: {input_json["product"]}

## 기술 요약
{input_json["tech_summary"]}

## 시장성 평가
{input_json["market_eval"]}

## 경쟁사 비교
{input_json["competitor_analysis"]}

## 투자 판단
{input_json["investment_decision"]}
"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {"status": "success", "report_path": output_path}
