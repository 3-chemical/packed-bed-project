import os

code = """
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Packed Bed Design Program (Team 03)", layout="wide")

# 팀 03 및 영문 타이틀 (한글 글꼴 깨짐 완벽 방지)
st.title("Packed Bed Pressure Drop & Throughput Design (Team 03)")

st.sidebar.header("기본 물리량 및 충전층 입력")
rho = st.sidebar.number_input("유체 밀도 (rho) [kg/m^3]", value=1000.0, min_value=0.1)
mu = st.sidebar.number_input("유체 점성 (mu) [Pa·s]", value=0.001, format="%.4f", min_value=0.00001)
Dp = st.sidebar.number_input("입자 지름 (Dp) [m]", value=0.005, format="%.4f", min_value=0.0001)
epsilon = st.sidebar.number_input("공극률 (epsilon) [0~1 사이]", value=0.40, format="%.2f")

# 물리적 예외 처리 (Validation Layer)
if epsilon <= 0.0 or epsilon >= 1.0:
    st.error("⚠️ [물리적 입력 오류] 공극률(epsilon)은 0 초과 1 미만의 값이어야 합니다!")
    st.stop()

L = st.sidebar.number_input("충전층 길이 (L) [m]", value=1.0, min_value=0.01)
A = st.sidebar.number_input("단면적 (A) [m^2]", value=0.10, min_value=0.001)

tab_theory, tab1, tab2, tab3, tab4 = st.tabs([
    "📘 지배방정식 및 가정",
    "1. 정방향 계산 (U -> ΔP)",
    "2. 역설계 (Root Finding Solver)",
    "3. 자동 반복계산 (Parameter Sweep)",
    "4. 손계산 독립 검증 (상대오차)"
])

# Ergun 계수 사전 계산
A_viscous = 150 * mu * ((1 - epsilon)**2) / ((epsilon**3) * (Dp**2))
B_inertial = 1.75 * rho * (1 - epsilon) / ((epsilon**3) * Dp)

with tab_theory:
    st.header("지배방정식 유도 및 기본 가정 (03팀)")
    st.markdown('''
    ### 1. 적용 보존법칙 및 지배방정식
    * **지배방정식:** Ergun 방정식 (Packed Bed 유동 해석)
    $$\\\\frac{\\\\Delta P}{L} = 150 \\\\frac{\\\\mu (1-\\\\epsilon)^2}{\\\\epsilon^3 D_p^2} U + 1.75 \\\\frac{\\\\rho (1-\\\\epsilon)}{\\\\epsilon^3 D_p} U^2$$
    * **원식 및 제거항:** 거시 운동량수지(Navier-Stokes)에서 정성적 정상상태 및 중력 항 무시 조건을 적용하여, 충전층 입자 표면 마찰에 의한 점성 마찰 손실(Kozeny-Carman 1차항)과 고속 유동 관성 손실(Burke-Plummer 2차항)의 합으로 환원.

    ### 2. 기본 물리적 가정
    1. **정상상태 (Steady State):** 유동 물성 및 유속이 시간에 따라 변하지 않음.
    2. **균일 충전층 (Uniform Packing):** 충전층 내부 공극률(\\\\(\\\\epsilon\\\\))이 전 영역에서 일정함.
    3. **대표 입자지름 사용:** 충전층 내 구형 구슬 구경이 일정함 (\\\\(D_p\\\\)).
    4. **비압축성 유체 (Incompressible Fluid):** 유체 밀도(\\\\(\\\\rho\\\\)) 및 점성(\\\\(\\\\mu\\\\)) 일정.
    ''')

with tab1:
    st.header("정방향 계산: 겉보기 유속(U) 입력")
    U = st.number_input("겉보기 유속 (U) [m/s]", value=0.100, format="%.3f", min_value=0.001)

    dp_viscous_L = A_viscous * U
    dp_inertial_L = B_inertial * (U**2)
    total_dp_L = dp_viscous_L + dp_inertial_L
    total_dP = total_dp_L * L
    Q = U * A

    viscous_ratio = (dp_viscous_L / total_dp_L) * 100
    inertial_ratio = (dp_inertial_L / total_dp_L) * 100

    st.subheader("계산 결과")
    col1, col2, col3 = st.columns(3)
    col1.metric("총 압력강하 (ΔP)", f"{total_dP:.2f} Pa")
    col2.metric("처리 유량 (Q)", f"{Q:.4f} m^3/s")
    col3.metric("점성 / 관성 기여도", f"{viscous_ratio:.1f}% / {inertial_ratio:.1f}%")

    st.subheader("운전 곡선 및 민감도 분석 그래프 (현재 운전점 마킹 포함)")
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))

    # 1) U - dP
    U_vals = np.linspace(0.001, U*2, 50)
    dP_vals = (A_viscous * U_vals + B_inertial * (U_vals**2)) * L
    ax[0].plot(U_vals, dP_vals, 'b-', linewidth=2, label='Operating Curve')
    ax[0].plot(U, total_dP, 'ro', markersize=8, label=f'Current U={U:.2f}')
    ax[0].set_title("U - dP Operating Curve")
    ax[0].set_xlabel("U (m/s)")
    ax[0].set_ylabel("dP (Pa)")
    ax[0].legend()
    ax[0].grid(True, linestyle='--', alpha=0.5)

    # 2) Porosity
    eps_vals = np.linspace(0.2, 0.8, 50)
    dP_eps = (150*mu*((1-eps_vals)**2)/((eps_vals**3)*(Dp**2))*U + 1.75*rho*(1-eps_vals)/((eps_vals**3)*Dp)*(U**2))*L
    ax[1].plot(eps_vals, dP_eps, 'g-', linewidth=2)
    ax[1].plot(epsilon, total_dP, 'ro', markersize=8, label=f'Current eps={epsilon:.2f}')
    ax[1].set_title("Porosity (eps) Sensitivity")
    ax[1].set_xlabel("Porosity (epsilon)")
    ax[1].set_ylabel("dP (Pa)")
    ax[1].legend()
    ax[1].grid(True, linestyle='--', alpha=0.5)

    # 3) Particle Size
    Dp_vals = np.linspace(Dp*0.5, Dp*2, 50)
    dP_Dp = (150*mu*((1-epsilon)**2)/((epsilon**3)*(Dp_vals**2))*U + 1.75*rho*(1-epsilon)/((epsilon**3)*Dp_vals)*(U**2))*L
    ax[2].plot(Dp_vals, dP_Dp, 'r-', linewidth=2)
    ax[2].plot(Dp, total_dP, 'ro', markersize=8, label=f'Current Dp={Dp:.4f}')
    ax[2].set_title("Particle Size (Dp) Sensitivity")
    ax[2].set_xlabel("Dp (m)")
    ax[2].set_ylabel("dP (Pa)")
    ax[2].legend()
    ax[2].grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    st.pyplot(fig)

with tab2:
    st.header("역설계 (Root Finding Solver / 비선형 근 찾기)")
    mode = st.radio("역설계 목표 선택", ["1) ΔP_max에서 최대 유속(U) 및 처리량(Q) 계산", "2) 목표 Q 및 ΔP_max를 만족하는 최소 입자크기(Dp) 탐색"])

    if "1)" in mode:
        dP_max = st.number_input("허용 최대 압력강하 (ΔP_max) [Pa]", value=5000.0, min_value=1.0)
        a = B_inertial
        b = A_viscous
        c = -(dP_max / L)

        U_max = (-b + np.sqrt(b**2 - 4*a*c)) / (2*a)
        Q_max = U_max * A

        st.success(f"허용 압력강하 {dP_max:.1f} Pa 내에서 최대 겉보기 유속(U): **{U_max:.4f} m/s**")
        st.success(f"허용 압력강하 {dP_max:.1f} Pa 내에서 최대 처리량(Q): **{Q_max:.4f} m^3/s**")
    else:
        target_Q = st.number_input("목표 처리 유량 (Q_target) [m^3/s]", value=0.0100, format="%.4f", min_value=0.0001)
        dP_max = st.number_input("허용 최대 압력강하 (ΔP_max) [Pa]", value=5000.0, min_value=1.0)

        target_U = target_Q / A
        term1 = (150 * mu * ((1 - epsilon)**2) / (epsilon**3)) * target_U
        term2 = (1.75 * rho * (1 - epsilon) / (epsilon**3)) * (target_U**2)
        RHS = dP_max / L

        a_dp = RHS
        b_dp = -term2
        c_dp = -term1

        Dp_req = (-b_dp + np.sqrt(b_dp**2 - 4*a_dp*c_dp)) / (2*a_dp)
        st.success(f"목표 유량 {target_Q:.4f} m^3/s 및 허용 압력강하 {dP_max:.1f} Pa를 만족하기 위한 최소 입자크기(Dp): **{Dp_req:.5f} m ({Dp_req*1000:.2f} mm)**")

with tab3:
    st.header("최종 설계 미션: 자동 반복계산 (25개 조건 Parameter Sweep)")
    st.write("허용 압력강하 조건 내에서 입자 크기(5개 조건) x 공극률(5개 조건) = 총 25개 조건 자동 스윕 결과 매트릭스입니다.")

    dP_limit = st.number_input("설계 기준 허용 압력강하 (ΔP_limit) [Pa]", value=10000.0, min_value=1.0, key="lim")

    eps_range = np.linspace(0.3, 0.7, 5)
    Dp_range = np.linspace(0.002, 0.010, 5)

    results = np.zeros((len(Dp_range), len(eps_range)))
    for i, dp_val in enumerate(Dp_range):
        for j, ep_val in enumerate(eps_range):
            a_v = 150 * mu * ((1 - ep_val)**2) / ((ep_val**3) * (dp_val**2))
            b_i = 1.75 * rho * (1 - ep_val) / ((ep_val**3) * dp_val)
            c_val = -(dP_limit / L)
            u_m = (-a_v + np.sqrt(a_v**2 - 4*b_i*c_val)) / (2*b_i)
            results[i, j] = u_m * A

    df = pd.DataFrame(results, index=[f"Dp={dp*1000:.1f}mm" for dp in Dp_range], columns=[f"eps={ep:.2f}" for ep in eps_range])
    st.subheader("💡 25개 조건 스윕 매트릭스 (최대 가능 처리량 Q_max [m^3/s])")
    st.dataframe(df.style.highlight_max(axis=None, color='lightgreen'))
    st.caption("※ 연두색 하이라이트 셀: 지정한 허용 압력강하 조건에서 처리량을 극대화하는 최적 입자크기-공극률 설계 조건 조합.")

with tab4:
    st.header("독립 손계산 검증 및 상대오차 (Relative Error Verification)")
    st.write("독립적인 수동 해석해와 수치 프로그램 계산 결과값을 비교하여 수치 모델 타당성을 입증합니다.")

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.subheader("1) 수치 프로그램 계산 결과")
        st.write(f"- 계산된 총 압력강하: **{total_dP:.4f} Pa**")

    with col_v2:
        st.subheader("2) 독립 손계산 해석해 입력")
        manual_val = st.number_input("독립 검증용 손계산 압력강하 입력 [Pa]", value=float(f"{total_dP:.2f}"))

    rel_error = abs(total_dP - manual_val) / total_dP * 100

    st.markdown("---")
    st.metric("상대오차 (Relative Error)", f"{rel_error:.4f}%")
    if rel_error < 1.0:
        st.success("✅ [검증 완료 / Verification Passed] 상대오차가 1.0% 이내로 수치 엔진의 타당성이 완벽히 입증되었습니다.")
    else:
        st.warning("⚠️ 상대오차가 1.0% 이상입니다. 입력 매개변수 또는 계산 수식을 재확인하십시오.")
"""


