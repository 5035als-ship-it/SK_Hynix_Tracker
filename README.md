# SK하이닉스 주가 디스코드 알림봇

GitHub Actions가 평일 장중(09:00~15:30 KST)에 5분마다 SK하이닉스(000660) 시세를 네이버 금융에서 가져와 디스코드 채널로 보냅니다. 외부 패키지 없이 Python 표준 라이브러리만 사용합니다.

## 설정 방법

1. **디스코드 웹훅 만들기**
   채널 설정 → 연동(Integrations) → 웹후크 → 새 웹후크 → **웹후크 URL 복사**

2. **GitHub 저장소에 올리기**
   ```bash
   git init
   git add .
   git commit -m "SK하이닉스 주가 알림봇"
   git branch -M main
   git remote add origin https://github.com/<계정>/<저장소>.git
   git push -u origin main
   ```

3. **Secret 등록**
   저장소 → Settings → Secrets and variables → Actions → New repository secret
   - Name: `DISCORD_WEBHOOK_URL`
   - Secret: 1번에서 복사한 웹훅 URL

4. **동작 확인**
   Actions 탭 → `SK하이닉스 주가 알림` → **Run workflow** 로 바로 한 번 실행해 보세요.

## 로컬 테스트

```bash
DRY_RUN=1 python3 stock_notify.py
```

## 참고

- GitHub Actions의 `schedule`은 최소 5분 간격이며, 서버 부하에 따라 **몇 분~수십 분 지연되거나 건너뛸 수 있습니다.** 정확한 5분 간격이 필요하면 서버/PC에서 cron을 돌리는 편이 낫습니다.
- 공개(public) 저장소에서 60일 동안 커밋이 없으면 예약 워크플로가 자동 비활성화됩니다. Actions 탭에서 다시 켜면 됩니다.
- 공휴일은 따로 거르지 않습니다(휴장일에도 전일 종가가 전송됨).
- 다른 종목은 워크플로의 `env`에 `STOCK_CODE: "005930"` 처럼 추가하면 됩니다.
