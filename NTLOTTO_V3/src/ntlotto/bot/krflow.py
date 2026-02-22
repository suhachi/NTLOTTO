from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path

from ntlotto.bot.session_state import load_state, save_state, SessionState

def _run(cmd: list[str]) -> None:
    subprocess.check_call(cmd)

def _require_project_root() -> None:
    if not Path("data/ssot_sorted.csv").exists() or not Path("data/ssot_ordered.csv").exists():
        raise RuntimeError("[실행 위치 오류] NTLOTTO_V3 루트에서 실행하세요. (data/ssot_sorted.csv 없음)")

def _print_done(msg: str) -> None:
    # 사용자 요구: 완료 문구를 단일 출력
    print(msg)

def _parse_round_int(x: str) -> int:
    try:
        return int(x)
    except:
        raise ValueError(f"[입력 오류] 회차 숫자 파싱 실패: {x}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--say", type=str, required=True, help="자연어 한국어 1문장 명령")
    args = ap.parse_args()

    _require_project_root()
    st = load_state()

    s = args.say.strip()

    # 1) "<R>회차까지 데이터들을 분석/학습해"
    m = re.search(r"(\d+)\s*회차까지\s*데이터.*(분석|학습).*(해|해줘|해라)$", s)
    if m:
        R = _parse_round_int(m.group(1))

        # 분석/학습 정의(고정):
        # - make_reports로 WHY/엔진 리포트 생성(분석)
        # - eval_k_cli로 엔진 평가 리포트 생성(학습 근거)
        # ※ 여기서 조합 생성은 절대 하지 않음
        _run(["python","-m","ntlotto.cli.make_reports","--round",str(R),"--long","100","--short","5,10,15,20,25,30"])
        _run(["python","-m","ntlotto.cli.eval_k_cli","--k","20","--n","100"])

        st.analyzed_up_to_round = R
        # 리포트 대상은 기본적으로 "다음 회차"를 가정(운영 루프)
        st.report_round = R + 1
        save_state(st)
        _print_done("데이터분석/학습완료")
        return

    # 2) "리포터를 작성해" (리포트 생성)
    if re.search(r"(리포트|리포터).*(작성|만들|생성).*(해|해줘|해라)$", s):
        if st.report_round is None:
            raise RuntimeError("[상태 오류] 먼저 '<회차>회차까지 데이터들을 분석/학습해' 를 실행하세요.")
        R = st.report_round
        _run(["python","-m","ntlotto.cli.make_reports","--round",str(R),"--long","100","--short","5,10,15,20,25,30"])
        save_state(st)
        _print_done("리포트생성완료")
        return

    # 3) "… 로 생성해" (전략+조합 생성)
    # 입력 예:
    # "NT4 10 / NT5 10 / NTO 15 / NT-Ω 5 / NT-VPA-1 5 / NT-LL 5 / NT-PAT 0 로 생성해"
    if re.search(r"(생성해|만들어|뽑아)", s) and re.search(r"(NT4|NT5|NTO|NT-Ω|NT-VPA-1|NT-LL|NT-PAT)", s):
        if os.environ.get("ALLOW_COMBO_GENERATION") != "1":
            raise RuntimeError("조합 생성은 잠금 상태입니다. 먼저 환경변수 설정: ALLOW_COMBO_GENERATION=1")

        # 어떤 회차로 생성할지: report_round(=분석 up-to +1) 우선
        if st.report_round is None:
            raise RuntimeError("[상태 오류] 먼저 분석/학습 및 리포트 작성 단계를 완료하세요.")
        R = st.report_round

        quota_text = s
        quota_text = re.sub(r"(로\s*)?(생성해|만들어|뽑아).*?$", "", quota_text).strip()

        selection_path = f"docs/reports/latest/ENGINE_SELECTION_R{R}_M50.json"
        _run([
            "python","-m","ntlotto.cli.set_strategy_cli",
            "--round",str(R),
            "--M","50",
            "--seed","20260222",
            "--p_max","0.20",
            "--ev_slots_max","5",
            "--fallback_max","5",
            "--oversample_factor","200",
            "--text",quota_text,
            "--out",selection_path
        ])

        _run([
            "python","-m","ntlotto.cli.generate_combos_cli",
            "--round",str(R),
            "--selection",selection_path,
            "--i_understand_and_allow_generation"
        ])

        st.selection_path = selection_path
        st.predicted_round = R
        st.predicted_csv = f"docs/reports/latest/NTUC_{R}_M50_combos.csv"
        save_state(st)
        _print_done("예측조합생성완료")
        return

    # 4) "당첨번호 ... 보너스 ... 채점해"
    m = re.search(r"당첨번호\s+([0-9\s]+)\s+보너스\s+(\d+)\s+채점해", s)
    if m:
        if st.predicted_round is None or st.predicted_csv is None:
            raise RuntimeError("[상태 오류] 먼저 '...로 생성해'로 예측조합을 만든 뒤 채점하세요.")
        ordered_nums = [int(x) for x in m.group(1).split() if x.strip()]
        bonus = int(m.group(2))
        if len(ordered_nums) != 6:
            raise ValueError("[입력 오류] 당첨번호는 6개(추첨순서)여야 합니다. 예: 당첨번호 8 25 44 31 5 41 보너스 45 채점해")

        R = st.predicted_round
        _run([
            "python","-m","ntlotto.cli.score_round_cli",
            "--round",str(R),
            "--combos",st.predicted_csv,
            "--ordered"," ".join(map(str, ordered_nums)),
            "--bonus",str(bonus)
        ])
        _print_done("채점완료")
        return

    raise ValueError(
        "지원 명령 형식:\n"
        "1) '1212회차까지 데이터들을 분석/학습해'\n"
        "2) '리포터를 작성해'\n"
        "3) 'NT4 10 / ... / NT-PAT 0 로 생성해'\n"
        "4) '당첨번호 8 25 44 31 5 41 보너스 45 채점해'\n"
    )

if __name__ == "__main__":
    main()
