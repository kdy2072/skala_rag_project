class TechSummaryAgent:
    def run(self, name: str, product: str, tech_raw: str) -> dict:
        summary = f"{name}은 {tech_raw} 기술을 적용하여 {product}을(를) 개발 중"
        return {
            "tech_summary": summary,
            "product": product,
            "company_name": name
        }
