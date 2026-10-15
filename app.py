import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="Laporan Penjualan Sandal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Styling CSS 
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 16px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Judul Utama
st.title("Laporan Penjualan Sandal")
st.caption("Dashboard monitoring data penjualan sandal berdasarkan periode, produk, dan wilayah")

# 3. Load & Preprocessing Data
@st.cache_data
def load_and_clean_data():
    df = pd.read_csv("penjualan_sandal.csv")
    
    # Parsing Tanggal (Format DD/MM/YYYY)
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], format="%d/%m/%Y", errors="coerce")
    
    # Standarisasi Penulisan Teks
    df["Kota"] = df["Kota"].astype(str).str.strip().str.title()
    df["Kota"] = df["Kota"].replace({"Surakarta": "Solo"})
    
    df["Channel_Penjualan"] = df["Channel_Penjualan"].astype(str).str.strip().str.title()
    df["Metode_Pembayaran"] = df["Metode_Pembayaran"].astype(str).str.strip().str.upper()
    df["Metode_Pembayaran"] = df["Metode_Pembayaran"].replace({"TRANSFER": "Transfer", "E-WALLET": "E-Wallet"})
    
    df["Gender"] = df["Gender"].astype(str).str.strip().str.title()
    df["Gender"] = df["Gender"].replace({"Wanita": "Perempuan", "Laki-Laki": "Pria"})
    
    return df

try:
    df = load_and_clean_data()
except Exception as e:
    st.error(f"Gagal membaca data: {e}. Pastikan file 'penjualan_sandal.csv' ada di folder yang sama.")
    st.stop()


# 4. SIDEBAR FILTER
st.sidebar.header("Filter Laporan")

# Filter Status
status_list = df["Status"].unique().tolist()
selected_status = st.sidebar.multiselect("Status Pesanan", status_list, default=["Selesai"])

# Filter Tanggal
min_date = df["Tanggal"].min().date()
max_date = df["Tanggal"].max().date()
date_range = st.sidebar.date_input("Rentang Tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date)

# Filter Dimensi
selected_categories = st.sidebar.multiselect("Kategori", sorted(df["Kategori"].unique()), default=sorted(df["Kategori"].unique()))
selected_channels = st.sidebar.multiselect("Channel Penjualan", sorted(df["Channel_Penjualan"].unique()), default=sorted(df["Channel_Penjualan"].unique()))
selected_cities = st.sidebar.multiselect("Kota", sorted(df["Kota"].unique()), default=sorted(df["Kota"].unique()))

# Validasi Tanggal
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# Terapkan Filter
filtered = df[
    (df["Status"].isin(selected_status)) &
    (df["Tanggal"].dt.date >= start_date) &
    (df["Tanggal"].dt.date <= end_date) &
    (df["Kategori"].isin(selected_categories)) &
    (df["Channel_Penjualan"].isin(selected_channels)) &
    (df["Kota"].isin(selected_cities))
].copy()

if filtered.empty:
    st.warning("Tidak ada transaksi yang sesuai dengan filter yang dipilih.")
    st.stop()

# 5. (KPI)
total_revenue = filtered["Total_Penjualan"].sum()
total_pairs = filtered["Jumlah"].sum()
total_orders = filtered["ID_Transaksi"].nunique()
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Penjualan", f"Rp {total_revenue:,.0f}")
kpi2.metric("Produk Terjual", f"{total_pairs:,} pcs")
kpi3.metric("Jumlah Transaksi", f"{total_orders:,}")
kpi4.metric("Rata-rata Transaksi", f"Rp {avg_order_value:,.0f}")

st.write("")


# 6. TAB VISUALISASI DATA
tab1, tab2, tab3 = st.tabs([
    "Tren & Saluran Penjualan", 
    "Produk & Ukuran", 
    "Kota & Pembayaran"
])

# TAB 1: TREN & CHANNEL 
with tab1:
    col_t1, col_t2 = st.columns([1.6, 1])
    with col_t1:
        trend_data = (
            filtered.assign(Bulan=filtered["Tanggal"].dt.to_period("M").astype(str))
            .groupby("Bulan", as_index=False)["Total_Penjualan"]
            .sum()
        )
        fig_trend = px.line(
            trend_data,
            x="Bulan",
            y="Total_Penjualan",
            markers=True,
            title="Tren Penjualan Bulanan",
            labels={"Total_Penjualan": "Penjualan (Rp)", "Bulan": "Bulan"}
        )
        fig_trend.update_layout(template="plotly_white")
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_t2:
        channel_data = (
            filtered.groupby("Channel_Penjualan", as_index=False)["Total_Penjualan"]
            .sum()
            .sort_values("Total_Penjualan", ascending=False)
        )
        fig_channel = px.pie(
            channel_data,
            names="Channel_Penjualan",
            values="Total_Penjualan",
            title="Penjualan per Channel",
            hole=0.45
        )
        fig_channel.update_layout(template="plotly_white")
        st.plotly_chart(fig_channel, use_container_width=True)

# TAB 2: PRODUK & UKURAN 
with tab2:
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        top_sandal = (
            filtered.groupby("Nama_Produk", as_index=False)["Total_Penjualan"]
            .sum()
            .sort_values("Total_Penjualan", ascending=True)
        )
        fig_prod = px.bar(
            top_sandal,
            x="Total_Penjualan",
            y="Nama_Produk",
            orientation="h",
            title="Penjualan Berdasarkan Produk",
            text_auto=".2s"
        )
        fig_prod.update_layout(template="plotly_white")
        st.plotly_chart(fig_prod, use_container_width=True)

    with col_p2:
        size_data = (
            filtered.dropna(subset=["Ukuran"])
            .groupby("Ukuran", as_index=False)["Jumlah"]
            .sum()
            .sort_values("Ukuran")
        )
        size_data["Ukuran_Str"] = size_data["Ukuran"].astype(int).astype(str)
        fig_size = px.bar(
            size_data,
            x="Ukuran_Str",
            y="Jumlah",
            title="Penjualan per Ukuran Sandal",
            labels={"Ukuran_Str": "Ukuran", "Jumlah": "Jumlah Terjual (pcs)"}
        )
        fig_size.update_layout(template="plotly_white")
        st.plotly_chart(fig_size, use_container_width=True)

# TAB 3: KOTA & METODE PEMBAYARAN
with tab3:
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        city_sales = (
            filtered.groupby("Kota", as_index=False)["Total_Penjualan"]
            .sum()
            .sort_values("Total_Penjualan", ascending=False)
        )
        fig_city = px.bar(
            city_sales,
            x="Kota",
            y="Total_Penjualan",
            title="Penjualan Berdasarkan Kota",
            text_auto=".2s"
        )
        fig_city.update_layout(template="plotly_white")
        st.plotly_chart(fig_city, use_container_width=True)

    with col_g2:
        pay_data = (
            filtered.groupby("Metode_Pembayaran", as_index=False)["ID_Transaksi"]
            .count()
            .rename(columns={"ID_Transaksi": "Jumlah_Transaksi"})
            .sort_values("Jumlah_Transaksi", ascending=False)
        )
        fig_pay = px.pie(
            pay_data,
            names="Metode_Pembayaran",
            values="Jumlah_Transaksi",
            title="Metode Pembayaran"
        )
        fig_pay.update_layout(template="plotly_white")
        st.plotly_chart(fig_pay, use_container_width=True)


# 7. TABEL DETAIL & DOWNLOAD
st.markdown("---")
with st.expander("Tabel Transaksi Lengkap"):
    st.dataframe(
        filtered.sort_values("Tanggal", ascending=False),
        use_container_width=True,
        hide_index=True
    )
    
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Data Terfilter (CSV)",
        data=csv_bytes,
        file_name="laporan_penjualan_sandal.csv",
        mime="text/csv"
    )