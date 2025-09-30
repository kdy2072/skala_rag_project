class MarketEvalAgent:
    def run(self, input_json: dict) -> dict:
        input_json.update({
            "market_eval": "원격 의료 시장에서 연평균 12% 성장",
            "market_size": "2025년까지 10조원 규모 예상",
            "market_trend": "비대면 진료 수요 증가, 고령화에 따른 헬스케어 수요 확대",
            "regulation_risk": "원격의료 관련 법안 개정 지연 가능성"
        })
        return input_json