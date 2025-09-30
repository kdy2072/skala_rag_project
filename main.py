from agents.explorer_agent import ExplorerAgent
from agents.tech_summary_agent import TechSummaryAgent
from agents.market_eval_agent import MarketEvalAgent
from agents.competitor_agent import CompetitorAgent
from agents.investment_agent import InvestmentAgent

def main():

    data = ExplorerAgent().run()
    data = TechSummaryAgent().run(data)
    data = MarketEvalAgent().run(data)
    data = CompetitorAgent().run(data)
    data = InvestmentAgent().run(data)

    print("최종 결과:", data)

if __name__ == "__main__":
    main()