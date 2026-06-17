import streamlit as st
import streamlit.components.v1 as components
import json
import os

# 1. 앱 설정
st.set_page_config(page_title="텍스트 리틀 알케미", page_icon="🧪", layout="wide")
st.title("🧪 리틀 알케미 (텍스트 버전)")

# 2. JSON 데이터 로드
@st.cache_data
def load_game_data():
    if not os.path.exists("recipes.json"):
        return {"recipes": {}}
    with open("recipes.json", "r", encoding="utf-8") as f:
        return json.load(f)

game_data = load_game_data()
RECIPES = game_data.get("recipes", {})

# 3. 세션 상태 초기화 및 관리
DEFAULT_ELEMENTS = ["물", "불", "흙", "공기"]

if "elements" not in st.session_state:
    st.session_state.elements = DEFAULT_ELEMENTS.copy()

# 4. 사이드바 사이드 기능 (초기화 및 치트키)
with st.sidebar:
    st.header("🛠️ 관리자 메뉴")
    
    # 기능 1: 진행상황 전체 초기화
    if st.button("🔄 게임 데이터 전체 초기화", use_container_width=True):
        st.session_state.elements = DEFAULT_ELEMENTS.copy()
        st.query_params.clear()
        st.toast("게임 데이터가 처음으로 리셋되었습니다!", icon="♻️")
        st.rerun()
        
    # 기능 2: 제작자 전용 치트키
    st.markdown("---")
    cheat_code = st.text_input("🔑 치트키 입력", type="password")
    if cheat_code == "admin123":  # 원하는 치트키 비밀번호로 수정 가능
        if st.button("🌟 모든 원소 해금"):
            # 레시피에 존재하는 모든 결과물 가져오기
            all_possible = set(DEFAULT_ELEMENTS) | set(RECIPES.values())
            st.session_state.elements = list(all_possible)
            st.success("제작자 모드: 모든 원소가 도감에 추가되었습니다!")
            st.rerun()

# 5. 자바스크립트 조합 처리 스크립트
query_params = st.query_params
if "combine" in query_params:
    combined_str = query_params["combine"]
    parts = sorted(combined_str.split(","))
    
    # 콤마로 연결된 두 가지 경우의 수 모두 체크
    key1 = f"{parts[0]},{parts[1]}"
    key2 = f"{parts[1]},{parts[0]}"
    
    result = RECIPES.get(key1) or RECIPES.get(key2)
    
    if result:
        if result not in st.session_state.elements:
            st.session_state.elements.append(result)
            st.toast(f"🎉 새로운 물질 발견: {result}!", icon="✨")
        else:
            st.toast(f"이미 발견한 물질입니다: {result}", icon="💡")
    else:
        st.toast("💥 아무 일도 일어나지 않았습니다.", icon="💨")
        
    st.query_params.clear()

# 6. 프론트엔드 HTML / CSS / JavaScript 구현
elements_json = json.dumps(st.session_state.elements)

html_code = f"""
<!-- 스타일 정의: 깔끔한 텍스트 상자 디자인 -->
<style>
    .element-card {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 10px 16px;
        background: #f1f3f5;
        border: 2px solid #dee2e6;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        color: #212529;
        cursor: grab;
        user-select: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .element-card:active {{ cursor: grabbing; }}
    
    .placed-node {{
        position: absolute;
        padding: 8px 14px;
        background: #e7f5ff;
        border: 2px solid #339af0;
        border-radius: 8px;
        font-size: 13px;
        font-weight: bold;
        color: #1c7ed6;
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
</style>

<div style="display: flex; flex-direction: column; gap: 10px; font-family: sans-serif;">
    <!-- 기능 3: 작업판 비우기 버튼 -->
    <div>
        <button id="clear-board" style="padding: 8px 16px; background: #fa5252; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
            🗑️ 작업판(캔버스) 비우기
        </button>
    </div>

    <div style="display: flex; gap: 20px; min-height: 500px;">
        <!-- 왼쪽: 조합 실험실 드롭 존 -->
        <div id="drop-zone" style="flex: 2; border: 3px dashed #ced4da; border-radius: 15px; position: relative; background: #f8f9fa;">
            <div id="hint-text" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #adb5bd; font-size: 18px; font-weight: 500; pointer-events: none;">
                여기에 원소들을 끌어다 놓고 서로 포개보세요!
            </div>
            <div id="workspace" style="position: absolute; width:100%; height:100%; top:0; left:0;"></div>
        </div>

        <!-- 오른쪽: 인벤토리 -->
        <div style="flex: 1; border: 1px solid #dee2e6; padding: 15px; border-radius: 15px; background: #fff; max-height: 500px; overflow-y: auto;">
            <h3 style="margin-top:0; color: #495057;">🎒 보유 인벤토리 ({len(st.session_state.elements)})</h3>
            <div id="inventory" style="display: flex; flex-wrap: wrap; gap: 10px;"></div>
        </div>
    </div>
</div>

<script>
    const elements = {elements_json};
    const inventory = document.getElementById('inventory');
    const dropZone = document.getElementById('drop-zone');
    const workspace = document.getElementById('workspace');
    const hintText = document.getElementById('hint-text');
    const clearBtn = document.getElementById('clear-board');

    let draggedName = null;
    let placedElements = [];

    // 1. 인벤토리 목록 그리기
    elements.forEach(name => {{
        const div = document.createElement('div');
        div.className = 'element-card';
        div.innerText = name;
        div.draggable = true;
        
        div.addEventListener('dragstart', () => {{ draggedName = name; }});
        inventory.appendChild(div);
    }});

    // 2. 드래그 앤 드롭 이벤트
    dropZone.addEventListener('dragover', (e) => e.preventDefault());

    dropZone.addEventListener('drop', (e) => {{
        e.preventDefault();
        if (!draggedName) return;

        hintText.style.display = 'none';

        const rect = dropZone.getBoundingClientRect();
        const x = e.clientX - rect.left - 35;
        const y = e.clientY - rect.top - 15;

        // 작업판 위에 텍스트 박스 생성
        const node = document.createElement('div');
        node.className = 'placed-node';
        node.style.left = x + 'px';
        node.style.top = y + 'px';
        node.innerText = draggedName;
        workspace.appendChild(node);

        const newObj = {{ name: draggedName, x: x, y: y, dom: node }};
        placedElements.push(newObj);

        // 충돌 검사 (두 텍스트 박스가 겹치는지 체크)
        if (placedElements.length >= 2) {{
            for (let i = 0; i < placedElements.length - 1; i++) {{
                const prev = placedElements[i];
                const dist = Math.hypot(newObj.x - prev.x, newObj.y - prev.y);

                // 두 박스 간 거리가 70픽셀 미만이면 조합 요청 수행
                if (dist < 70) {{
                    const combineQuery = prev.name + ',' + newObj.name;
                    window.parent.location.search = '?combine=' + encodeURIComponent(combineQuery);
                    return;
                }}
            }}
        }}
        draggedName = null;
    }});

    // 3. 기능: 작업판 비우기 액션
    clearBtn.addEventListener('click', () => {{
        workspace.innerHTML = '';
        placedElements = [];
        hintText.style.display = 'block';
    }});
</script>
"""

# 7. 컴포넌트 렌더링
components.html(html_code, height=580)
st.caption("💡 사용 방법: 인벤토리의 글자를 드래그하여 회색 작업판에 놓으세요. 두 글자 상자를 서로 겹치면 조합을 시도합니다.")
