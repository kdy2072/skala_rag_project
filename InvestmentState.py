from typing import Union, Dict, List
from pydantic import BaseModel

class InvestmentState(BaseModel):
    # 기본 회사 정보
    company_name: str = ""
    owner: str = ""
    core_tech: str = ""
    pros: str = ""
    patents: str = ""
    investments: Union[str, List[Dict], dict] = ""   # ✅ 리스트도 허용

    # TechSummaryAgent 결과
    tech_summary: str = ""
    strengths_and_weaknesses: str = ""
    differentiation_points: str = ""
    technical_risks: str = ""
    patents_and_papers: List[str] = []
    confidence_score: float = 0.0

    # MarketEvalAgent 결과
    industry_trends: str = ""
    market_size: str = ""
    regulatory_barriers: str = ""
    customer_segments: str = ""

    # CompetitorAgent 결과
    main_competitors: str = ""
    competitor_profiles: str = ""
    market_positioning: str = ""
    product_comparison: str = ""
    unique_value_props: str = ""
    threat_analysis: str = ""
    market_share: str = ""
    reference_urls: List[str] = []

    # InvestmentAgent 결과
    scores: Dict[str, int] = {}
    total_score: float = 0.0
    decision: str = ""

    # ReportAgent 결과
    report_path: str = ""
