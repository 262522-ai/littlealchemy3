import streamlit as st

# 1. 앱 제목 및 기본 UI 설정
st.set_page_config(page_title="나만의 리틀 알케미", page_icon="🧪")
st.title("🧪 리틀 알케미 클론")
st.write("두 가지 원소를 조합하여 새로운 원소를 발견해보세요!")

# 2. 조합 레시피 데이터 사전 정의
RECIPES = {
    frozenset(["물", "불"]): "증기",
    frozenset(["물", "흙"]): "진흙",
    frozenset(["불", "흙"]): "용암",
    frozenset(["공기", "불"]): "에너지",
    frozenset(["공기", "용암"]): "돌",
    frozenset(["물", "용암"]): "옵시디언",
    # 원하는 조합 레시피를 여기에 계속 추가할 수 있습니다.
}

# 3. 게임 상태 초기화 (초기 4대 원소)
if "elements" not in st.session_state:
    st.session_state.elements = ["물", "불", "흙", "공기"]
if "discovered_recipes" not in st.session_state:
    st.session_state.discovered_recipes = []

# 4. 화면 레이아웃 분할
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎒 내가 가진 원소")
    # 세로로 길어질 것에 대비하여 멀티셀렉트나 라디오 버튼으로 원소 선택
    el1 = st.selectbox("첫 번째 원소 선택", st.session_state.elements, key="el1")
    el2 = st.selectbox("두 번째 원소 선택", st.session_state.elements, key="el2")
    
    # 조합 버튼
    if st.button("🔮 조합하기"):
        if el1 == el2:
            st.warning("서로 다른 원소를 선택하거나 신중하게 조합해보세요!")
        else:
            combination = frozenset([el1, el2])
            if combination in RECIPES:
                result = RECIPES[combination]
                
                # 새로운 원소 발견 처리
                if result not in st.session_state.elements:
                    st.session_state.elements.append(result)
                    st.success(f"🎉 새로운 원소 발견: **{result}**!!")
                else:
                    st.info(f"이미 알고 있는 원소입니다: **{result}**")
            else:
                st.error("💥 아무 일도 일어나지 않았습니다.")

with col2:
    st.subheader("📜 도감 및 통계")
    st.write(f"현재 발견한 원소 개수: **{len(st.session_state.elements)}**개")
    st.write("보유 중인 원소 리스트:")
    st.write(", ".join(st.session_state.elements))
