import streamlit as st
import streamlit.components.v1 as components
import json
import os

# 1. 앱 설정
st.set_page_config(page_title="텍스트 리틀 알케미", page_icon="🧪", layout="wide")
st.title("🧪 리틀 알케미 (자유 이동 및 합성 수정 버전)")

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

# 4. 사이드바 기능 (초기화 및 치트키)
with st.sidebar:
    st.header("🛠️ 관리자 메뉴")
    
    if st.button("🔄 게임 데이터 전체 초기화", use_container_width=True):
        st.session_state.elements = DEFAULT_ELEMENTS.copy()
        st.query_params.clear()
        st.toast("게임 데이터가 리셋되었습니다!", icon="♻️")
        st.rerun()
        
    st.markdown("---")
    cheat_code = st.text_input("🔑 치트키 입력", type="password")
    if cheat_code == "admin123":
        if st.button("🌟 모든 원소 해금", use_container_width=True):
            all_possible = set(DEFAULT_ELEMENTS) | set(RECIPES.values())
            st.session_state.elements = list(all_possible)
            st.success("모든 원소가 도감에 추가되었습니다!")
            st.rerun()

# 5. 백엔드 합성 로직 수정 (가나다 정렬 매칭)
query_params = st.query_params
if "combine" in query_params:
    combined_str = query_params["combine"]
    # 콤마로 분리 후 정렬하여 "물,불" 형태로 변환
    parts = sorted(combined_str.split(","))
    recipe_key = ",".join(parts)
    
    result = RECIPES.get(recipe_key)
    
    if result:
        if result not in st.session_state.elements:
            st.session_state.elements.append(result)
            st.toast(f"🎉 새로운 물질 발견: {result}!", icon="✨")
        else:
            st.toast(f"이미 발견한 물질입니다: {result}", icon="💡")
    else:
        st.toast("💥 합성 실패! 아무 일도 일어나지 않았습니다.", icon="💨")
        
    st.query_params.clear()

# 6. 프론트엔드 인터페이스 빌드 (HTML/CSS/JavaScript)
elements_json = json.dumps(st.session_state.elements)

html_code = f"""
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
        cursor: move;
        user-select: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 10;
    }}
</style>

<div style="display: flex; flex-direction: column; gap: 10px; font-family: sans-serif;">
    <div>
        <button id="clear-board" style="padding: 8px 16px; background: #fa5252; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
            🗑️ 작업판(캔버스) 비우기
        </button>
    </div>

    <div style="display: flex; gap: 20px; min-height: 520px;">
        <!-- 왼쪽: 작업판 -->
        <div id="drop-zone" style="flex: 2; border: 3px dashed #ced4da; border-radius: 15px; position: relative; background: #f8f9fa; overflow: hidden;">
            <div id="hint-text" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #adb5bd; font-size: 18px; font-weight: 500; pointer-events: none;">
                여기에 원소를 끌어다 놓으세요! 배치된 원소도 자유롭게 다시 움직이고 포갤 수 있습니다.
            </div>
            <div id="workspace" style="position: absolute; width:100%; height:100%; top:0; left:0;"></div>
        </div>

        <!-- 오른쪽: 인벤토리 -->
        <div style="flex: 1; border: 1px solid #dee2e6; padding: 15px; border-radius: 15px; background: #fff; max-height: 520px; overflow-y: auto;">
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
    
    // 작업판 내부 드래그 추적용 변수
    let activeNode = null;
    let offsetX = 0;
    let offsetY = 0;

    // 1. 인벤토리 드로우
    elements.forEach(name => {{
        const div = document.createElement('div');
        div.className = 'element-card';
        div.innerText = name;
        div.draggable = true;
        div.addEventListener('dragstart', () => {{ draggedName = name; }});
        inventory.appendChild(div);
    }});

    // 2. 인벤토리 -> 작업판 드롭 이벤트
    dropZone.addEventListener('dragover', (e) => e.preventDefault());
    dropZone.addEventListener('drop', (e) => {{
        e.preventDefault();
        if (!draggedName) return;

        hintText.style.display = 'none';
        const rect = dropZone.getBoundingClientRect();
        const x = e.clientX - rect.left - 30;
        const y = e.clientY - rect.top - 15;

        createNode(draggedName, x, y);
        draggedName = null;
    }});

    // 3. 작업판 노드 생성 및 마우스 마우스 드래그 기능 바인딩
    function createNode(name, x, y) {{
        const node = document.createElement('div');
        node.className = 'placed-node';
        node.innerText = name;
        node.style.left = x + 'px';
        node.style.top = y + 'px';
        workspace.appendChild(node);

        const obj = {{ name: name, x: x, y: y, dom: node }};
        placedElements.push(obj);

        // 작업판 내부 마우스 드래그 시작
        node.addEventListener('mousedown', (e) => {{
            activeNode = obj;
            const rect = node.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            e.stopPropagation();
        }});

        checkCollision(obj);
    }}

    // 4. 작업판 내 드래그 이동 및 마우스 업 처리
    window.addEventListener('mousemove', (e) => {{
        if (!activeNode) return;
        
        const rect = dropZone.getBoundingClientRect();
        let x = e.clientX - rect.left - offsetX;
        let y = e.clientY - rect.top - offsetY;

        // 경계 아웃 방지
        x = Math.max(0, Math.min(x, rect.width - activeNode.dom.offsetWidth));
        y = Math.max(0, Math.min(y, rect.height - activeNode.dom.offsetHeight));

        activeNode.x = x;
        activeNode.y = y;
        activeNode.dom.style.left = x + 'px';
        activeNode.dom.style.top = y + 'px';
    }});

    window.addEventListener('mouseup', () => {{
        if (activeNode) {{
            checkCollision(activeNode);
            activeNode = null;
        }}
    }});

    // 5. 충돌 검사 (두 원소가 겹칠 시 백엔드로 보내 합성 유도)
    function checkCollision(targetObj) {{
        if (placedElements.length < 2) return;

        for (let i = 0; i < placedElements.length; i++) {{
            const other = placedElements[i];
            if (other === targetObj) continue;

            const dist = Math.hypot(targetObj.x - other.x, targetObj.y - other.y);
            
            // 75픽셀 미만으로 가까워지면 합성 시도
            if (dist < 75) {{
                const combineQuery = other.name + ',' + targetObj.name;
                window.parent.location.search = '?combine=' + encodeURIComponent(combineQuery);
                return;
            }}
        }}
    }}

    // 6. 작업판 비우기 버튼
    clearBtn.addEventListener('click', () => {{
        workspace.innerHTML = '';
        placedElements = [];
        hintText.style.display = 'block';
    }});
</script>
"""

# 7. 렌더링
components.html(html_code, height=600)
