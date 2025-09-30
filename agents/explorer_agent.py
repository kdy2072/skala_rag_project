import json

class ExplorerAgent:
    def run(self, input_json: dict = None) -> dict:
        # input_json 없음 → 탐색 시작
        output = {
            "company_name": "헬스케어AI",
            "product": "AI 기반 환자 모니터링 시스템",
            "tech_raw": "딥러닝 기반 생체신호 분석"
        }
        return output

