from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

REF_TOPICS = [
    "후궁 품계 제도 (답응 ~ 황귀비 / 황후), 각 품계별 권한 및 혜택과 승급 조건",
    "황제의 총애를 얻는 전략과 절대 하면 안 되는 행동",
    "궁중에서 독살 방법, 은침 검독법과 대응 수단",
    "모함과 저주의식 조작 방법, 증거 조작과 대응법",
    "황자 출산의 정치적 의미, 임신 중 위험과 보호 전략",
    "내명부의 권력 구조, 황후/황귀비/귀비/비/빈/상궁의 실질적 역할",
    "외척과 신하 포섭 방법, 군권 장악까지의 단계",
    "측천무후가 후궁에서 황제가 된 과정과 핵심 전략",
    "폐서인과 냉궁 유폐 제도와 역사적 사례",
    "폐서인 혹은 냉궁 유폐 후 복위 사례",
    "황후 폐위에 필요한 명분, 절차와 실패 사례",
    "궁중 첩보망 구축, 시비/내관 매수와 이중 첩자 활용",
    "궁중 동맹의 속성, 배신 징후 파악과 대비법",
    "황태자 책봉 경쟁, 폐위된 황태자 음모와 황자 보호 전략",
    "역모죄 성립 조건, 연좌제와 처형 방식",
    "수렴청정 제도, 실권 장악 과정과 역사적 사례",
    "궁중 예법 실수의 정치적 활용, 함정 만들기",
    "궁중 생존 전략, 굴욕을 감수해야 할 때와 반격 타이밍",
    "황후 권한의 실질적 한계, 황제 없이 황후가 무너지는 과정",
]

def generate_palace_knowledge(llm: ChatOpenAI) -> list:
    """LLM으로 궁중 지식 문서를 생성하여 Document 리스트로 반환"""
    
    docs = []

    for topic in REF_TOPICS:
        prompt = f"""
궁중 암투 드라마 스타일로 아래 주제에 대한 궁중 지식을 4~5문장으로 서술하세요.
실제 역사와 드라마 설정을 혼합해 현실감 있게 작성하세요.
문장 형태로만 출력하고 불필요한 것들은 붙이지 마세요.

주제: {topic}
"""
        content = llm.invoke(prompt).content.strip()
        docs.append(Document(
            page_content=content,
            metadata={"topic": topic}
        ))
    return docs