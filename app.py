import streamlit as st
import streamlit.components.v1 as components
import json
import os

# 1. 앱 설정
st.set_page_config(page_title="텍스트 리틀 알케미", page_icon="🧪", layout="wide")
st.title("🧪 리틀 알케미 (자유 이동 및 우클릭 놓기)")

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

# 5. 백엔드 합성 로직
query_params = st.query_params
if "combine" in query_params:
    combined_str = query_params["combine"]
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
                원소를 마우스로 조작해 보세요!<br>
                💡 팁: 드래그 중 <b>오른쪽 마우스 클릭</b>을 하면 그 자리에 놓아집니다.
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

    // 3. 작업판 노드 생성 및 마우스 이벤트 바인딩
    function createNode(name, x, y) {{
        const node = document.createElement('div');
        node.className = 'placed-node';
        node.innerText = name;
        node.style.left = x + 'px';
        node.style.top = y + 'px';
        workspace.appendChild(node);

        const obj = {{ name: name, x: x, y: y, dom: node }};
        placedElements.push(obj);

        // 마우스 다운 (드래그 시작)
        node.addEventListener('mousedown', (e) => {{
            if (e.button === 0) {{ // 왼쪽 클릭만 드래그 시작 허용
                activeNode = obj;
                const rect = node.getBoundingClientRect();
                offsetX = e.clientX - rect.left;
                offsetY = e.clientY - rect.top;
                e.stopPropagation();
            }}
        }});
        
        // 브라우저 기본 우클릭 메뉴가 열려 드래그가 꼬이는 것 방지
        node.addEventListener('contextmenu', (e) => {{
            e.preventDefault();
        }});

        checkCollision(obj);
    }}

    // 4. 작업판 내 드래그 이동
    window.addEventListener('mousemove', (e) => {{
        if (!activeNode) return;
        
        const rect = dropZone.getBoundingClientRect();
        let x = e.clientX - rect.left - offsetX;
        let y = e.clientY - rect.top - offsetY;

        // 경계 제한
        x = Math.max(0, Math.min(x, rect.width - activeNode.dom.offsetWidth));
        y = Math.max(0, Math.min(y, rect.height - activeNode.dom.offsetHeight));

        activeNode.x = x;
        activeNode.y = y;
        activeNode.dom.style.left = x + 'px';
        activeNode.dom.style.top = y + 'px';
    }});

    // 5. 드래그 종료 이벤트 처리 (왼쪽 클릭 뗌 OR 오른쪽 클릭 다운)
    function releaseNode() {{
        if (activeNode) {{
            checkCollision(activeNode);
            activeNode = null;
        }}
    }}

    window.addEventListener('mouseup', (e) => {{
        if (e.button === 0) {{ // 왼쪽 마우스 뗌
            releaseNode();
        }}
    }});

    // ★ 기능 구현: 드래그 도중 오른쪽 마우스 클릭 시 강제 고정 및 놓기
    window.addEventListener('mousedown', (e) => {{
        if (e.button === 2 && activeNode) {{ // 오른쪽 마우스 클릭
            e.preventDefault();
            releaseNode();
        }}
    }});
    
    // 작업판 내부 전체 우클릭 메뉴창 열림 방지
    dropZone.addEventListener('contextmenu', (e) => {{
        e.preventDefault();
    }});

    // 6. 어느 정도(60px 이하) 완전히 포개졌을 때만 합성 요청
    function checkCollision(targetObj) {{
        if (placedElements.length < 2) return;

        for (let i = 0; i < placedElements.length; i++) {{
            const other = placedElements[i];
            if (other === targetObj) continue;

            const dist = Math.hypot(targetObj.x - other.x, targetObj.y - other.y);
            
            // 두 텍스트 상자가 확실하게 겹치면(60px 내외) 합성 실행
            if (dist < 60) {{
                const combineQuery = other.name + ',' + targetObj.name;
                window.parent.location.search = '?combine=' + encodeURIComponent(combineQuery);
                return;
            }}
        }}
    }}

    // 7. 작업판 비우기 버튼
    clearBtn.addEventListener('click', () => {{
        workspace.innerHTML = '';
        placedElements = [];
        hintText.style.display = 'block';
    }});
</script>
"""

# 8. 렌더링
components.html(html_code, height=600)
