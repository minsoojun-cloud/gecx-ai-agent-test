# Gemini Enterprise (Vertex AI Agent Builder) Cost & Optimization Guide

고객님께서 문의주신 **Vertex AI Agent Builder (이하 Gemini Enterprise)**의 과금 체계와 비용 효율성을 극대화하기 위한 최적화(Tuning) 방안을 상세히 안내해 드립니다.

---

## 1. 주요 기능별 과금 체계 상세

Vertex AI Agent Builder의 비용은 크게 **대화형 세션(Conversation)**, **검색(Search)**, **추천(Recommendation)** 등으로 나뉘며, 각 에디션 및 사용량에 따라 다르게 부과됩니다.

### 1) 대화 세션 (Conversational Agents / Vertex AI Conversation)
대화형 에이전트는 사용자와의 **채팅 세션(Session)** 또는 **사용자 질의(Query)** 단위로 과금됩니다.
*   **Vertex AI Conversation (Dialogflow CX 기반 에이전트)**:
    *   **채팅 세션당 요금**: 일반적인 텍스트 기반 대화 세션당 약 **$0.007 ~ $0.02** 수준으로 책정됩니다. (세션은 보통 첫 메시지 시작 후 30분 동안 유지되며, 세션 내 대화 횟수와 상관없이 단일 세션 요금이 적용됩니다.)
    *   **LLM 생성형 답변(Generative Playbooks/Data Stores)**을 사용할 경우, Vertex AI 플랫폼의 **LLM Token 요금(Input/Output Token 당 비용)** 및 **검색 쿼리 비용**이 추가로 합산되어 청구됩니다.
*   **관련 링크**: [Dialogflow CX / Vertex AI Conversation 상세 단가표](https://cloud.google.com/dialogflow/pricing#cx-pricing)

### 2) 상품 및 콘텐츠 추천 (Vertex AI Recommendations)
추천 기능은 API를 통해 호출된 **추천 결과 제공 횟수(1,000회당 단가)** 및 **사용자 행동 로그(User Event) 학습량**을 기반으로 과금됩니다.
*   **추천 예측 (Prediction)**:
    *   기본적으로 1,000회 예측 요청당 약 **$0.27 ~ $0.56**이 청구됩니다. (볼륨이 커질수록 계층형 할인(Tiered Pricing)이 적용됩니다.)
*   **모델 학습 및 튜닝 (Training & Tuning)**:
    *   고객의 데이터를 학습하는 노드 시간(Node Hour)당 요금이 발생합니다.
*   **관련 링크**: [Vertex AI Recommendations 상세 단가표](https://cloud.google.com/generative-ai-app-builder/pricing#vertex-ai-search-pricing)

### 3) 엔터프라이즈 검색 (Vertex AI Search)
*   **Standard Edition**: 1,000회 쿼리당 약 **$1.50 ~ $2.00**
*   **Enterprise Edition (LLM 요약 및 생성형 답변 포함)**: 1,000회 쿼리당 약 **$4.00** + LLM 토큰 비용 별도
*   **관련 링크**: [Vertex AI Search 에디션별 상세 단가표](https://cloud.google.com/generative-ai-app-builder/pricing)

---

## 2. 비용 성능(Cost Performance) 최적화 및 튜닝 포인트

종량제 과금 구조에서 성능을 유지하며 비용을 최적화할 수 있는 구체적인 가이드라인입니다.

### 1) 대화 세션(Conversation) 최적화 방안
*   **Context Caching (콘텍스트 캐싱) 도입 (★가장 효과적)**:
    *   에이전트가 긴 시스템 프롬프트, PDF 문서 세트, 혹은 대화 이력(History)을 매번 LLM에 전달하면 Input Token 비용이 기하급수적으로 증가합니다.
    *   **Vertex AI Context Caching**을 적용하면 자주 참조되는 프롬프트나 대화 맥락을 캐싱하여 **Input Token 비용을 최대 75%까지 절감**할 수 있습니다.
*   **하이브리드 라우팅 (Intent-based + Generative)**:
    *   모든 단순 질문에 LLM(Generative Playbook)을 대응시키지 않고, FAQ나 고정된 시나리오는 **Dialogflow의 Flow/Intent(룰베이스)**로 처리하도록 설계합니다. 비용이 거의 들지 않는 룰베이스 엔진을 전면에 배치하여 LLM 호출 빈도를 줄입니다.
*   **대화 이력(Session History) 요약 및 제한**:
    *   에이전트가 처리하는 슬라이딩 윈도우(최근 대화 기억 장치)의 토큰 수를 제한하거나, 일정 턴이 지나면 대화 내용을 요약(Summary)하여 입력 토큰 크기를 압축합니다.

### 2) 추천(Recommendations) 및 검색(Search) 최적화 방안
*   **User Event 필터링 및 정제**:
    *   학습에 사용되는 사용자 이벤트(클릭, 장바구니 담기, 구매 등) 중 불필요한 노이즈 데이터나 중복 세션을 전처리 단계에서 제거하여 모델 학습(Training Node Hours) 비용을 줄입니다.
*   **추천 결과 캐싱 및 배치 프로세싱**:
    *   실시간성이 크게 중요하지 않은 추천 영역의 경우, 페이지 진입 시마다 실시간 API를 호출하기보다 배치를 통해 주기적으로 추천 목록을 계산하여 캐시(Redis, Memcached 등)에 저장 후 서빙합니다.
*   **검색 쿼리 스로틀링 및 캐싱**:
    *   자동 완성(Auto-complete)이나 인기 검색어 결과 등 반복적인 검색 요청은 프론트엔드 또는 API 게이트웨이 레이어에서 캐싱 처리하여 Vertex AI Search API 호출 수 자체를 제어합니다.

### 3) 대화 로그 가공 및 평가 프로세스 최적화
대화 로그를 수집하여 분석, 가공, 품질 평가(Evaluation)할 때 발생할 수 있는 가상의 비용을 절감하는 방안입니다.
*   **샘플링 평가 기법 적용**:
    *   전체 대화 로그(100%)를 LLM을 통해 자동 평가(LLM-as-a-Judge)하는 방식은 비용이 매우 큽니다. 통계적으로 유의미한 수준(예: 전체의 5~10%)으로 로그를 **무작위 샘플링**하여 평가 프로세스를 운영합니다.
*   **경량 모델(Gemini Flash 등) 활용**:
    *   로그 분류, 데이터 마스킹(개인정보 식별), 성능 평가 등 복잡한 추론이 필요하지 않은 사후 가공 태스크에는 고비용의 Pro 모델 대신 **Gemini Flash** 모델을 적극 활용하여 처리 비용을 낮춥니다.

---

## 3. 요약 및 권장 로드맵

1.  **단기 실행 과제**: 프롬프트 크기가 큰 에이전트 시나리오에 **Context Caching** 적용 여부 검토 및 단순 응답용 **룰베이스(Intent) 처리 비중 확대**.
2.  **중기 실행 과제**: 실시간 추천 호출 영역을 식별하여 **서빙 캐시 레이어** 구축.
3.  **로그 분석 인프라 구축 시**: 자동 평가 모델을 **Gemini Flash**로 지정하고, 평가 대상 로그를 **샘플링** 처리하도록 파이프라인 설계.
