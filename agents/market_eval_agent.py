class MarketEvalAgent:
    def run(self, company_name: str, product: str, tech_summary: str) -> dict:
        market_info = f"{company_name}의 제품 '{product}'은 원격 의료 시장에서 12% 성장 가능성이 있음"
        return {
            "market_eval": market_info,
            "tech_summary": tech_summary
        }
