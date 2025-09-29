from agents.explorer_agent import ExplorerAgent
from agents.tech_summary_agent import TechSummaryAgent
from agents.market_eval_agent import MarketEvalAgent
from agents.competitor_agent import CompetitorAgent
from agents.investment_agent import InvestmentAgent
from agents.report_agent import ReportAgent

def main():
    # 1. 스타트업 탐색
    startup = ExplorerAgent().run()

    # 2. 기술 요약
    startup = TechSummaryAgent().run(startup)

    # 3. 시장성 평가
    startup = MarketEvalAgent().run(startup)

    # 4. 경쟁사 비교
    startup = CompetitorAgent().run(startup)

    # 5. 투자 판단
    startup = InvestmentAgent().run(startup)

    # 6. 보고서 생성
    ReportAgent().run(startup)

if __name__ == "__main__":
    main()
