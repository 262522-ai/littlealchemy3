import streamlit as st
import streamlit.components.v1 as components
import json
import os

# 1. 앱 설정
st.set_page_config(page_title="드래그 리틀 알케미", page_icon="🧪", layout="wide")
st.title("🧪 드래그 앤 드롭 리틀 알케미")

# 2. 외부 JSON 파일 연동 함수
@st.cache_data
def load_game_data():
    # 파일이 없을 경우 기본 데이터 세팅
    if not os.path.exists("recipes.json"):
        return {"recipes": {}, "images": {}}
    with open("recipes.json", "r", encoding="utf-8") as f:
        return json.load(f)

game_data = load_game_data()
RECIPES = game_data.get("recipes", {})
IMAGES = game_data.get("images", {})

# 3. 세션 상태 초기화 (기본 4대 원소)
if "elements" not in st.session_state:
    st.session_state.elements = ["물", "불", "흙", "공기"]

# 4. 쿼리 매개변수를 이용해 자바스크립트(프론트엔드)에서 조합 성공 신호 받기
query_params = st.query_params
if "combine" in query_params:
    combined_str = query_params["combine"]
    # 정렬하여 매칭 (예: "물,불" 또는 "불,물" 모두 가능하도록 체크)
    parts = sorted(combined_str.split(","))
    key1 = f"{parts[0]},{parts[1]}"
    key2 = f"{parts[1]},{parts[0]}"
    
    result = RECIPES.get(key1) or RECIPES.get(key2)
    
    if result and result not in st.session_state.elements:
        st.session_state.elements.append(result)
        st.toast(f"🎉 새로운 물질 발견: {result}!", icon="✨")
    st.query_params.clear()  # 주소창 초기화하여 무한 루프 방지

# 5. 자바스크립트 및 HTML5 드래그 인터페이스 생성
# 보유 중인 원소 데이터를 자바스크립트 배열로 가공
elements_json = json.dumps([
    {"name": el, "img": IMAGES.get(el, "https://gstatic.com")}
    for el in st.session_state.elements
])

html_code = f"""
<div style="display: flex; gap: 20px; font-family: sans-serif; min-height: 500px;">
    <!-- 왼쪽: 조합 실험실 드롭 존 -->
    <div id="drop-zone" style="flex: 2; border: 3px dashed #bbb; border-radius: 15px; position: relative; background: #f9f9f9; display: flex; align-items: center; justify-content: center;">
        <p id="hint-text" style="color: #888; font-size: 18px; pointer-events: none;">여기에 두 원소를 차례대로 끌어다 놓으세요!</p>
        <div id="workspace" style="position: absolute; width:100%; height:100%; top:0; left:0;"></div>
    </div>

    <!-- 오른쪽: 내가 가진 원소 인벤토리 -->
    <div style="flex: 1; border: 1px solid #ddd; padding: 15px; border-radius: 15px; background: #fff; max-height: 500px; overflow-y: auto;">
        <h3 style="margin-top:0;">🎒 인벤토리</h3>
        <div id="inventory" style="display: flex; flex-wrap: wrap; gap: 12px;"></div>
    </div>
</div>

<script>
    const elements = {elements_json};
    const inventory = document.getElementById('inventory');
    const dropZone = document.getElementById('drop-zone');
    const workspace = document.getElementById('workspace');
    const hintText = document.getElementById('hint-text');

    let draggedElementName = null;
    let placedElements = [];

    // 1. 인벤토리 렌더링
    elements.forEach(el => {{
        const div = document.createElement('div');
        div.style.cssText = 'display:flex; flex-direction:column; align-items:center; width:70px; cursor:grab; border:1px solid #eee; padding:5px; border-radius:8px; background:#fafafa;';
        div.draggable = true;
        
        div.innerHTML = `<img src="${{el.img}}" width="45" height="45" style="object-fit:contain;"><span style="font-size:12px; margin-top:4px; font-weight:bold;">${{el.name}}</span>`;
        
        div.addEventListener('dragstart', () => {{ draggedElementName = el.name; }});
        inventory.appendChild(div);
    }});

    // 2. 드래그 앤 드롭 이벤트 바인딩
    dropZone.addEventListener('dragover', (e) => e.preventDefault());

    dropZone.addEventListener('drop', (e) => {{
        e.preventDefault();
        if (!draggedElementName) return;

        hintText.style.display = 'none';

        // 드롭된 마우스 절대 좌표 계산
        const rect = dropZone.getBoundingClientRect();
        const x = e.clientX - rect.left - 25;
        const y = e.clientY - rect.top - 25;

        // 화면에 원소 이미지 생성
        const targetEl = elements.find(item => item.name === draggedElementName);
        const img = document.createElement('img');
        img.src = targetEl.img;
        img.style.cssText = `position: absolute; left: ${{x}}px; top: ${{y}}px; width: 50px; height: 50px; cursor: pointer; transition: transform 0.2s;`;
        workspace.appendChild(img);

        placedElements.push({{ name: draggedElementName, x: x, y: y, element: img }});

        // 원소가 2개 이상 배치되었을 때 조합 조건 확인 (거리 기반)
        if (placedElements.length >= 2) {{
            const last = placedElements[placedElements.length - 1];
            for (let i = 0; i < placedElements.length - 1; i++) {{
                const prev = placedElements[i];
                const dist = Math.hypot(last.x - prev.x, last.y - prev.y);

                // 두 이미지 거리가 60픽셀 이하로 겹치면 파이썬으로 데이터 전송
                if (dist < 60) {{
                    const combineQuery = prev.name + ',' + last.name;
                    // 스트림릿 웹페이지 부모창 주소에 쿼리를 심어 상태를 새로고침 유도
                    window.parent.location.search = '?combine=' + encodeURIComponent(combineQuery);
                    return;
                }}
            }}
        }}
        draggedElementName = null;
    }});
</script>
"""

# 6. 컴포넌트를 화면에 배치
components.html(html_code, height=550)

# 하단 도감 가이드 추가
st.caption("💡 팁: 인벤토리에서 원소를 드래그하여 왼쪽 빈 캔버스에 떨어뜨리세요. 두 원소 이미지를 가까이 포개면 새로운 원소 조합을 시도합니다.")
