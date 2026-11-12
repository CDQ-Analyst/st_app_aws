import pandas as pd
import streamlit as st
st.write("CMDQ Team")
st.set_page_config(page_title="Simple Sales Analysis", layout="wide")

REQUIRED_COLUMNS = ["date", "region", "product", "units", "unit_price", "revenue"]


@st.cache_data
def load_excel(file) -> pd.DataFrame:
    """Read the uploaded Excel file into a DataFrame."""
    df = pd.read_excel(file)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


st.title("Simple Sales Analysis")
st.write("A small Streamlit app for practising deployment on AWS.")

# --- File upload ---
uploaded = st.file_uploader("Upload your sales Excel file (.xlsx)", type=["xlsx"])

if uploaded is None:
    st.info("Upload sales_data.xlsx to see the analysis.")
    st.stop()

df = load_excel(uploaded)

missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing:
    st.error(f"The file is missing these columns: {', '.join(missing)}")
    st.stop()

df["date"] = pd.to_datetime(df["date"])

# --- Sidebar filters ---
st.sidebar.header("Filters")
regions = st.sidebar.multiselect(
    "Region", sorted(df["region"].unique()), default=sorted(df["region"].unique())
)
products = st.sidebar.multiselect(
    "Product", sorted(df["product"].unique()), default=sorted(df["product"].unique())
)

filtered = df[df["region"].isin(regions) & df["product"].isin(products)]

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

# --- Key numbers ---
col1, col2, col3 = st.columns(3)
col1.metric("Total revenue", f"${filtered['revenue'].sum():,.0f}")
col2.metric("Units sold", f"{filtered['units'].sum():,}")
col3.metric("Orders", f"{len(filtered):,}")

# --- Charts ---
left, right = st.columns(2)

with left:
    st.subheader("Revenue by month")
    monthly = filtered.set_index("date")["revenue"].resample("MS").sum()
    monthly.index = monthly.index.strftime("%Y-%m")
    st.line_chart(monthly)

with right:
    st.subheader("Revenue by product")
    st.bar_chart(filtered.groupby("product")["revenue"].sum())

# --- Tables ---
st.subheader("Revenue by region and product")
pivot = filtered.pivot_table(
    index="region", columns="product", values="revenue", aggfunc="sum", fill_value=0
)
st.dataframe(pivot)

with st.expander("Show raw data"):
    st.dataframe(filtered)
    st.download_button(
        "Download as CSV",
        filtered.to_csv(index=False),
        file_name="sales_filtered.csv",
        mime="text/csv",
    )
