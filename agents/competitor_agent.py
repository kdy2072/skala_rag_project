class CompetitorAgent:
    def run(self, market_eval: str, tech_summary: str) -> dict:
        competitors = ["메디컬AI", "헬스케어솔루션즈"]
        return {
            "competitor_analysis": f"경쟁사: {', '.join(competitors)}",
            "market_eval": market_eval,
            "tech_summary": tech_summary
        }
