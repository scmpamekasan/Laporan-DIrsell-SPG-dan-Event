import pandas as pd
import streamlit as st

from app_config import apply_custom_styling, setup_page_config
from data_store import init_session_state, load_master_harga
from date_utils import get_current_week_label


setup_page_config()
apply_custom_styling()
init_session_state()


def format_currency(value):
    try:
        return f"Rp {int(value):,}"
    except (TypeError, ValueError):
        return "Rp 0"


st.title("Administrasi Stok & Penjualan Rokok")
st.caption("Laporan Penjualan dan Stock Rokok")

master_harga = load_master_harga()
merk_list = [item.get("merk", "") for item in master_harga if item.get("merk")]

with st.sidebar:
    st.subheader("Filter & Input")
    tanggal = st.date_input("Tanggal", value=pd.Timestamp.today().to_pydatetime())
    st.write(get_current_week_label(tanggal))

    promotor = st.text_input("Team / Promotor", placeholder="Masukkan nama")
    selected_merk = st.selectbox("Merk Rokok", merk_list or ["Tidak ada data"])

    if selected_merk != "Tidak ada data":
        current_data = next((item for item in master_harga if item.get("merk") == selected_merk), {})
        st.markdown(f"**Harga Kanvas:** {format_currency(current_data.get('harga_kanvas', 0))}")
        st.markdown(f"**Ball:** {current_data.get('ball', 0)}")
        st.markdown(f"**Slop:** {current_data.get('slop', 0)}")
        st.markdown(f"**Bungkus:** {current_data.get('bungkus', 0)}")

if not merk_list:
    st.warning("Master harga belum tersedia. Pastikan file `master_harga_rokok.json` ada di folder aplikasi.")
    st.stop()

with st.form("form_transaksi"):
    col1, col2, col3 = st.columns(3)

    with col1:
        stok_awal = st.number_input("Stok Awal", min_value=0, step=1, value=0)
        bon_qty = st.number_input("Bon Qty", min_value=0, step=1, value=0)
        harga_kanvas = st.number_input("Harga Kanvas", min_value=0, step=100, value=0)

    with col2:
        stok_akhir = st.number_input("Stok Akhir", min_value=0, step=1, value=0)
        keperluan_bon = st.number_input("Keperluan Bon", min_value=0, step=1, value=0)
        harga_konsumen = st.number_input("Harga Konsumen", min_value=0, step=100, value=0)

    with col3:
        belum_selesai = st.number_input("Belum Selesai", min_value=0, step=1, value=0)
        terjual = st.number_input("Terjual", min_value=0, step=1, value=0)
        total_setoran_kanvas = st.number_input("Total Setoran Kanvas", min_value=0, step=100, value=0)

    submitted = st.form_submit_button("Simpan Transaksi")

    if submitted:
        row = {
            "ID": len(st.session_state.df_transaksi) + 1,
            "Tanggal": str(tanggal),
            "Minggu": get_current_week_label(tanggal),
            "Team/Promotor": promotor,
            "Merk Rokok": selected_merk,
            "Stok Awal": stok_awal,
            "Stok Akhir": stok_akhir,
            "Belum Selesai": belum_selesai,
            "Bon Qty": bon_qty,
            "Keperluan Bon": keperluan_bon,
            "Terjual": terjual,
            "Harga Kanvas": harga_kanvas,
            "Harga Konsumen": harga_konsumen,
            "Total Setoran Kanvas": total_setoran_kanvas,
            "Total Setoran Konsumen": harga_konsumen * terjual,
        }

        st.session_state.df_transaksi = pd.concat(
            [st.session_state.df_transaksi, pd.DataFrame([row])],
            ignore_index=True,
        )
        st.success("Transaksi berhasil disimpan.")

st.subheader("Ringkasan")
metrics = st.columns(4)
metrics[0].metric("Jumlah Transaksi", len(st.session_state.df_transaksi))
metrics[1].metric("Terjual", int(st.session_state.df_transaksi["Terjual"].sum()) if not st.session_state.df_transaksi.empty else 0)
metrics[2].metric("Bon Qty", int(st.session_state.df_transaksi["Bon Qty"].sum()) if not st.session_state.df_transaksi.empty else 0)
metrics[3].metric("Setoran Kanvas", format_currency(st.session_state.df_transaksi["Total Setoran Kanvas"].sum()) if not st.session_state.df_transaksi.empty else "Rp 0")

st.subheader("Data Transaksi")
st.dataframe(st.session_state.df_transaksi, use_container_width=True)
