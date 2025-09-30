import os
from glob import glob
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

class VectorDBBuilder:
    def __init__(self, model_name: str = "nlpai-lab/KURE-v1"):
        """
        :param model_name: HuggingFace 임베딩 모델명
        """
        self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)

    def build_from_pdfs(self, pdf_files: List[str], save_path: str = None) -> FAISS:
        """
        PDF 파일들로부터 메타데이터를 포함한 FAISS 벡터DB를 생성
        :param pdf_files: PDF 파일 경로 리스트
        :param save_path: 저장할 경로 (예: 'faiss_db/unicorns')
        :return: FAISS 객체
        """
        docs = []
        total_pages = 0
        total_chunks = 0

        # ✨ Semantic Chunking 적용
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            separators=["\n\n", "\n", " ", ""],  # 문단/문장 단위 보존
            length_function=len,
            is_separator_regex=False
        )

        for pdf in pdf_files:
            company_name = os.path.basename(pdf).split('.')[0]  # 파일명 기반 회사명 추출
            loader = PyPDFLoader(pdf)
            pages = loader.load()
            total_pages += len(pages)

            # Semantic Chunking 실행
            splits = splitter.split_documents(pages)
            total_chunks += len(splits)

            # 메타데이터 추가
            for split in splits:
                split.metadata["company"] = company_name

            print(f"📄 {os.path.basename(pdf)} ({company_name}) → {len(pages)} pages → {len(splits)} chunks")

            docs.extend(splits)

        # ✨ Flat Index (FAISS 기본: IndexFlatL2 / IP)
        vectordb = FAISS.from_documents(docs, self.embedding_model)

        if save_path:
            os.makedirs(save_path, exist_ok=True)
            vectordb.save_local(save_path)

        print("=====================================")
        print(f"✅ 총 PDF 개수: {len(pdf_files)}")
        print(f"✅ 총 페이지 수: {total_pages}")
        print(f"✅ 총 청크 수: {total_chunks}")
        print(f"✅ 메타데이터 추가 완료: 'company'")
        print(f"✅ 벡터DB 저장 경로: {save_path}")
        print("=====================================")

        return vectordb

    def load_vectorstore(self, save_path: str) -> FAISS:
        """
        저장된 FAISS 벡터DB 로드
        """
        return FAISS.load_local(
            save_path,
            self.embedding_model,
            allow_dangerous_deserialization=True
        )


if __name__ == "__main__":
    # 📂 data 폴더 밑 모든 PDF 자동 탐지
    data_dir = "data"
    pdf_files = glob(os.path.join(data_dir, "*.pdf"))

    if not pdf_files:
        print("⚠️ data 폴더에 PDF 파일이 없습니다.")
        exit()

    # 📂 저장 경로
    save_path = "faiss_db/unicorns_sementic"

    # 🚀 VectorDB 생성
    builder = VectorDBBuilder(model_name="nlpai-lab/KURE-v1")
    vectordb = builder.build_from_pdfs(pdf_files, save_path)
