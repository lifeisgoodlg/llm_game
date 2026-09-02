import re
import json

from langchain_core.messages import HumanMessage, SystemMessage

def parse_json(content):
    if "```" in content:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if match:
            content = match.group(1).strip()
    content = re.sub(r'//.*?\n', '\n', content)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    content = re.sub(r',\s*([}\]])', r'\1', content)
    start = content.find('{') if '{' in content else content.find('[')
    end = content.rfind('}') if '{' in content else content.rfind(']')
    if start != -1 and end != -1:
        content = content[start:end+1]
    return json.loads(content)

class JSONInvokeError(RuntimeError):
    """재시도해도 쓸만한 JSON을 받지 못했을 때."""


def invoke_json(llm, system: str, human: str, validate=None, retries: int = 3):
    """JSON 응답을 받을 때까지 최대 retries 번 재시도한다.

    validate(data) 가 False 를 돌려주면 형식이 맞아도 실패로 본다.
    """
    last_error = None
    for _ in range(retries):
        try:
            response = llm.invoke([
                SystemMessage(content=system),
                HumanMessage(content=human),
            ])
            data = parse_json(response.content.strip())
            if validate and not validate(data):
                raise ValueError("응답 형식 검증 실패")
            return data
        except Exception as exc:
            last_error = exc
    raise JSONInvokeError(f"{retries}번 시도했지만 응답을 받지 못했습니다: {last_error}")
