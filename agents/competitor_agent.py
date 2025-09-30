class CompetitorAgent:
    def run(self, input_json: dict) -> dict:
        input_json.update({
            "competitor_analysis": "경쟁사 대비 특허 3건 보유, 네트워크 강점",
            "competitors": ["메디컬AI", "헬스케어솔루션즈"],
            "competitive_advantage": "특허 기반 기술 장벽 + 병원 네트워크",
            "market_share_estimate": "경쟁사 대비 초기 시장 점유율 5% 예상"
        })
        return input_json