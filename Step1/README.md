# GECX Agent Data Mapping Guide

이 저장소는 GECX 상품 검색 에이전트(Search Agent)의 데이터 매핑 및 위젯 렌더링 정확성을 개선하기 위한 프로젝트입니다. 에이전트가 API 응답 결과를 프론트엔드 위젯 스키마로 올바르게 변환하도록 보장하는 규칙과 지침을 정리합니다.

---

## 1. 데이터 매핑 이슈 및 해결 팁 (Troubleshooting)

### 이슈 현상
- 상품 검색 결과 위젯(`product_list`) 렌더링 시, 상품 이미지(`imageUris`)가 빈 배열(`[]`)로 출력되거나 상세 페이지 링크(`uri`)에 가짜 도메인(예: `https://example.com/products/...`)이 주입되는 현상 발생.

### 원인
1. **데이터 계층 불일치**: API가 반환하는 이미지 데이터는 `results[].product.images` 경로에 있으나, 에이전트가 이를 단순 `results[].images`로 찾아 매핑 실패.
2. **타입 스키마 불일치**: API는 이미지 정보를 객체 배열(`[{"uri": "..."}]`)로 반환하는 반면, 위젯 스키마는 평탄한 문자열 배열(`["url1"]`)을 요구함.
3. **환각(Hallucination)**: 데이터 추출에 실패할 경우 에이전트가 임의의 플레이스홀더 URL을 생성하여 채워 넣음.

### 해결 가이드 (Best Practices)
- **명시적 경로 지정**: Instruction 내에 `results[].product.images`와 같이 정확한 JSON 데이터 접근 경로를 정의합니다.
- **데이터 변환 규칙 정의**: 객체 배열을 문자열 배열로 변환하는 과정을 구체적인 예시와 함께 지시합니다.
- **강력한 도메인 제약 조건**: 임의의 도메인(예: `example.com`) 생성을 금지하고, API가 반환한 도메인(`shiseido.co.jp`)을 그대로 유지하도록 강제합니다.
- **Few-Shot 예시 활용**: Instruction 최하단의 `<examples>` 태그에 실제 API Response 입력값과 변환된 Widget Output JSON 페이로드를 제공하여 학습시킵니다.

---

## 2. 핵심 수정 파일 안내

* [search_instraction.xml](file:///Users/minsoojun/work/GECX/Test/search_instraction.xml): 상품 검색 에이전트(Search Agent)의 태스크 흐름 및 데이터 변환 규칙을 정의합니다.
* [root_agent_instraction.xml](file:///Users/minsoojun/work/GECX/Test/root_agent_instraction.xml): 최상위 에이전트(Root Agent)에서 하위 에이전트로 데이터를 전달할 때 데이터 유실이 없도록 매핑 제약 조건을 공유합니다.
