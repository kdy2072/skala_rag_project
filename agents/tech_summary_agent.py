class TechSummaryAgent:
    def run(self, input_json: dict) -> dict:
        # 원래 데이터 유지하면서 새 key/value 추가
        input_json.update({
            "tech_summary": "딥러닝 기반 생체신호 분석",
            "tech_patents": ["KR-2023-00123", "US-2022-00987"],
            "tech_maturity": "TRL 6 (시제품 단계)"
        })
        return input_json