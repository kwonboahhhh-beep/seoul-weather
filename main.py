import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib as mpl
import urllib.request

# ── 한글 폰트 설정 (그래프에 한글이 깨지지 않도록) ────────────────
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
FONT_PATH = "/tmp/NanumGothic-Regular.ttf"
try:
    urllib.request.urlretrieve(FONT_URL, FONT_PATH)
    fm.fontManager.addfont(FONT_PATH)
    mpl.rc('font', family=fm.FontProperties(fname=FONT_PATH).get_name())
except Exception:
    pass
mpl.rcParams['axes.unicode_minus'] = False

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

st.set_page_config(page_title="서울 100년 기온 변화", page_icon="🌡️", layout="wide")

st.title("🌡️ 서울, 100년의 기온 변화")
st.caption("서울 기상 관측 데이터를 바탕으로 연평균 기온이 어떻게 변해왔는지 살펴봅니다.")


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연도"] = df["날짜"].dt.year
    return df


df = load_data()

# 연평균 기온 계산 (자료가 부족한 첫 해·마지막 해는 표시만 하고 그대로 둠)
yearly = (
    df.groupby("연도")[["평균기온", "최저기온", "최고기온"]]
    .mean()
    .reset_index()
)

first_year = int(yearly["연도"].min())
last_year = int(yearly["연도"].max())

st.markdown(f"**관측 기간:** {first_year}년 ~ {last_year}년 (총 {last_year - first_year + 1}년)")

# ── 연도 범위 선택 ─────────────────────────────────────────
year_range = st.slider(
    "살펴볼 연도 범위를 선택하세요",
    min_value=first_year,
    max_value=last_year,
    value=(first_year, last_year),
)

filtered = yearly[(yearly["연도"] >= year_range[0]) & (yearly["연도"] <= year_range[1])]

# ── 핵심 지표 ─────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
start_temp = filtered["평균기온"].iloc[0]
end_temp = filtered["평균기온"].iloc[-1]
diff = end_temp - start_temp

col1.metric(f"{int(filtered['연도'].iloc[0])}년 연평균 기온", f"{start_temp:.1f} ℃")
col2.metric(f"{int(filtered['연도'].iloc[-1])}년 연평균 기온", f"{end_temp:.1f} ℃", f"{diff:+.1f} ℃")
col3.metric("연평균 기온 최고치", f"{filtered['평균기온'].max():.1f} ℃",
            f"{int(filtered.loc[filtered['평균기온'].idxmax(), '연도'])}년")

st.markdown("---")

# ── 메인 그래프: 연평균 기온 추이 + 추세선 ───────────────────
st.subheader("📈 연평균 기온 추이")

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(filtered["연도"], filtered["평균기온"], color="#EF6C00", linewidth=1.6, label="연평균 기온")

# 5년 이동평균으로 큰 흐름을 함께 보여줌
if len(filtered) >= 5:
    rolling = filtered["평균기온"].rolling(window=5, center=True).mean()
    ax.plot(filtered["연도"], rolling, color="#1565C0", linewidth=2.5, label="5년 이동평균")

# 선형 추세선
if len(filtered) >= 2:
    import numpy as np
    z = np.polyfit(filtered["연도"], filtered["평균기온"], 1)
    trend = np.poly1d(z)
    ax.plot(filtered["연도"], trend(filtered["연도"]), color="#757575",
             linestyle="--", linewidth=1.5, label=f"추세선 (연 {z[0]:+.3f}℃)")

ax.set_xlabel("연도")
ax.set_ylabel("연평균 기온 (℃)")
ax.legend(loc="upper left")
ax.grid(alpha=0.3)
st.pyplot(fig)

# ── 최고·최저 기온도 함께 보기 ────────────────────────────
st.subheader("🔺🔻 연평균 최고·최저 기온")
fig2, ax2 = plt.subplots(figsize=(12, 5))
ax2.plot(filtered["연도"], filtered["최고기온"], color="#D32F2F", linewidth=1.5, label="연평균 최고기온")
ax2.plot(filtered["연도"], filtered["최저기온"], color="#1976D2", linewidth=1.5, label="연평균 최저기온")
ax2.set_xlabel("연도")
ax2.set_ylabel("기온 (℃)")
ax2.legend(loc="upper left")
ax2.grid(alpha=0.3)
st.pyplot(fig2)

# ── 원본 데이터 보기 ──────────────────────────────────────
with st.expander("📄 연도별 데이터 표 보기"):
    st.dataframe(
        filtered.rename(columns={"평균기온": "연평균 기온(℃)", "최저기온": "연평균 최저기온(℃)", "최고기온": "연평균 최고기온(℃)"}),
        use_container_width=True,
        hide_index=True,
    )

st.caption("데이터 출처: 서울 기상 관측소(지점 108) 일별 기온 자료")
