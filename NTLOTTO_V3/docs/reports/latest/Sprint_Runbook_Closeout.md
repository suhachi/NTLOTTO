# RUNBOOK 패치 완료 보고서 (Sprint_Runbook_Closeout.md)

요청하신 "RUNBOOK_V3.md 필수 텍스트 2줄 교체" 및 "알림 메시지/완료보고서 텍스트 완화 4줄 적용" 작업을 정상적으로 수행했습니다.

변경 내용은 다음과 같습니다.

## 1. RUNBOOK_V3.md 교체 내역 (2줄)

**(1) set_strategy_cli 명령 줄 (p_max, oversample_factor 고정)**
- [교체 전]
`python -m ntlotto.cli.set_strategy_cli --round 1213 --M 50 --seed 20260222 --p_max 0.16 --ev_slots_max 5 --fallback_max 5 \`
- [교체 후]
`python -m ntlotto.cli.set_strategy_cli --round 1213 --M 50 --seed 20260222 --p_max 0.16 --ev_slots_max 5 --fallback_max 5 --oversample_factor 40 \`

**(2) “운영 원칙” 헌법 문장 (기본값 표기)**
- [교체 전]
`- 헌법(중복/쏠림)은 전역 적용, 위반 시 FAIL`
- [교체 후]
`- 헌법(중복/쏠림)은 전역 적용, 위반 시 FAIL (p_max 기본 0.16, 권장 범위 0.14~0.18)`

---

## 2. 완료보고서(Closeout) 텍스트 정리 내역 (4줄)

**(3) p_max 예시값 변경**
- [교체 전]
  `--p_max 0.20 --ev_slots_max 5 --fallback_max 5 \`
- [교체 후]
  `--p_max 0.16 --ev_slots_max 5 --fallback_max 5 \`

**(4) “보고서 양식 위반” 단정 문구 변경**
- [교체 전]
`보고서 양식 위반: 필수 헤더(ex. # 1. 기초 지표) 누락 시 즉결 에러 발생`
- [교체 후]
`보고서 양식 위반: 계약서에 정의된 필수 섹션(WHY_LONG_SECTIONS / WHY_SHORT_SECTIONS) 누락 시 FAIL-FAST`

**(5) GitHub 푸시 단정 표현 제거**
- [교체 전]
`모든 코드는 GitHub에 feat(runbook): hard-lock contracts + add strategy CLI for quota text input 커밋으로 안전하게 푸시되었습니다.`
- [교체 후]
`작업 로그 기준으로 feat(runbook): hard-lock contracts + add strategy CLI for quota text input 커밋이 원격 저장소에 반영된 것으로 보고되었습니다.`

**(6) “즉시 투입 가능” 단정 완화**
- [교체 전]
`이제 운영팀은 데이터 최신화 이후 위 RUNBOOK_V3.md에 명시된 짧은 명령어 세 줄만 순차적으로 치면 완벽하게 잠재된 룰에 따라 조합을 획득할 수 있습니다.`
- [교체 후]
`이제 운영팀은 데이터 최신화 이후 RUNBOOK_V3.md의 명령 3단계를 순차 실행하면, 계약/헌법 검증(PASS 기록)을 전제로 조합을 산출할 수 있습니다.`
