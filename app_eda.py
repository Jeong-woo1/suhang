import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
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

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 인구 데이터 EDA")

        uploaded = st.file_uploader("population_trends.csv 파일 업로드", type="csv")
        if not uploaded:
            st.info("CSV 파일을 업로드해주세요.")
            return

        # 데이터 로드 및 전처리
        df = pd.read_csv(uploaded)

        # '-'를 0으로, 쉼표 제거 후 숫자로 변환
        numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']
        df.replace("-", 0, inplace=True)
        for col in numeric_cols:
            df[col] = df[col].astype(str).str.replace(",", "").str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        tabs = st.tabs([
            "기초 통계",
            "연도별 추이",
            "지역별 분석",
            "변화량 분석",
            "시각화"
        ])

        # 1. 기초 통계
        with tabs[1]:
            st.subheader("📈 National Population Trend (with Projection to 2036)")

            # 전국 데이터 필터링
            national = df[df['지역'] == '전국'].sort_values('연도')

            # 연도, 인구, 출생, 사망
            years = national['연도'].tolist()
            population = national['인구'].tolist()
            births = national['출생아수(명)'].tolist()
            deaths = national['사망자수(명)'].tolist()

            # 최근 3년 평균 자연 증가 계산
            recent = national.tail(3)
            avg_natural_increase = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()

            # 예측값 생성: 2024 ~ 2036 (2년 간격)
            last_year = years[-1]
            last_pop = population[-1]

            future_years = list(range(last_year + 2, 2037, 2))  # 2024부터 시작
            future_pops = []

            # 첫 예측값 (2024)을 별도로 계산하여 연결용으로 사용
            pop_2024 = last_pop + avg_natural_increase * 2
            current_pop = pop_2024

            for year in future_years:
                current_pop += avg_natural_increase * 2
                future_pops.append(current_pop)

            fig, ax = plt.subplots()

            # 실제 관측값: 실선
            ax.plot(years, population, marker='o', label='Observed', color='blue')

            # 2022-2024 연결: 점선
            ax.plot([last_year, 2024], [last_pop, pop_2024], linestyle='--', color='red')

            # 이후 예측값 (2024 제외): 점선
            future_plot_years = [2024] + future_years
            future_plot_pops = [pop_2024] + future_pops
            ax.plot(future_plot_years, future_plot_pops, marker='o', linestyle='--', color='red', label='Predicted')

            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.set_title("National Population Trend")
            ax.legend()
            st.pyplot(fig)






        # 2. 연도별 추이
        with tabs[1]:
            st.subheader("📈 연도별 전국 인구 추이")
            national = df[df['지역'] == '전국'].sort_values('연도')

            fig, ax = plt.subplots()
            ax.plot(national['연도'], national['인구'], marker='o', label='Observed')
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.set_title("National Population Trend")

            # 2035년 예측
            recent = national.tail(3)
            avg_delta = (recent['인구'].iloc[-1] - recent['인구'].iloc[0]) / 2
            pred_2035 = national['인구'].iloc[-1] + avg_delta * (2035 - national['연도'].iloc[-1])
            ax.axhline(pred_2035, color='red', linestyle='--', label=f'Predicted 2035: {int(pred_2035):,}')
            ax.legend()
            st.pyplot(fig)

        # 3. 지역별 분석
        with tabs[2]:
            st.subheader("🏙️ 최근 5년간 지역별 인구 변화량")
            latest_year = df['연도'].max()
            past_year = latest_year - 5
            df_latest = df[df['연도'] == latest_year]
            df_past = df[df['연도'] == past_year]

            merged = pd.merge(df_latest, df_past, on='지역', suffixes=('_최근', '_과거'))
            merged['변화량'] = merged['인구_최근'] - merged['인구_과거']
            merged = merged[merged['지역'] != '전국'].sort_values('변화량', ascending=False)

            fig, ax = plt.subplots(figsize=(8, 6))
            sns.barplot(x='변화량', y='지역', data=merged, ax=ax)
            ax.set_xlabel("Change")
            ax.set_ylabel("Region")
            st.pyplot(fig)

            # 변화율 추가
            merged['변화율(%)'] = (merged['변화량'] / merged['인구_과거']) * 100
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            sns.barplot(x='변화율(%)', y='지역', data=merged, ax=ax2)
            ax2.set_xlabel("Rate (%)")
            ax2.set_ylabel("Region")
            st.pyplot(fig2)

        # 4. 변화량 분석
        with tabs[3]:
            st.subheader("📊 연도별 인구 증감률 상위 지역")
            df['증감'] = df.groupby('지역')['인구'].diff()
            diff_df = df[df['지역'] != '전국'].dropna().sort_values('증감', ascending=False).head(100)

            styled = diff_df.style.background_gradient(
                cmap='coolwarm', subset=['증감']
            ).format({
                '증감': '{:,.0f}',
                '인구': '{:,.0f}'
            })
            st.dataframe(styled)

        # 5. 시각화
        with tabs[4]:
            st.subheader("📊 지역별 연도별 인구 누적영역그래프")
            pivot_df = df.pivot(index='연도', columns='지역', values='인구')
            pivot_df = pivot_df.drop(columns='전국', errors='ignore')

            fig, ax = plt.subplots(figsize=(10, 6))
            pivot_df.plot.area(ax=ax)
            ax.set_title("Population Area Chart")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()