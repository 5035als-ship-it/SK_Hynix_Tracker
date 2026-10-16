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


NXT_SESSION = {
    "PRE_MARKET": "프리마켓",
    "REGULAR_MARKET": "메인마켓",
    "AFTER_MARKET": "애프터마켓",
}


def format_change(src):
    code = src["compareToPreviousPrice"]["code"]
    arrow, label, color = DIRECTION.get(code, ("", "", 0x868E96))
    sign = "-" if code in ("4", "5") else "+" if code in ("1", "2") else ""
    text = f"{arrow} {src['compareToPreviousClosePrice']}원 ({sign}{src['fluctuationsRatio']}%)"
    return text, label, color


def build_payload(q):
    # q 는 KRX 시세, overMarketPriceInfo 는 넥스트레이드(NXT) 시세
    nxt = q.get("overMarketPriceInfo")
    krx_open = q.get("marketStatus") == "OPEN"
    nxt_open = bool(nxt) and nxt.get("overMarketStatus") == "OPEN"

    # KRX 정규장이면 KRX 가격을, KRX 장외시간에 NXT가 열려 있으면 NXT 가격을 메인으로 표시
    if krx_open or not nxt_open:
        main, main_price, venue = q, q["closePrice"], "KRX"
        status = "KRX 정규장" if krx_open else "장마감"
    else:
        main, main_price, venue = nxt, nxt["overPrice"], "NXT"
        session = nxt.get("tradingSessionType", "")
        status = f"NXT {NXT_SESSION.get(session, session)}"

    change, label, color = format_change(main)
    traded_at = main["localTradedAt"][:19].replace("T", " ")

    fields = [
        {"name": "시가", "value": f"{main['openPrice']}원", "inline": True},
        {"name": "고가", "value": f"{main['highPrice']}원", "inline": True},
        {"name": "저가", "value": f"{main['lowPrice']}원", "inline": True},
        {"name": "거래량", "value": f"{main['accumulatedTradingVolume']}주", "inline": True},
        {"name": "거래대금", "value": f"{main['accumulatedTradingValue']}원", "inline": True},
        {"name": "상태", "value": f"{status} · {label}", "inline": True},
    ]

    # 메인이 아닌 쪽 시장 가격도 함께 표시
    if venue == "KRX" and nxt:
        other_change, _, _ = format_change(nxt)
        fields.append({"name": "NXT", "value": f"{nxt['overPrice']}원 {other_change}", "inline": False})
    elif venue == "NXT":
        other_change, _, _ = format_change(q)
        fields.append({"name": "KRX 종가", "value": f"{q['closePrice']}원 {other_change}", "inline": False})

    return {
        "username": "주가 알림봇",
        "embeds": [
            {
                "title": f"{q['stockName']} ({q['itemCode']}) · {venue}",
                "url": f"https://finance.naver.com/item/main.naver?code={q['itemCode']}",
                "description": f"## {main_price}원\n{change}",
                "color": color,
                "fields": fields,
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
    embed = payload["embeds"][0]
    print(f"전송 완료 ({status}): {embed['title']} {embed['description'].splitlines()[0][3:]}")


if __name__ == "__main__":
    main()
