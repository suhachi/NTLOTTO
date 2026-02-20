# NT Project Lotto Engine - vNext Architecture

> **[2026-02-15 UPDATE]**: 본 프로젝트는 `NT_Engines` 중심의 아키텍처로 개편되었습니다. 상세 구조는 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)를 참조하십시오.

## 개요
본 저장소는 NT 프로젝트의 **채점, 학습, 점수 계산 코어**입니다. 
SSOT(Single Source of Truth) 원칙에 따라 모든 로직은 `00_Data_Center`의 데이터와 `NT_Engines` 내의 `rules.md`를 기반으로 동작합니다.

## 핵심 규칙 (Strict Constraints)
1. **조합 생성 금지**: 본 레포지토리 내 어느 코드에서도 로또 조합(6개 번호 세트)을 스스로 생성하지 않습니다.
2. **결정론적 실행**: 동일한 입력과 스키마에 대해 항상 동일한 점수와 채점 결과를 보장합니다.
3. **추적성**: 모든 점수는 Breakdown(성분별 분석)을 통해 검증 가능합니다.
4. **포트폴리오 다양성 (NEW)**: 최종 선발 단계에서 모든 조합쌍 간 공유 번호는 2개 이하여야 합니다 ($|C_i \cap C_j| \le 2$).

## 시스템 구조
- **SSOT Layer**: 사람이 읽는 문서와 기계가 읽는 YAML 스키마.
- **Core Layer**: 정규화, 통계, 피처 추출 등 수학적 기반.
- **Engine Layer**: NT4, NT5 등 각 방식별 스코어 모델.
- **Guard Layer**: 합계, 홀짝 등 제약 조건 필터.
- **Grading & Learning**: 성적 채점 및 가중치 업데이트(EMA).

## 실행 방법
### 테스트
```bash
npm test
```

### CLI 사용 (조합 생성 기능 없음)
```bash
# 분석 실행
npm run nt -- analyze --input data/draws.json --schema config/ssot/nt_methods.schema.yaml

# 채점 실행
npm run nt -- grade --pred results/1209_predictions.json --actual data/1209_actual.json
```

## SSOT 준수 체크리스트
| SSOT 항목 | 코드 모듈 | 검증 상태 |
| :--- | :--- | :--- |
| 공통 피처 (밴드, 합계 등) | `src/core/features.ts` | ✅ 반영 |
| 정규화 규칙 (MinMax, Softmax) | `src/core/normalize.ts` | ✅ 반영 |
| 엔진 수식 (NT4 등) | `src/engines/` | ✅ 반영 |
| 학습 업데이트 (EMA, Clamp) | `src/learning/updateWeights.ts` | 🏗️ 구현 중 |
| 가드 규칙 (Sum, OddEven) | `src/guards/index.ts` | ✅ 반영 |
