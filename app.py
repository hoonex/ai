import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import os
import textwrap # 들여쓰기 깨짐 방지용 모듈 추가

# 1. API 키 설정 (Streamlit Secrets에서 가져옴)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 현재 정상 작동하는 가장 빠르고 안정적인 모델
model = genai.GenerativeModel('gemini-2.5-flash') 

# 2. IPYNB 파일에서 코드(문법)만 추출하는 함수
def extract_code_from_ipynb(folder_path):
    extracted_codes = ""
    if not os.path.exists(folder_path):
        return extracted_codes
        
    for filename in os.listdir(folder_path):
        if filename.endswith(".ipynb"):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
                extracted_codes += f"\n### [학교 수업 자료: {filename}] ###\n"
                for cell in notebook.get("cells", []):
                    if cell.get("cell_type") == "code":
                        source_code = "".join(cell.get("source", []))
                        extracted_codes += source_code + "\n"
    return extracted_codes

# 3. Streamlit 화면 구성
st.set_page_config(page_title="AI 수행평가 치트키", layout="wide")
st.title("🤫 인공지능기초 수행평가 자동완성기")
st.markdown("학교에서 배운 코드 스타일만 100% 반영하여, 주어진 단계별 양식에 맞춰 코드를 생성합니다.")

# 사이드바: AI가 학습할 학교 코드 확인
with st.sidebar:
    st.header("📚 현재 AI가 학습한 학교 코드")
    reference_code = extract_code_from_ipynb("reference_notebooks")
    if reference_code:
        st.success("참고용 ipynb 파일 분석 완료!")
        with st.expander("학습된 문법 전체 보기"):
            st.code(reference_code, language='python')
    else:
        st.error("reference_notebooks 폴더에 ipynb 파일을 넣어주세요.")

# 메인 화면: 데이터 업로드 및 문제(템플릿) 입력
col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("수행평가용 데이터 파일 업로드 (CSV)", type=['csv'])

with col2:
    st.markdown("**수행평가 문제 양식 입력 (예: # [단계1] 데이터 불러오기)**")
    task_template = st.text_area("여기에 수행평가 빈칸 양식(.ipynb의 마크다운 텍스트)을 그대로 복붙하세요.", height=200)

if st.button("🚀 맞춤형 코드 생성 시작", type="primary", use_container_width=True):
    if not uploaded_file or not task_template:
        st.warning("데이터 파일과 문제 양식을 모두 입력해야 합니다!")
    else:
        with st.spinner("학교 문법을 분석하여 템플릿에 맞게 코드를 작성 중입니다..."):
            
            # 데이터 구조 파악 (에러가 나던 to_markdown()을 to_string()으로 변경)
            df = pd.read_csv(uploaded_file)
            data_info = f"- 데이터 컬럼명: {list(df.columns)}\n- 샘플 데이터 (상위 3줄):\n{df.head(3).to_string()}"
            
            # 4. 핵심 시스템 프롬프트 (textwrap.dedent를 써서 프롬프트 자체의 여백 찌꺼기 제거)
            system_prompt = textwrap.dedent(f"""
            너는 대한민국 고등학생의 '인공지능기초' 과목 수행평가를 도와주는 AI야. 
            학생이 제출할 코드를 작성해야 하므로 아래 [규칙]을 무조건 지켜야 해.
            
            [규칙]
            1. (제한된 문법 사용) 아래 [학교 수업 코드]에 등장하는 라이브러리(모듈), 함수, 파이썬 문법만 엄격하게 사용해. 학교 수업에 없는 고급 문법(List comprehension, lambda, 복잡한 사용자 정의 함수 등)을 사용하면 부정행위로 간주되므로 절대 금지야.
            2. (템플릿 완벽 준수) 학생이 제공한 [수행평가 템플릿]의 마크다운 헤더(예: `# **[단계1]...**`)를 100% 똑같이 그대로 출력해. 
            3. 각 단계 헤더 바로 아래에, 해당 단계에 맞는 파이썬 코드 블록(```python ... ```)을 작성해서 채워 넣어.
            4. (들여쓰기 절대 엄수) 생성하는 모든 파이썬 코드는 반드시 '스페이스바 4칸(4 spaces)'을 기준으로 들여쓰기를 맞춰야 해. 탭(Tab) 문자를 섞어 쓰지 마.
            5. (코드 블록 형태) 코드 블록(```python)의 앞쪽이나 뒤쪽에 절대 불필요한 공백을 띄우지 마. 복사-붙여넣기 할 때 들여쓰기 오류(IndentationError)가 나면 안 돼.
            6. 텍스트 설명은 주석으로만 달고, 주피터 노트북 셀에 그대로 '복사-붙여넣기' 할 수 있게 깔끔하게 작성해.
            
            [학교 수업 코드 (이 문법 안에서만 해결할 것)]
            {reference_code}
            
            [업로드된 데이터 정보]
            {data_info}
            
            [수행평가 템플릿 (이 양식을 그대로 살려서 답변할 것)]
            {task_template}
            """)
            
            # Gemini API 호출
            try:
                response = model.generate_content(system_prompt)
                
                # 결과 출력
                st.markdown("---")
                st.markdown("### ✨ 완성된 수행평가 코드")
                st.info("💡 코드 블록 우측 상단의 '복사 아이콘(📋)'을 눌러서 주피터/코랩 코드 셀에 복사하세요.")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"코드 생성 중 오류가 발생했습니다: {e}")
