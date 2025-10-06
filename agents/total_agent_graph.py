from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import os

class GraphState(dict):
    """전체 워크플로우 상태 (공용 state)"""
    pass

def build_total_agent_graph(filename="total_agent_graph.png"):
    """전체 에이전트 워크플로우 정의 후 컴파일 & PNG 저장"""
    workflow = StateGraph(GraphState)

    # 노드 정의
    workflow.add_node("ExplorerAgent", lambda s: s)
    workflow.add_node("TechSummaryAgent", lambda s: s)
    workflow.add_node("MarketEvalAgent", lambda s: s)
    workflow.add_node("CompetitorAgent", lambda s: s)
    workflow.add_node("InvestmentAgent", lambda s: s)
    workflow.add_node("ReportAgent", lambda s: s)

    # 순차 연결
    workflow.add_edge("ExplorerAgent", "TechSummaryAgent")
    workflow.add_edge("TechSummaryAgent", "MarketEvalAgent")
    workflow.add_edge("MarketEvalAgent", "CompetitorAgent")
    workflow.add_edge("CompetitorAgent", "InvestmentAgent")
    workflow.add_edge("InvestmentAgent", "ReportAgent")
    workflow.add_edge("ReportAgent", END)

    workflow.set_entry_point("ExplorerAgent")

    # ✅ compile
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    # ✅ 저장 경로
    output_path = os.path.join("reports", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ✅ mermaid → PNG 저장
    png_bytes = app.get_graph().draw_mermaid_png()
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"✅ 에이전트 그래프가 {output_path} 로 저장되었습니다.")
    return app
