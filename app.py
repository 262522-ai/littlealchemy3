import streamlit as st
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
import json
import os
import urllib.parse

# 1. 앱 기본 설정
st.set_page_config(page_title="텍스트 리틀 알케미", page_icon="🧪", layout="wide")
st.title("🧪 리틀 알케미")

# 2. JSON 데이터 로드
@st.cache_data
def load_game_data():
    if not os.path.exists("recipes.json"):
        return {"recipes": {}}
    with open("recipes.json", "r", encoding="utf-8") as f:
        return json.load(f)

game_data = load_game_data()
RECIPES = game_data.get("recipes", {})

# 3. 게임 세션 상태 정의
DEFAULT_ELEMENTS = ["물", "불", "흙", "공기"]
if "elements" not in st.session_state:
    st.session_state.elements = DEFAULT_ELEMENTS.copy()

# 4. 사이드바 메뉴 (초기화 및 치트키)
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

# 5. URL 합성 매칭 엔진 (기존 로직 유지)
url = st_javascript("window.location.href")
if url and "?combine=" in url:
    try:
        query_part = url.split("?combine=")[1].split("&")[0]
        combined_str = urllib.parse.unquote(query_part)
       
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
            st.toast(f"💥 합성 실패! 레시피가 없습니다. ({recipe_key})", icon="💨")
    except Exception as e:
        pass
   
    st_javascript("window.history.replaceState({}, document.title, window.location.pathname);")

# 6. 프론트엔드 인터페이스 (개선된 버전)
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
            <div id="hint-text" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #adb5bd; font-size: 17px; text-align: center; pointer-events: none; line-height: 1.5;">
                🎒 인벤토리에서 원소를 끌어다 놓으세요!<br>
                🖱️ <b>[우클릭 조작법]</b> 배치된 원소는 <b>오른쪽 마우스를 누른 채 이동</b>하고, <b>떼면</b> 고정됩니다.
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
   
    let activeNode = null;
    let offsetX = 0;
    let offsetY = 0;

    // 브라우저 세션에서 작업판 데이터 복구
    const savedState = sessionStorage.getItem('alchemy_workspace');
    if (savedState) {{
        const items = JSON.parse(savedState);
        if (items.length > 0) hintText.style.display = 'none';
        items.forEach(item => {{
            if (elements.includes(item.name)) {{
                createNode(item.name, item.x, item.y, false);
            }}
        }});
    }}

    // 인벤토리 목록 렌더링
    elements.forEach(name => {{
        const div = document.createElement('div');
        div.className = 'element-card';
        div.innerText = name;
        div.draggable = true;
        div.addEventListener('dragstart', () => {{ draggedName = name; }});
        inventory.appendChild(div);
    }});

    // 작업판 드롭
    dropZone.addEventListener('dragover', (e) => e.preventDefault());
    dropZone.addEventListener('drop', (e) => {{
        e.preventDefault();
        if (!draggedName) return;
        hintText.style.display = 'none';
        const rect = dropZone.getBoundingClientRect();
        const x = e.clientX - rect.left - 30;
        const y = e.clientY - rect.top - 15;
        createNode(draggedName, x, y, true);
        draggedName = null;
    }});

    // 노드 생성 함수 (크기 저장 추가)
    function createNode(name, x, y, triggerCheck) {{
        const node = document.createElement('div');
        node.className = 'placed-node';
        node.innerText = name;
        node.style.left = x + 'px';
        node.style.top = y + 'px';
        workspace.appendChild(node);

        const obj = {{ name: name, x: x, y: y, dom: node }};
        
        // ★ 중심점 계산을 위해 실제 렌더링된 크기 저장
        obj.width = node.offsetWidth || 70;
        obj.height = node.offsetHeight || 28;

        placedElements.push(obj);
        saveCurrentWorkspace();

        node.addEventListener('mousedown', (e) => {{
            if (e.button === 2) {{
                activeNode = obj;
                const rect = node.getBoundingClientRect();
                offsetX = e.clientX - rect.left;
                offsetY = e.clientY - rect.top;
                e.stopPropagation();
                e.preventDefault();
            }}
        }});
       
        node.addEventListener('contextmenu', (e) => e.preventDefault());

        if (triggerCheck) {{
            checkCollision(obj);
        }}
    }}

    window.addEventListener('mousemove', (e) => {{
        if (!activeNode) return;
       
        const rect = dropZone.getBoundingClientRect();
        let x = e.clientX - rect.left - offsetX;
        let y = e.clientY - rect.top - offsetY;
        x = Math.max(0, Math.min(x, rect.width - activeNode.dom.offsetWidth));
        y = Math.max(0, Math.min(y, rect.height - activeNode.dom.offsetHeight));
        activeNode.x = x;
        activeNode.y = y;
        activeNode.dom.style.left = x + 'px';
        activeNode.dom.style.top = y + 'px';
    }});

    window.addEventListener('mouseup', (e) => {{
        if (e.button === 2 && activeNode) {{
            saveCurrentWorkspace();
            checkCollision(activeNode);
            activeNode = null;
        }}
    }});
   
    dropZone.addEventListener('contextmenu', (e) => e.preventDefault());

    function saveCurrentWorkspace() {{
        const data = placedElements.map(el => ({{ name: el.name, x: el.x, y: el.y }}));
        sessionStorage.setItem('alchemy_workspace', JSON.stringify(data));
    }}

    // ★★★ 개선된 충돌 판정 (중심점 기준 + 디버그 로그) ★★★
    function checkCollision(targetObj) {{
        if (placedElements.length < 2) return;

        const targetW = targetObj.width || targetObj.dom.offsetWidth || 70;
        const targetH = targetObj.height || targetObj.dom.offsetHeight || 28;
        const targetCenter = {{
            x: targetObj.x + targetW / 2,
            y: targetObj.y + targetH / 2
        }};

        for (let i = 0; i < placedElements.length; i++) {{
            const other = placedElements[i];
            if (other === targetObj) continue;

            const otherW = other.width || other.dom.offsetWidth || 70;
            const otherH = other.height || other.dom.offsetHeight || 28;
            const otherCenter = {{
                x: other.x + otherW / 2,
                y: other.y + otherH / 2
            }};

            const dist = Math.hypot(targetCenter.x - otherCenter.x, targetCenter.y - otherCenter.y);

            // F12 콘솔에서 확인 가능 (디버깅용)
            console.log(`[합성체크] ${{targetObj.name}} ↔ ${{other.name}} | 거리: ${{dist.toFixed(1)}}px`);

            if (dist < 80) {{   // ← 이 숫자를 70~100 사이로 조절하면서 테스트하세요
                const combineQuery = other.name + ',' + targetObj.name;
                
                // iframe 환경 호환성을 위해 window.top과 window.parent 둘 다 시도
                try {{
                    const targetWin = window.top || window.parent;
                    targetWin.location.search = '?combine=' + encodeURIComponent(combineQuery);
                }} catch (err) {{
                    console.error('location 변경 실패:', err);
                }}
                return;
            }}
        }}
    }}

    clearBtn.addEventListener('click', () => {{
        workspace.innerHTML = '';
        placedElements = [];
        sessionStorage.removeItem('alchemy_workspace');
        hintText.style.display = 'block';
    }});
</script>
"""

components.html(html_code, height=600)
