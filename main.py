from agents.explorer_agent import ExplorerAgent
from agents.tech_summary_agent import TechSummaryAgent
from agents.market_eval_agent import MarketEvalAgent
from agents.competitor_agent import CompetitorAgent
from agents.investment_agent import InvestmentAgent
from agents.report_agent import ReportAgent
from dotenv import load_dotenv
from agents.total_agent_graph import build_total_agent_graph
import os

load_dotenv()
FAISS_DIR = "./faiss_db/unicorns_sementic"
print("FAISS_DIR:", FAISS_DIR, os.path.exists(os.path.join(FAISS_DIR, "index.faiss")))

def main():
    explorer = ExplorerAgent(faiss_path=FAISS_DIR)

    # ✅ DB에 있는 모든 회사 → state 리스트 생성
    states = explorer.run()

    # ✅ 이후 각 state를 다른 Agent들에 넘기면서 업데이트
    updated_states = []
    for state in states:
        state = TechSummaryAgent().run(state)
        state = MarketEvalAgent().run(state)
        state = CompetitorAgent().run(state)
        state = InvestmentAgent().run(state)
        state = ReportAgent().run(state)
        updated_states.append(state)
    

    build_total_agent_graph(app=None, filename="total_agent_graph.png")
    print("✅ 전체 그래프 저장 완료: total_agent_graph.png")

if __name__ == "__main__":
    main()
