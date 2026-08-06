# GECX Chat Messenger 'Add to cart' 버튼 제거 가이드 / GECX Chat Messenger 'Add to cart' ボタン削除ガイド

이 문서에서는 상품검색, 상품상세, 상품비교 화면에 기본적으로 노출되는 "Add to cart" 버튼을 숨김 처리한 방법과 그 구현 내용을 설명합니다.
このドキュメントでは、商品検索、商品詳細、商品比較画面にデフォルトで表示される「Add to cart」ボタンを非表示にする方法とその実装内容について説明します。

---

## 🇰🇷 한국어 설명

### 1. 배경 및 문제점
GECX Chat Messenger SDK (`chat-messenger.js`)에서 제공하는 기본 위젯(`product_list`, `product-detail`, `compare_products`)은 웹 컴포넌트의 **Shadow DOM** 내부에 렌더링됩니다. 이로 인해 메인 페이지의 글로벌 스타일시트(CSS)가 캡슐화 장벽을 뚫지 못해, 단순 CSS 규칙만으로는 "Add to cart" 버튼을 제어할 수 없었습니다.

### 2. 해결 방법
메인 웹 페이지의 JavaScript에 **Shadow DOM 탐색 로직**을 탑재하여 주기적으로 메신저의 DOM을 스캔하도록 구현했습니다. 격리된 Shadow DOM을 재귀적으로 파고들어가 매칭되는 버튼 컴포넌트(`df-cart-button` 및 `md-filled-button`)를 찾아 `display: none !important` 속성을 부여해 숨김 처리합니다.

### 3. 적용 코드 ([index.html](file:///Users/minsoojun/work/GECX/index.html))
`window.addEventListener("chat-messenger-loaded", ...)` 콜백 이벤트 안에 아래 로직이 삽입되었습니다.

```javascript
// GECX 메신저가 로드 완료된 후 실행
window.addEventListener("chat-messenger-loaded", () => {
  chatSdk.registerContext(
    chatSdk.prebuilts.ces.createContext({ ... })
  );

  // Shadow DOM 내부까지 재귀적으로 엘리먼트를 검색하는 함수
  function querySelectorAllShadow(selector, root = document) {
    const results = [];
    function traverse(node) {
      if (!node) return;
      if (node.nodeType === Node.ELEMENT_NODE) {
        if (node.matches(selector)) {
          results.push(node);
        }
        if (node.shadowRoot) {
          traverse(node.shadowRoot); // Shadow Root 내부 탐색
        }
      }
      let child = node.firstChild;
      while (child) {
        traverse(child);
        child = child.nextSibling;
      }
    }
    traverse(root);
    return results;
  }

  // 300ms 주기로 버튼을 감지하여 숨김 처리
  setInterval(() => {
    // 1. df-cart-button 컴포넌트 감추기
    querySelectorAllShadow('df-cart-button').forEach(el => {
      el.style.setProperty('display', 'none', 'important');
    });

    // 2. 'Add to cart' 텍스트나 장바구니 아이콘을 포함하는 md-filled-button 감추기
    querySelectorAllShadow('md-filled-button').forEach(el => {
      const icon = el.querySelector('md-icon');
      const hasCartIcon = icon && icon.textContent.trim() === 'shopping_cart';
      const hasCartText = el.textContent.toLowerCase().includes('add to cart');
      if (hasCartIcon || hasCartText) {
        el.style.setProperty('display', 'none', 'important');
      }
    });
  }, 300);
});
```

### 4. 영향 범위
* **상품검색**: 상품 검색 결과 캐러셀 카드의 하단 장바구니 아이콘 및 버튼이 숨겨집니다.
* **상품상세**: 상품 상세 정보 카드 하단에 노출되는 구매 유도 버튼이 숨겨집니다.
* **상품비교**: 비교 테이블 하단에 렌더링되는 장바구니 추가용 원형 버튼이 숨겨집니다.

---

## 🇯🇵 日本語の説明

### 1. 背景と課題
GECX Chat Messenger SDK (`chat-messenger.js`) が提供する標準ウィジェット (`product_list`, `product-detail`, `compare_products`) は、Webコンポーネントの **Shadow DOM** 内にレンダリングされます。そのため、メインページのグローバルCSSスタイルがカプセル化の障壁によって適用されず、単純なCSSの記述のみでは「Add to cart」ボタンを非表示にすることができませんでした。

### 2. 解決策
メインWebページのJavaScriptに **Shadow DOM探索ロジック** を組み込み、チャットメッセンジャーのDOMを定期的にスキャンするように実装しました。カプセル化されたShadow DOMを再帰的に巡回し、該当するボタンコンポーネント (`df-cart-button` および `md-filled-button`) を見つけ出して `display: none !important` 属性を適用し、非表示にします。

### 3. 適用コード ([index.html](file:///Users/minsoojun/work/GECX/index.html))
`window.addEventListener("chat-messenger-loaded", ...)` のコールバックイベント内に以下のロジックを挿入しました。

```javascript
// GECX メッセンジャーのロード完了時に実行
window.addEventListener("chat-messenger-loaded", () => {
  chatSdk.registerContext(
    chatSdk.prebuilts.ces.createContext({ ... })
  );

  // Shadow DOM の内部まで再帰的に要素を検索する関数
  function querySelectorAllShadow(selector, root = document) {
    const results = [];
    function traverse(node) {
      if (!node) return;
      if (node.nodeType === Node.ELEMENT_NODE) {
        if (node.matches(selector)) {
          results.push(node);
        }
        if (node.shadowRoot) {
          traverse(node.shadowRoot); // Shadow Root 内部を探索
        }
      }
      let child = node.firstChild;
      while (child) {
        traverse(child);
        child = child.nextSibling;
      }
    }
    traverse(root);
    return results;
  }

  // 300ミリ秒周期でボタンを検知して非表示化
  setInterval(() => {
    // 1. df-cart-button コンポーネントを隠す
    querySelectorAllShadow('df-cart-button').forEach(el => {
      el.style.setProperty('display', 'none', 'important');
    });

    // 2. 'Add to cart' テキストまたはカートアイコンが含まれる md-filled-button を隠す
    querySelectorAllShadow('md-filled-button').forEach(el => {
      const icon = el.querySelector('md-icon');
      const hasCartIcon = icon && icon.textContent.trim() === 'shopping_cart';
      const hasCartText = el.textContent.toLowerCase().includes('add to cart');
      if (hasCartIcon || hasCartText) {
        el.style.setProperty('display', 'none', 'important');
      }
    });
  }, 300);
});
```

### 4. 影響範囲
* **商品検索**: 商品検索結果カルーセルカードの下部にあるカートアイコンおよびボタンが非表示になります。
* **商品詳細**: 商品詳細カードの下部に表示されるカート追加ボタンが非表示になります。
* **商品比較**: 比較テーブルの下部に配置されるカート追加用丸型ボタンが非表示になります。
