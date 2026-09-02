# 작업 규칙

## 브랜치 전략

```
main                 배포 브랜치. 직접 커밋도 push도 하지 않는다.
dev                  통합 브랜치. 작업 브랜치를 머지한 뒤 push한다.
{type}/{feature}     개인 작업 브랜치
```

**작업 브랜치는 항상 `dev`에서 딴다.** 이름은 소문자 영문으로, `feature`에는 지금 하는 작업을 짧게 적는다.

```
feat/rag-pipeline
fix/ending-rule
docs/readme
```

### 작업 흐름

```bash
git checkout dev
git pull origin dev
git checkout -b feat/rag-pipeline
# 작업 및 커밋
git push origin feat/rag-pipeline
```

머지 전에 `dev`의 변경사항을 먼저 작업 브랜치에 반영한다. 머지가 끝나면 작업 브랜치는 바로 삭제한다 — 오래 두면 충돌이 커진다.

```bash
git checkout dev && git pull origin dev
git checkout feat/rag-pipeline && git merge dev
```

## 커밋 컨벤션

```
{type}: {한글 제목}
```

| 타입 | 상황 |
|---|---|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | README, 주석 등 문서 수정 |
| `refactor` | 기능 변경 없이 코드 구조 개선 |
| `chore` | 패키지 설치, 설정 파일 수정 |
| `style` | 코드 포맷, 린트 수정 |

- 말머리(type)를 제외한 제목은 **한글**로 쓴다.
- 제목은 **50자 이내**로 간결하게.

```
feat: 조선왕조실록 RAG 파이프라인 연결
fix: 중전 강등 시 엔딩 판정 오류 수정
docs: README에 밸런스 표 추가
chore: faiss-cpu 의존성 추가
```

## 금지

```
main, dev 브랜치에 직접 커밋
force push (git push -f)
.env 커밋
API 키·비밀번호 하드코딩
100MB 이상 대용량 파일 커밋
머지 후 브랜치 방치
```

push 전에 `git status`로 `.env`가 스테이징되지 않았는지 확인한다.
`.env`에 새 키를 추가했다면 `.env.example`도 함께 갱신한다.

## 코딩 컨벤션

- 변수명·함수명은 `snake_case`, 클래스명은 `PascalCase`
- 들여쓰기는 공백 4칸
- 함수명과 파일명은 기능을 알 수 있도록 명확하게
- 불필요한 주석은 지양하고, 복잡한 로직에만 주석을 단다
- API 키·비밀번호 등 민감 정보는 코드에 쓰지 않고 `.env`로 관리한다

## 이 프로젝트에서

게임 밸런스에 영향을 주는 값(`RANK_CURVE`, `DIFFICULTY`, `THRONE_GATE`, `FOUND_GATE`,
`RELATION_RIPPLE`)을 건드렸다면 커밋 전에 시뮬레이터를 돌려 엔딩 분포를 확인한다.

```bash
python balance_sim.py
```
