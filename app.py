import streamlit as st
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
import json
import os
import urllib.parse

# 1. 앱 기본 설정
st.set_page_config(page_title="리틀 알케미 3", page_icon="🧪", layout="wide")
st.title("🧪 리틀 알케미 3")

# 2. JSON 데이터 로드
@st.cache_data
def load_game_data():
    if not os.path.exists("recipes.json"):
        return {"recipes": {}}
    with open("recipes.json", "r", encoding="utf-8") as f:
        return json.load(f)

game_data = load_game_data()
RECIPES = game_data.get("recipes", {})

# 3. 게임 세션 상태
DEFAULT_ELEMENTS = ["물", "불", "흙", "공기"]
if "elements" not in st.session_state:
    st.session_state.elements = DEFAULT_ELEMENTS.copy()

# 4. 사이드바
with st.sidebar:
    st.header("🛠️ 관리자 메뉴")
    if st.button("🔄 전체 초기화", use_container_width=True):
        st.session_state.elements = DEFAULT_ELEMENTS.copy()
        st.query_params.clear()
        st.toast("게임이 완전히 리셋되었습니다!", icon="♻️")
        st.rerun()

    st.markdown("---")
    cheat_code = st.text_input("🔑 치트키", type="password", placeholder="admin123")
    if cheat_code == "admin123":
        if st.button("🌟 모든 원소 해금", use_container_width=True):
            all_elements = set(DEFAULT_ELEMENTS) | set(RECIPES.values())
            st.session_state.elements = list(all_elements)
            st.success("모든 원소가 해금되었습니다!")
            st.rerun()

# 5. JS → Python 동기화 (새로운 방식)
# sessionStorage에 pending_new_element가 있으면 추가
pending = st_javascript("sessionStorage.getItem('pending_new_element') || ''")
if pending and pending.strip():
    if pending not in st.session_state.elements:
        st.session_state.elements.append(pending)
        st.toast(f"🎉 새로운 물질 발견: {pending}!", icon="✨")
    st_javascript("sessionStorage.removeItem('pending_new_element')")

# 6. 프론트엔드 (대혁신 버전)
elements_json = json.dumps(st.session_state.elements)
recipes_json = json.dumps(RECIPES)

html_code = f"""
<style>
    .element-card {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 10px 16px;
        background: linear-gradient(145deg, #f8f9fa, #e9ecef);
        border: 2px solid #adb5bd;
        border-radius: 10px;
        font-size: 15px;
        font-weight: 700;
        color: #212529;
        cursor: grab;
        user-select: none;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        transition: transform 0.1s, box-shadow 0.1s;
    }}
    .element-card:active {{
        transform: scale(0.95);
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }}
    .placed-node {{
        position: absolute;
        padding: 9px 16px;
        background: linear-gradient(145deg, #e7f5ff, #d0ebff);
        border: 2.5px solid #339af0;
        border-radius: 10px;
        font-size: 14px;
        font-weight: 700;
        color: #1864ab;
        cursor: grab;
        user-select: none;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        z-index: 10;
        white-space: nowrap;
    }}
    .placed-node:hover {{
        box-shadow: 0 6px 12px rgba(51, 154, 240, 0.3);
    }}
</style>

<div style="display: flex; flex-direction: column; gap: 12px; font-family: system-ui, sans-serif;">
    <div style="display: flex; gap: 12px; align-items: center;">
        <button id="clear-board" style="padding: 8px 18px; background: #fa5252; color: white; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 14px;">
            🗑️ 작업판 비우기
        </button>
        <div style="color: #868e96; font-size: 13px;">💡 원소를 끌어서 다른 원소 위에 놓으면 합성됩니다</div>
    </div>

    <div style="display: flex; gap: 20px; min-height: 560px;">
        <!-- 작업판 -->
        <div id="drop-zone" style="flex: 2.2; border: 3px dashed #ced4da; border-radius: 18px; position: relative; background: #f8f9fa; overflow: hidden; box-shadow: inset 0 2px 8px rgba(0,0,0,0.05);">
            <div id="hint-text" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #adb5bd; font-size: 18px; text-align: center; pointer-events: none; line-height: 1.6;">
                🎒 오른쪽 인벤토리에서 원소를 끌어다 놓으세요<br>
                🖱️ 작업판 위에서 <b>드래그</b>해서 이동하고,<br>
                <b>다른 원소 위에 놓으면</b> 합성 시도!
            </div>
            <div id="workspace" style="position: absolute; width:100%; height:100%; top:0; left:0;"></div>
        </div>

        <!-- 인벤토리 -->
        <div style="flex: 1; border: 1px solid #dee2e6; padding: 18px; border-radius: 18px; background: white; max-height: 560px; overflow-y: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 14px 0; color: #495057; font-size: 17px;">🎒 보유 원소 ({len(st.session_state.elements)})</h3>
            <div id="inventory" style="display: flex; flex-wrap: wrap; gap: 10px;"></div>
        </div>
    </div>
</div>

<script>
    const elements = {elements_json};
    const RECIPES = {recipes_json};
    const inventory = document.getElementById('inventory');
    const dropZone = document.getElementById('drop-zone');
    const workspace = document.getElementById('workspace');
    const hintText = document.getElementById('hint-text');
    const clearBtn = document.getElementById('clear-board');

    let placedElements = [];
    let draggedName = null;
    let activeDrag = null;
    let offsetX = 0, offsetY = 0;

    // 세션에서 작업판 복구
    const saved = sessionStorage.getItem('alchemy_workspace');
    if (saved) {{
        const items = JSON.parse(saved);
        if (items.length > 0) hintText.style.display = 'none';
        items.forEach(item => {{
            if (elements.includes(item.name)) createNode(item.name, item.x, item.y);
        }});
    }}

    // 인벤토리 렌더링
    function renderInventory() {{
        inventory.innerHTML = '';
        elements.forEach(name => {{
            const div = document.createElement('div');
            div.className = 'element-card';
            div.innerText = name;
            div.draggable = true;
            div.addEventListener('dragstart', () => {{ draggedName = name; }});
            inventory.appendChild(div);
        }});
    }}
    renderInventory();

    // 작업판에 새 노드 생성
    function createNode(name, x, y) {{
        const node = document.createElement('div');
        node.className = 'placed-node';
        node.innerText = name;
        node.style.left = x + 'px';
        node.style.top = y + 'px';
        workspace.appendChild(node);

        const obj = {{ name, x, y, dom: node }};
        placedElements.push(obj);
        saveWorkspace();

        // 드래그 시작 (왼쪽 마우스)
        node.addEventListener('mousedown', (e) => {{
            if (e.button !== 0) return; // 왼쪽 버튼만
            activeDrag = obj;
            const rect = node.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            e.stopPropagation();
            e.preventDefault();
        }});

        node.addEventListener('contextmenu', e => e.preventDefault());
    }}

    // 작업판 드롭 (인벤토리 → 작업판)
    dropZone.addEventListener('dragover', e => e.preventDefault());
    dropZone.addEventListener('drop', (e) => {{
        e.preventDefault();
        if (!draggedName) return;
        hintText.style.display = 'none';
        const rect = dropZone.getBoundingClientRect();
        const x = e.clientX - rect.left - 35;
        const y = e.clientY - rect.top - 18;
        createNode(draggedName, x, y);
        draggedName = null;
    }});

    // 마우스 이동 (드래그 중)
    window.addEventListener('mousemove', (e) => {{
        if (!activeDrag) return;
        const rect = dropZone.getBoundingClientRect();
        let x = e.clientX - rect.left - offsetX;
        let y = e.clientY - rect.top - offsetY;
        x = Math.max(0, Math.min(x, rect.width - activeDrag.dom.offsetWidth));
        y = Math.max(0, Math.min(y, rect.height - activeDrag.dom.offsetHeight));
        activeDrag.x = x;
        activeDrag.y = y;
        activeDrag.dom.style.left = x + 'px';
        activeDrag.dom.style.top = y + 'px';
    }});

    // 마우스 놓기 (드래그 종료)
    window.addEventListener('mouseup', (e) => {{
        if (!activeDrag) return;
        saveWorkspace();
        checkDropOnOther(activeDrag);
        activeDrag = null;
    }});

    // 다른 원소 위에 놓았는지 검사 → 합성 시도
    function checkDropOnOther(releasedObj) {{
        for (let i = 0; i < placedElements.length; i++) {{
            const other = placedElements[i];
            if (other === releasedObj) continue;

            // 간단한 겹침 판정 (중심점 기준)
            const dist = Math.hypot(
                (releasedObj.x + releasedObj.dom.offsetWidth/2) - (other.x + other.dom.offsetWidth/2),
                (releasedObj.y + releasedObj.dom.offsetHeight/2) - (other.y + other.dom.offsetHeight/2)
            );

            if (dist < 65) {{ // 겹침 기준
                tryCombine(releasedObj, other);
                return;
            }}
        }}
    }}

    // 실제 합성 처리 (즉시 시각적 반응)
    function tryCombine(objA, objB) {{
        const names = [objA.name, objB.name].sort();
        const key = names.join(',');
        const result = RECIPES[key];

        if (!result) {{
            // 합성 실패 시 그냥 위치 저장
            return;
        }}

        // 시각적으로 두 개 제거하고 새 원소 생성
        removeNode(objA);
        removeNode(objB);

        const avgX = (objA.x + objB.x) / 2;
        const avgY = (objA.y + objB.y) / 2;
        createNode(result, avgX, avgY);

        // Python에 새 발견 알리기
        sessionStorage.setItem('pending_new_element', result);

        // Streamlit rerun 강제 트리거
        setTimeout(() => {{
            window.top.location.search = '?t=' + Date.now();
        }}, 80);
    }}

    function removeNode(obj) {{
        if (obj.dom && obj.dom.parentNode) {{
            obj.dom.parentNode.removeChild(obj.dom);
        }}
        const idx = placedElements.indexOf(obj);
        if (idx > -1) placedElements.splice(idx, 1);
    }}

    function saveWorkspace() {{
        const data = placedElements.map(el => ({{ name: el.name, x: el.x, y: el.y }}));
        sessionStorage.setItem('alchemy_workspace', JSON.stringify(data));
    }}

    // 작업판 비우기
    clearBtn.addEventListener('click', () => {{
        workspace.innerHTML = '';
        placedElements = [];
        sessionStorage.removeItem('alchemy_workspace');
        hintText.style.display = 'block';
    }});
</script>
"""

components.html(html_code, height=620)
