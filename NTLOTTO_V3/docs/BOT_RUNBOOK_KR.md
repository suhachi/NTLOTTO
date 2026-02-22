# NTLOTTO V3 — 한국어 1문장 운영 봇

## 사용법(딱 4문장)
1) 분석/학습:
- "1212회차까지 데이터들을 분석/학습해"
→ 출력: 데이터분석/학습완료

2) 리포트 생성:
- "리포터를 작성해"
→ 출력: 리포트생성완료

3) 예측(전략+조합 생성):
- "NT4 10 / NT5 10 / NTO 15 / NT-Ω 5 / NT-VPA-1 5 / NT-LL 5 / NT-PAT 0 로 생성해"
※ 조합 생성 잠금 해제 필요: ALLOW_COMBO_GENERATION=1
→ 출력: 예측조합생성완료

4) 채점:
- "당첨번호 8 25 44 31 5 41 보너스 45 채점해"
→ 출력: 채점완료

## 실행 명령(고정)
```bash
python -m ntlotto.bot.krflow --say "1212회차까지 데이터들을 분석/학습해"
python -m ntlotto.bot.krflow --say "리포터를 작성해"
export ALLOW_COMBO_GENERATION=1
python -m ntlotto.bot.krflow --say "NT4 10 / NT5 10 / NTO 15 / NT-Ω 5 / NT-VPA-1 5 / NT-LL 5 / NT-PAT 0 로 생성해"
python -m ntlotto.bot.krflow --say "당첨번호 8 25 44 31 5 41 보너스 45 채점해"
```
