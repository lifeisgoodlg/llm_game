import os
from langchain_community.vectorstores import FAISS
from palace_knowledge import generate_palace_knowledge

INDEX_PATH = "faiss_index"

def build_retriever(embeddings, llm):
    """FAISS 인덱스가 이미 존재하면 로드, 없으면 LLM으로 문서 생성 후 저장"""
    if os.path.exists(INDEX_PATH):
        vectorstore = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        docs = generate_palace_knowledge(llm)
        vectorstore = FAISS.from_documents(docs, embeddings)
        vectorstore.save_local(INDEX_PATH)

    return vectorstore.as_retriever(search_kwargs={"k": 3})

def retrieve_context(query: str, retriever) -> str:
    """쿼리와 관련된 궁중 지식 문서를 검색해 문자열로 반환"""
    docs = retriever.invoke(query)
    return "\n".join([d.page_content for d in docs])