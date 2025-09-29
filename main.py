from agents.explorer_agent import ExplorerAgent
from agents.tech_summary_agent import TechSummaryAgent
from agents.market_eval_agent import MarketEvalAgent
from agents.competitor_agent import CompetitorAgent
from agents.investment_agent import InvestmentAgent
from agents.report_agent import ReportAgent

def main():
    # 1. 스타트업 탐색
    explorer_output = ExplorerAgent().run()

    # 2. 기술 요약
    tech_output = TechSummaryAgent().run(
        explorer_output["name"],
        explorer_output["product"],
        explorer_output["tech_raw"]
    )

    # 3. 시장성 평가
    market_output = MarketEvalAgent().run(
        tech_output["company_name"],
        tech_output["product"],
        tech_output["tech_summary"]
    )

    # 4. 경쟁사 비교
    competitor_output = CompetitorAgent().run(
        market_output["market_eval"],
        market_output["tech_summary"]
    )

    # 5. 투자 판단
    investment_output = InvestmentAgent().run(
        competitor_output["market_eval"],
        competitor_output["competitor_analysis"]
    )

    # 6. 보고서 생성
    ReportAgent().run(
        company_name=tech_output["company_name"],
        product=tech_output["product"],
        tech_summary=tech_output["tech_summary"],
        market_eval=market_output["market_eval"],
        competitor_analysis=competitor_output["competitor_analysis"],
        investment_decision=investment_output["investment_decision"]
    )

if __name__ == "__main__":
    main()
