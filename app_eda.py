import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import platform

# --------------------
# 한글 폰트 설정 (matplotlib)
# --------------------
# OS별로 다른 폰트 경로 설정
def get_korean_font():
    if platform.system() == 'Windows':
        return 'Malgun Gothic'
    elif platform.system() == 'Darwin': # macOS
        return 'AppleGothic'
    else: # Linux (Google Colab, Streamlit Cloud 등)
        # 나눔 폰트를 미리 설치해야 합니다.
        # Streamlit Cloud 배포 시 packages.txt에 'fonts-nanum*' 추가 필요
        return 'NanumGothic'

plt.rc('font', family=get_korean_font())
plt.rcParams['axes.unicode_minus'] = False # 마이너스 폰트 깨짐 방지


# --------------------
# Firebase 설정
# --------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# --------------------
# 세션 상태 초기화
# --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_name = ""

# --------------------
# 페이지 클래스 및 함수
# --------------------

class EDA:
    """탐색적 데이터 분석 페이지를 위한 클래스"""
    def run(self):
        st.title("📊 탐색적 데이터 분석 (EDA)")
        st.write("---")

        # 두 개의 분석을 위한 탭 생성
        tab_bike, tab_population = st.tabs(["🚲 자전거 수요 예측 분석", "👨‍👩‍👧‍👦 지역별 인구 분석"])

        # =====================================================================
        # 자전거 수요 예측 분석 탭
        # =====================================================================
        with tab_bike:
            st.header("📁 파일 업로드")
            uploaded_file = st.file_uploader("분석할 CSV 파일을 업로드하세요 (예: bike.csv).", type=['csv'], key="bike_uploader")

            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.success("파일이 성공적으로 업로드되었습니다.")

                    st.subheader("데이터 미리보기")
                    st.dataframe(df.head())

                    st.subheader("데이터 기본 정보")
                    buffer = io.StringIO()
                    df.info(buf=buffer)
                    s = buffer.getvalue()
                    st.text(s)

                    st.subheader("결측치 확인")
                    st.dataframe(df.isnull().sum().to_frame('결측치 개수'))

                    st.subheader("기술 통계량")
                    st.dataframe(df.describe())

                    st.header("📈 데이터 시각화")

                    st.subheader("시간에 따른 자전거 대여량")
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df['year'] = df['datetime'].dt.year
                    df['month'] = df['datetime'].dt.month
                    df['day'] = df['datetime'].dt.day
                    df['hour'] = df['datetime'].dt.hour
                    
                    hourly_counts = df.groupby('hour')['count'].mean()
                    fig, ax = plt.subplots(figsize=(10, 6))
                    hourly_counts.plot(kind='bar', ax=ax, color='skyblue')
                    ax.set_title('시간대별 평균 자전거 대여량')
                    ax.set_xlabel('시간')
                    ax.set_ylabel('평균 대여량')
                    ax.tick_params(axis='x', rotation=0)
                    st.pyplot(fig)

                    st.subheader("이상치(Outlier) 탐지: Box Plot")
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.boxplot(data=df, y='count', ax=ax)
                    ax.set_title('자전거 대여량(count)의 Box Plot')
                    ax.set_ylabel('대여량')
                    st.pyplot(fig)

                    st.subheader("데이터 분포 변환: 로그 변환")
                    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
                    sns.histplot(df['count'], kde=True, ax=axes[0])
                    axes[0].set_title("Original Count Distribution")
                    axes[0].set_xlabel("Count")
                    axes[0].set_ylabel("Frequency")

                    df['log_count'] = np.log1p(df['count'])
                    sns.histplot(df['log_count'], kde=True, ax=axes[1])
                    axes[1].set_title("Log(Count + 1) Distribution")
                    axes[1].set_xlabel("Log(Count + 1)")
                    axes[1].set_ylabel("Frequency")

                    st.pyplot(fig)

                    st.markdown("""
                        > **그래프 해석:** > - 왼쪽: 원본 분포는 한쪽으로 긴 꼬리를 가진 왜곡된 형태입니다.  
                        > - 오른쪽: 로그 변환 후 분포는 훨씬 균형잡힌 형태로, 중앙값 부근에 데이터가 집중됩니다.  
                        > - 극단치의 영향이 완화되어 이후 분석·모델링 안정성이 높아집니다.
                        """)
                except Exception as e:
                    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

        # =====================================================================
        # 지역별 인구 분석 탭 (과제 수행 부분)
        # =====================================================================
        with tab_population:
            st.header("📁 population_trends.csv 파일 업로드")
            uploaded_pop_file = st.file_uploader("population_trends.csv 파일을 업로드하세요.", type=['csv'], key="population_uploader")

            if uploaded_pop_file is not None:
                try:
                    df_pop = pd.read_csv(uploaded_pop_file)
                    st.success("인구 데이터 파일이 성공적으로 업로드되었습니다.")
                    
                    # --- 데이터 전처리 (과제 요구사항) ---
                    st.write("#### ✨ 데이터 전처리")
                    with st.expander("전처리 과정 보기"):
                        st.write("1. 컬럼명을 영문으로 변경합니다: '연도'->'Year', '지역'->'Region', '총인구수'->'Population'")
                        df_pop.rename(columns={'연도': 'Year', '지역': 'Region', '총인구수': 'Population'}, inplace=True)
                        
                        st.write("2. '세종' 지역의 결측치를 이전 연도의 값으로 채웁니다. (Forward Fill)")
                        df_pop.sort_values(by=['Region', 'Year'], inplace=True)
                        df_pop['Population'] = df_pop.groupby('Region')['Population'].transform(lambda x: x.ffill())
                        
                        st.write("3. 전처리 후 남은 결측치가 있는 행을 제거하고, 인구수 데이터를 정수형으로 변환합니다.")
                        df_pop.dropna(inplace=True)
                        df_pop['Population'] = df_pop['Population'].astype(int)
                        st.write("전처리가 완료되었습니다.")

                    # --- 분석 탭 구성 (과제 요구사항) ---
                    stat_tab, yearly_tab, regional_tab, change_tab, viz_tab = st.tabs([
                        "기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"
                    ])

                    with stat_tab:
                        st.subheader("기초 통계 분석")
                        st.write("##### 📊 데이터 샘플")
                        st.dataframe(df_pop.head())

                        st.write("##### 🔢 기술 통계")
                        st.dataframe(df_pop.describe())

                        st.write("##### ❓ 결측치 확인")
                        st.dataframe(df_pop.isnull().sum().to_frame('결측치 개수'))

                        st.write("##### ⛓️ 중복 데이터 확인")
                        st.write(f"중복된 행의 개수: {df_pop.duplicated().sum()} 개")

                    with yearly_tab:
                        st.subheader("연도별 전체 인구 추이")
                        yearly_total_pop = df_pop.groupby('Year')['Population'].sum()
                        st.line_chart(yearly_total_pop)
                        with st.expander("데이터 테이블 보기"):
                            st.dataframe(yearly_total_pop)

                    with regional_tab:
                        st.subheader("최신 연도 기준 지역별 인구수")
                        latest_year = df_pop['Year'].max()
                        st.write(f"기준 연도: **{latest_year}년**")
                        
                        latest_pop = df_pop[df_pop['Year'] == latest_year].sort_values("Population", ascending=False)
                        
                        fig, ax = plt.subplots(figsize=(12, 8))
                        sns.barplot(data=latest_pop, x='Region', y='Population', ax=ax, palette='viridis')
                        ax.set_title(f'{latest_year}년 지역별 인구수')
                        ax.set_xlabel('지역')
                        ax.set_ylabel('인구수 (명)')
                        plt.xticks(rotation=45, ha='right')
                        plt.tight_layout()
                        st.pyplot(fig)
                        
                        with st.expander("데이터 테이블 보기"):
                            st.dataframe(latest_pop.style.format({'Population': '{:,}'}))

                    with change_tab:
                        st.subheader("인구 변화량 분석")
                        
                        # 1. 이전 연도 대비 증감 계산 (과제 프롬프트 예시 구현)
                        st.write("##### 📈 이전 연도 대비 인구 증감 Top 100")
                        st.info("각 지역의 이전 연도 대비 인구 증감량을 계산하여 상위 100개 사례를 보여줍니다.")
                        df_pop.sort_values(by=['Region', 'Year'], inplace=True)
                        df_pop['증감'] = df_pop.groupby('Region')['Population'].diff()
                        
                        top_100_changes = df_pop.dropna(subset=['증감']).nlargest(100, '증감')
                        st.dataframe(top_100_changes[['Year', 'Region', 'Population', '증감']]
                                     .style.format({'Population': '{:,}', '증감': '{:+,}'})
                                     .background_gradient(cmap='bwr', subset=['증감'], vmin=-top_100_changes['증감'].abs().max(), vmax=top_100_changes['증감'].abs().max())
                                    )

                        # 2. 분석 기간 전체의 인구 변화
                        st.write("##### 📊 분석 기간 전체 인구 변화량")
                        start_year = df_pop['Year'].min()
                        end_year = df_pop['Year'].max()
                        st.info(f"{start_year}년부터 {end_year}년까지의 지역별 전체 인구 변화량을 보여줍니다.")
                        
                        start_pop = df_pop[df_pop['Year'] == start_year].set_index('Region')['Population']
                        end_pop = df_pop[df_pop['Year'] == end_year].set_index('Region')['Population']
                        
                        change_df = pd.DataFrame({
                            f'{start_year}년 인구': start_pop,
                            f'{end_year}년 인구': end_pop,
                            '변화량': end_pop - start_pop
                        }).dropna()
                        change_df['변화량'] = change_df['변화량'].astype(int)
                        
                        st.dataframe(change_df.sort_values('변화량', ascending=False)
                                     .style.format('{:,}').bar(subset=['변화량'], align='zero', color=['#d65f5f', '#5fba7d']))


                    with viz_tab:
                        st.subheader("누적 영역 그래프 시각화")
                        st.info("연도에 따른 지역별 인구수 변화를 누적하여 보여줍니다. '전국' 데이터는 시각화에서 제외되었습니다.")
                        
                        # Pivot table 생성
                        pivot_df = df_pop[df_pop['Region'] != '전국'].pivot_table(
                            index='Year', columns='Region', values='Population', aggfunc='sum'
                        )
                        pivot_df.fillna(0, inplace=True) # 결측치는 0으로 채워서 그래프 오류 방지

                        # Streamlit 내장 차트 사용
                        st.write("##### Streamlit 내장 누적 영역 그래프")
                        st.area_chart(pivot_df)

                        # Seaborn/Matplotlib을 이용한 시각화 (과제 프롬프트 예시 구현)
                        st.write("##### Seaborn 누적 영역 그래프")
                        # 한글 레이블을 영문으로 변경 (선택사항, 프롬프트 예시 기반)
                        region_map = {
                            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                            '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                            '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                            '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju'
                        }
                        pivot_df_en = pivot_df.rename(columns=region_map)
                        
                        fig, ax = plt.subplots(figsize=(15, 10))
                        palette = sns.color_palette("tab20", n_colors=len(pivot_df_en.columns))
                        
                        ax.stackplot(pivot_df_en.index, pivot_df_en.T, labels=pivot_df_en.columns, colors=palette, alpha=0.8)
                        
                        ax.set_title('Population Trends by Region', fontsize=16)
                        ax.set_xlabel('Year')
                        ax.set_ylabel('Population')
                        ax.legend(loc='upper left', title="Regions")
                        plt.tight_layout()
                        st.pyplot(fig)


                except Exception as e:
                    st.error(f"인구 데이터 분석 중 오류가 발생했습니다: {e}")

class Login:
    # ... (기존 Login 클래스 코드 유지)
    def run(self):
        st.set_page_config(page_title="로그인", layout="centered")
        st.title("로그인")
        email = st.text_input("이메일", key="login_email")
        password = st.text_input("비밀번호", type="password", key="login_password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                user_info = firestore.child("users").child(user['localId']).get().val()
                st.session_state.user_name = user_info.get('name', '사용자')
                st.rerun()
            except Exception as e:
                st.error("이메일 또는 비밀번호가 잘못되었습니다.")

class Register:
    # ... (기존 Register 클래스 코드 유지)
    def __init__(self, login_path):
        self.login_path = login_path

    def run(self):
        st.set_page_config(page_title="회원가입", layout="centered")
        st.title("회원가입")
        email = st.text_input("이메일", key="register_email")
        password = st.text_input("비밀번호", type="password", key="register_password")
        confirm_password = st.text_input("비밀번호 확인", type="password", key="register_confirm_password")
        name = st.text_input("이름", key="register_name")
        if st.button("회원가입"):
            if password == confirm_password:
                try:
                    user = auth.create_user_with_email_and_password(email, password)
                    user_data = {"name": name, "email": email}
                    firestore.child("users").child(user['localId']).set(user_data)
                    st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                    time.sleep(1)
                    st.switch_page(self.login_path)
                except Exception as e:
                    st.error(f"회원가입 실패: {e}")
            else:
                st.error("비밀번호가 일치하지 않습니다.")

class FindPassword:
    # ... (기존 FindPassword 클래스 코드 유지)
    def run(self):
        st.set_page_config(page_title="비밀번호 찾기", layout="centered")
        st.title("비밀번호 찾기")
        email = st.text_input("가입한 이메일 주소를 입력하세요.", key="find_pw_email")
        if st.button("비밀번호 재설정 이메일 보내기"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 보냈습니다. 받은 편지함을 확인하세요.")
            except Exception as e:
                st.error(f"오류 발생: {e}")

class Home:
    # ... (기존 Home 클래스 코드 유지)
    def __init__(self, login_page, register_page, find_pw_page):
        self.login_page = login_page
        self.register_page = register_page
        self.find_pw_page = find_pw_page
        
    def run(self):
        st.set_page_config(page_title="홈", layout="wide")
        st.title("Streamlit EDA 앱")
        st.write(f"안녕하세요, {st.session_state.get('user_name', '방문자')}님!")
        st.markdown("---")
        st.write("왼쪽 사이드바에서 메뉴를 선택하여 앱의 다른 기능들을 이용할 수 있습니다.")
        st.info("이 앱은 Streamlit을 사용하여 제작된 EDA(탐색적 데이터 분석) 플랫폼입니다.")

class UserInfo:
    # ... (기존 UserInfo 클래스 코드 유지)
    def run(self):
        st.set_page_config(page_title="내 정보", layout="centered")
        st.title("내 정보")
        st.write(f"이름: {st.session_state.user_name}")
        st.write(f"이메일: {st.session_state.user_email}")

class Logout:
    # ... (기존 Logout 클래스 코드 유지)
    def run(self):
        if st.session_state.logged_in:
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.user_name = ""
        st.success("로그아웃되었습니다.")
        time.sleep(1)
        st.switch_page("home")

# --------------------
# 페이지 객체 생성
# --------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout, title="Logout", icon="🚪", url_path="logout")
Page_EDA      = st.Page(EDA, title="EDA", icon="📈", url_path="eda")

# --------------------
# 네비게이션 설정
# --------------------
if st.session_state.logged_in:
    pages_for_logged_in_user = {
        "메인 페이지": Page_Home,
        "탐색적 데이터 분석": Page_EDA,
        "내 정보": Page_User,
        "로그아웃": Page_Logout
    }
    pg = st.navigation(pages_for_logged_in_user)
else:
    pages_for_guest = {
        "메인 페이지": Page_Home,
        "로그인": Page_Login,
        "회원가입": Page_Register,
        "비밀번호 찾기": Page_FindPW
    }
    pg = st.navigation(pages_for_guest)

# --------------------
# 페이지 실행
# --------------------
pg.run()