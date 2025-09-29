class InvestmentAgent:
    def run(self, market_eval: str, competitor_analysis: str) -> dict:
        decision = "투자 추천" if "성장" in market_eval else "투자 보류"
        return {
            "investment_decision": decision,
            "competitor_analysis": competitor_analysis,
            "market_eval": market_eval
        }
