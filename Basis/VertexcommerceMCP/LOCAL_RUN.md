# Local Run Guide (로컬 실행 가이드)

이 가이드는 로컬 환경에서 `testing.py`를 실행하여 MCP 서버 및 에이전트를 테스트하는 방법을 안내합니다.

## 1. 가상환경 생성 및 활성화

프로젝트의 의존성이 로컬 시스템에 전역으로 설치되는 것을 방지하기 위해 Python 가상환경(venv)을 사용하는 것을 권장합니다.

```bash
# 1. 가상환경 생성 (이름: .venv)
python3 -m venv .venv

# 2. 가상환경 활성화 (macOS)
source .venv/bin/activate
```

가상환경이 정상적으로 활성화되면 터미널 프롬프트 앞에 `(.venv)`가 표시됩니다.

## 2. 의존성 라이브러리 설치

가상환경이 활성화된 상태에서 `requirements.txt` 파일에 정의된 필수 패키지들을 설치합니다.

```bash
pip install -r requirements.txt
```

## 3. 테스트 스크립트 실행

의존성 설치가 완료되면 테스트용 에이전트 스크립트를 실행합니다.

```bash
python3 testing.py
```

## 4. 가상환경 종료

테스트가 끝난 후 가상환경을 비활성화하려면 아래 명령어를 입력합니다.

```bash
deactivate
```
