# from agents.explorer_agent import ExplorerAgent
# from agents.tech_summary_agent import TechSummaryAgent
# from agents.market_eval_agent import MarketEvalAgent
# from agents.competitor_agent import CompetitorAgent
# from agents.investment_agent import InvestmentAgent

# def main():

#     data = ExplorerAgent().run()
#     data = TechSummaryAgent().run(data)
#     data = MarketEvalAgent().run(data)
#     data = CompetitorAgent().run(data)
#     data = InvestmentAgent().run(data)

#     print("최종 결과:", data)

# if __name__ == "__main__":
#     main()


import json
import os
from agents.tech_summary_agent import TechSummaryAgent
from pprint import pprint
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    # 체크포인트 파일 경로
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    checkpoint_path = os.path.join(BASE_DIR, "checkpoint", "01_company_desc_semantic.json")
    
    # 체크포인트 파일에서 데이터 로드
    if not os.path.exists(checkpoint_path):
        print(f"❌ 체크포인트 파일이 존재하지 않습니다: {checkpoint_path}")
        return
    
    try:
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            companies_data = json.load(f)
        
        print(f"📋 총 {len(companies_data)}개 기업 데이터 로드 완료")
        
        # TechSummaryAgent 초기화
        agent = TechSummaryAgent()
        
        # 각 기업별로 분석 실행
        for i, company_data in enumerate(companies_data, 1):
            company_name = company_data.get('company_name', f'Company_{i}')
            
            print(f"\n🚀 [{i}/{len(companies_data)}] {company_name} 분석 시작")
            print("="*60)
            
            # 필요한 필드만 추출하여 입력 데이터 구성
            input_data = {
                "company_name": company_data.get("company_name", ""),
                "core_tech": company_data.get("core_tech", ""),
                "owner": company_data.get("owner", ""),
                "pros": company_data.get("pros", ""),
                "patents": company_data.get("patents", ""),
                "investments": company_data.get("investments", "")
            }
            
            # 기술 분석 실행
            try:
                result = agent.run(input_data)
                
                print(f"✅ {company_name} 분석 완료")
                print(f"📝 기술 요약: {result.get('tech_summary', 'N/A')[:100]}...")
                print(f"🏆 차별점: {result.get('differentiation_points', 'N/A')[:100]}...")
                
            except Exception as e:
                print(f"❌ {company_name} 분석 실패: {e}")
                continue
        
        print(f"\n🎉 전체 {len(companies_data)}개 기업 분석 완료!")
        print(f"📄 결과는 {checkpoint_path}에 자동 저장되었습니다.")
        
    except Exception as e:
        print(f"❌ 파일 처리 오류: {e}")


if __name__ == "__main__":
    main()