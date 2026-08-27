## Project Info
#### Project id: ai-commerce-search-e-osaka
#### Project number: 1047996184557
#### GECX AI Agent: https://ces.cloud.google.com/

## Run Local
```shell
python3 -m http.server 8080
```

## 테스트용 유저 쿠키 설정 (User Personalization Testing)

GECX AI Agent가 브라우저 쿠키에서 유저 이름을 읽어 맞춤 인사를 제공하도록 테스트하는 방법입니다.

### 방법 1. Chrome 콘솔(Console)에서 설정 (권장)
1. 브라우저에서 개발자 도구(`F12` 또는 `Cmd + Option + I`)를 열고 **Console** 탭으로 이동합니다.
2. 콘솔에 붙여넣기 차단 경고가 뜨는 경우, 먼저 아래 명령어를 직접 타이핑하고 Enter를 누릅니다:
   ```text
   allow pasting
   ```
3. 테스트용 유저 쿠키를 설정합니다:
   ```javascript
   // 로그인 유저 쿠키 설정 (일본어/한글 깨짐 방지 encodeURIComponent 적용)
   document.cookie = "username=" + encodeURIComponent("田中") + "; path=/";
   ```
4. 설정 확인:
   ```javascript
   document.cookie
   ```
5. 쿠키 삭제 (비회원/게스트 테스트 시):
   ```javascript
   document.cookie = "username=; Max-Age=0; path=/";
   ```

### 방법 2. Chrome DevTools [Application] 탭에서 설정 (GUI)
1. 개발자 도구 상단의 **Application** 탭으로 이동합니다.
2. 좌측 트리 메뉴: **Storage > Cookies > `http://localhost:8080`** 선택
3. 우측 쿠키 목록 테이블의 빈 행(마지막 줄)을 **더블 클릭**하여 추가:
   * **Name**: `username`
   * **Value**: `田中` (또는 원하는 이름)
   * **Path**: `/`
4. Enter를 누르면 즉시 저장됩니다.

