"""SK하이닉스 현재가를 조회해서 디스코드 웹훅으로 전송한다.

환경변수
  DISCORD_WEBHOOK_URL  디스코드 웹훅 URL (필수, DRY_RUN=1이면 생략 가능)
  STOCK_CODE           종목코드 (기본값 000660 = SK하이닉스)
  DRY_RUN              1이면 디스코드로 보내지 않고 콘솔에만 출력
"""

import json
import os
import sys
import urllib.request

STOCK_CODE = os.environ.get("STOCK_CODE", "000660")
API_URL = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{STOCK_CODE}"
USER_AGENT = "Mozilla/5.0 (compatible; hynix-discord-bot/1.0)"

# compareToPreviousPrice.code: 1 상한, 2 상승, 3 보합, 4 하한, 5 하락
DIRECTION = {
    "1": ("↑↑", "상한가", 0xE03131),
    "2": ("▲", "상승", 0xE03131),
    "3": ("-", "보합", 0x868E96),
    "4": ("↓↓", "하한가", 0x1971C2),
    "5": ("▼", "하락", 0x1971C2),
}


def fetch_quote():
    req = urllib.request.Request(API_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)
    return data["datas"][0]


def build_payload(q):
    code = q["compareToPreviousPrice"]["code"]
    arrow, label, color = DIRECTION.get(code, ("", "", 0x868E96))
    sign = "-" if code in ("4", "5") else "+" if code in ("1", "2") else ""

    change = f"{arrow} {q['compareToPreviousClosePrice']}원 ({sign}{q['fluctuationsRatio']}%)"
    traded_at = q["localTradedAt"][:19].replace("T", " ")
    status = "장중" if q.get("marketStatus") == "OPEN" else "장마감"

    return {
        "username": "주가 알림봇",
        "embeds": [
            {
                "title": f"{q['stockName']} ({q['itemCode']})",
                "url": f"https://finance.naver.com/item/main.naver?code={q['itemCode']}",
                "description": f"## {q['closePrice']}원\n{change}",
                "color": color,
                "fields": [
                    {"name": "시가", "value": f"{q['openPrice']}원", "inline": True},
                    {"name": "고가", "value": f"{q['highPrice']}원", "inline": True},
                    {"name": "저가", "value": f"{q['lowPrice']}원", "inline": True},
                    {"name": "거래량", "value": f"{q['accumulatedTradingVolume']}주", "inline": True},
                    {"name": "거래대금", "value": f"{q['accumulatedTradingValue']}원", "inline": True},
                    {"name": "상태", "value": f"{status} · {label}", "inline": True},
                ],
                "footer": {"text": f"기준 {traded_at} KST · 네이버 금융"},
            }
        ],
    }


def send_discord(webhook_url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status


def main():
    quote = fetch_quote()
    payload = build_payload(quote)

    if os.environ.get("DRY_RUN") == "1":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        sys.exit("DISCORD_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")

    status = send_discord(webhook_url, payload)
    print(f"전송 완료 ({status}): {quote['stockName']} {quote['closePrice']}원")


if __name__ == "__main__":
    main()
