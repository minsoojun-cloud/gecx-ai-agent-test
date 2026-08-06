import json
from urllib.parse import unquote

def get_identifiers_from_gecx_cookie(cookie_header_str: str) -> dict:
    """
    HTTP Header 'Cookie' 문자열에서 gecx_cookie를 파싱하여 visitor_id와 userid를 읽어옵니다.
    """
    visitor_id = None
    userid = None

    if cookie_header_str:
        # cookie 헤더 딕셔너리로 분할
        cookies = dict(
            item.strip().split("=", 1)
            for item in cookie_header_str.split(";")
            if "=" in item
        )

        if "gecx_cookie" in cookies:
            try:
                # URL 디코딩 후 JSON 파싱
                decoded_json = unquote(cookies["gecx_cookie"])
                data = json.loads(decoded_json)
                visitor_id = data.get("visitor_id")
                userid = data.get("userid") or data.get("user_id")
            except Exception as e:
                print(f"Failed to parse gecx_cookie: {e}")

    return {
        "status": "success",
        "visitor_id": visitor_id,
        "userid": userid
    }