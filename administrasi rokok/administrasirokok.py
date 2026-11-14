import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
import io

from app_config import setup_page_config, apply_custom_styling
from date_utils import get_current_week_label, format_date_indo
from data_store import load_master_harga, init_session_state

# Konfigurasi Awal
setup_page_config()
apply_custom_styling()
init_session_state()

master_rokok = load_master_harga()
list_merk = [item["merk"] for item in master_rokok]
dict_master_detail = {item["merk"]: item for item in master_rokok}

# Header Utama
st.title("🚬 Sistem Administrasi Stok & Penjualan Rokok")
st.markdown("Pencatatan stok awal, akhir, bon keperluan, rokok gantung/belum selesai, serta setoran harga kanvas vs konsumen.")

# --- SIDEBAR: NAVIGASI & ROLE ---
st.sidebar.image("https://img.icons8.com/color/96/wooden-crate.png", width=70)
st.sidebar.header("Panel Navigasi")
role = st.sidebar.selectbox("Pilih Hak Akses (Role)", ["Admin", "Supervisi", "SPG / Promotor"])

st.sidebar.divider()
selected_date = st.sidebar.date_input("Pilih Tanggal Laporan", datetime.now())
current_week = get_current_week_label(selected_date)
st.sidebar.info(f"📅 Periode: **{current_week}**")

# --- MENU UTAMA (Termasuk Sub-Menu / Tab Penjualan Per Team) ---
tab_stock, tab1, tab2, tab_lap_team, tab3, tab4 = st.tabs([
    "📦 Stock Rokok", 
    "📝 Input Transaksi", 
    "📊 Tabel Rekap & Edit", 
    "👥 Laporan Per Team",
    "📋 Manajemen Bon", 
    "⚙️ Reset & Hapus Data"
])

# ================= TAB 0: STOCK ROKOK (BON MULTI-MERK) =================
with tab_stock:
    st.subheader("📦 Manajemen Stock Rokok & Bon Multi-Merk")
    st.markdown("Input 1 nomor bon untuk sekaligus banyak merk rokok, pantau sisa stock terakhir, serta kalkulasi stock awal hari ini.")

    if "bon_form_reset_id" not in st.session_state:
        st.session_state.bon_form_reset_id = 0

    with st.expander("➕ Input Bon Rokok Baru (Multi-Merk)", expanded=True):
        with st.form(f"form_bon_multimerk_{st.session_state.bon_form_reset_id}", clear_on_submit=True):
            st.markdown("#### Informasi Umum Bon")
            
            c1, c2 = st.columns(2)
            with c1:
                nomor_bon = st.text_input("No Bon", placeholder="Contoh: bon111")
            with c2:
                team_bon = st.text_input("Nama (Promotor / Team)", placeholder="Contoh: Beni")

            c3, c4 = st.columns(2)
            with c3:
                keperluan_bon = st.selectbox("Keperluan Bon Utama", [
                    "Dirsell SPG", 
                    "Event Pameran", 
                    "Pembinaan Kantor", 
                    "Sampling / Promosi", 
                    "Penambahan Stock Gudang", 
                    "Lainnya"
                ])
            with c4:
                keterangan_bon_umum = st.text_input("Keterangan (Opsional)", placeholder="Contoh: Untuk event shamrock")

            st.markdown("---")
            st.markdown("#### Daftar Merk Rokok dalam Bon Ini")
            
            if "jumlah_baris_bon" not in st.session_state:
                st.session_state.jumlah_baris_bon = 10

            item_bon_list = []
            for i in range(st.session_state.jumlah_baris_bon):
                col_m, col_b, col_s, col_bu = st.columns([3, 1, 1, 1])
                with col_m:
                    m_pilih = st.selectbox(f"Merk Rokok #{i+1}", ["-"] + list_merk, key=f"bon_m_{st.session_state.bon_form_reset_id}_{i}")
                with col_b:
                    b_ball = st.number_input(f"Ball #{i+1}", min_value=0, value=0, key=f"bon_b_{st.session_state.bon_form_reset_id}_{i}")
                with col_s:
                    s_slop = st.number_input(f"Slop #{i+1}", min_value=0, value=0, key=f"bon_s_{st.session_state.bon_form_reset_id}_{i}")
                with col_bu:
                    bu_bungkus = st.number_input(f"Bungkus #{i+1}", min_value=0, value=0, key=f"bon_bu_{st.session_state.bon_form_reset_id}_{i}")

                if m_pilih != "-":
                    item_bon_list.append({
                        "merk": m_pilih,
                        "ball": b_ball,
                        "slop": s_slop,
                        "bungkus": bu_bungkus
                    })

            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                tambah_baris_btn = st.form_submit_button("➕ Tambah 5 Baris")
            with col_btn2:
                simpan_semua_bon = st.form_submit_button("💾 Simpan Semua Bon Ini", type="primary")

            if tambah_baris_btn:
                st.session_state.jumlah_baris_bon += 5
                st.rerun()

            if simpan_semua_bon:
                if not nomor_bon:
                    st.error("No Bon wajib diisi!")
                elif not item_bon_list:
                    st.error("Pilih minimal 1 merk rokok!")
                else:
                    sukses_count = 0
                    for item in item_bon_list:
                        merk = item["merk"]
                        b = item["ball"]
                        s = item["slop"]
                        bu = item["bungkus"]
                        
                        master_item = dict_master_detail.get(merk, {"slop": 10})
                        slop_per_ball = master_item.get("slop", 10)
                        bungkus_per_slop = 10
                        total_setara = (b * slop_per_ball * bungkus_per_slop) + (s * bungkus_per_slop) + bu
                        
                        if total_setara > 0:
                            ket_final = keterangan_bon_umum if keterangan_bon_umum else f"Bon No: {nomor_bon}"
                            new_row = {
                                "ID": nomor_bon,
                                "Tanggal": str(selected_date),
                                "Team/Promotor": team_bon if team_bon else "Tanpa Nama",
                                "Merk Rokok": merk,
                                "Ball": b,
                                "Slop": s,
                                "Bungkus": bu,
                                "Total Setara Bungkus": total_setara,
                                "Keperluan": keperluan_bon,
                                "Keterangan": ket_final
                            }
                            st.session_state.df_bon = pd.concat([st.session_state.df_bon, pd.DataFrame([new_row])], ignore_index=True)
                            sukses_count += 1

                    st.session_state.jumlah_baris_bon = 10
                    st.session_state.bon_form_reset_id += 1
                    st.session_state["last_bon_msg"] = f"✅ Berhasil menyimpan {sukses_count} item merk untuk No Bon **{nomor_bon}**!"
                    st.rerun()

    if "last_bon_msg" in st.session_state and st.session_state["last_bon_msg"]:
        st.success(st.session_state.pop("last_bon_msg"))

    st.divider()

    st.markdown("### 📉 Sisa Stock Terakhir & Stock Awal Hari Ini")
    
    df_terakhir = pd.DataFrame()
    if not st.session_state.df_transaksi.empty:
        df_sorted_trx = st.session_state.df_transaksi.sort_values(by="Tanggal", ascending=False)
        df_terakhir = df_sorted_trx.drop_duplicates(subset=["Team/Promotor", "Merk Rokok"], keep="first")
        
    df_bon_hari_ini = pd.DataFrame()
    if not st.session_state.df_bon.empty:
        df_bon_hari_ini = st.session_state.df_bon[st.session_state.df_bon["Tanggal"] == str(selected_date)]

    combined_data = []
    if not df_terakhir.empty:
        for _, row in df_terakhir.iterrows():
            if row["Stok Akhir"] > 0:
                combined_data.append({
                    "Team/Promotor": row["Team/Promotor"],
                    "Merk Rokok": row["Merk Rokok"],
                    "Stok Terakhir": row["Stok Akhir"],
                    "Bon Hari Ini (Bungkus)": 0,
                    "Total Stock Awal": row["Stok Akhir"]
                })

    if not df_bon_hari_ini.empty:
        for _, bon_row in df_bon_hari_ini.iterrows():
            team = bon_row["Team/Promotor"]
            merk = bon_row["Merk Rokok"]
            qty_bon = bon_row["Total Setara Bungkus"]
            
            found = False
            for item in combined_data:
                if item["Team/Promotor"] == team and item["Merk Rokok"] == merk:
                    item["Bon Hari Ini (Bungkus)"] += qty_bon
                    item["Total Stock Awal"] = item["Stok Terakhir"] + item["Bon Hari Ini (Bungkus)"]
                    found = True
                    break
            if not found:
                if qty_bon > 0:
                    combined_data.append({
                        "Team/Promotor": team,
                        "Merk Rokok": merk,
                        "Stok Terakhir": 0,
                        "Bon Hari Ini (Bungkus)": qty_bon,
                        "Total Stock Awal": qty_bon
                    })

    final_combined_data = [item for item in combined_data if item["Total Stock Awal"] > 0]

    if final_combined_data:
        st.dataframe(pd.DataFrame(final_combined_data), use_container_width=True)
    else:
        st.info("Tidak ada sisa stok aktif atau bon baru untuk hari ini (semua stok bernilai 0 / habis).")

# ================= TAB 1: INPUT TRANSAKSI =================
with tab1:
    st.subheader("📝 Form Pencatatan Harian Transaksi & Stok")
    st.markdown("Pilih Nomor Bon untuk menampilkan otomatis seluruh merk rokok sesuai layout.")

    if "trx_form_reset_id" not in st.session_state:
        st.session_state.trx_form_reset_id = 0

    if "last_trx_msg" in st.session_state and st.session_state["last_trx_msg"]:
        st.success(st.session_state.pop("last_trx_msg"))

    all_bons = []
    if not st.session_state.df_bon.empty:
        all_bons = st.session_state.df_bon["ID"].unique().tolist()
    
    used_bons = []
    if not st.session_state.df_transaksi.empty and "No Bon" in st.session_state.df_transaksi.columns:
        used_bons = st.session_state.df_transaksi["No Bon"].unique().tolist()

    available_bons = [b for b in all_bons if b not in used_bons]

    def update_bon_fields():
        chosen = st.session_state.get(f"select_bon_trx_{st.session_state.trx_form_reset_id}", "- Manual Input -")
        if chosen != "- Manual Input -" and not st.session_state.df_bon.empty:
            matched_row = st.session_state.df_bon[st.session_state.df_bon["ID"] == chosen]
            if not matched_row.empty:
                st.session_state[f"no_bon_in_{st.session_state.trx_form_reset_id}"] = chosen
                st.session_state[f"nama_in_{st.session_state.trx_form_reset_id}"] = matched_row.iloc[0]["Team/Promotor"]
        else:
            st.session_state[f"no_bon_in_{st.session_state.trx_form_reset_id}"] = ""
            st.session_state[f"nama_in_{st.session_state.trx_form_reset_id}"] = ""

    selected_bon_id = st.selectbox(
        "🔍 Cari / Pilih No Bon", 
        options=["- Manual Input -"] + available_bons,
        key=f"select_bon_trx_{st.session_state.trx_form_reset_id}",
        on_change=update_bon_fields
    )

    default_no_bon = ""
    default_nama = ""
    if selected_bon_id != "- Manual Input -" and not st.session_state.df_bon.empty:
        matched_row = st.session_state.df_bon[st.session_state.df_bon["ID"] == selected_bon_id]
        if not matched_row.empty:
            default_no_bon = selected_bon_id
            default_nama = matched_row.iloc[0]["Team/Promotor"]

    text_bon_key = f"no_bon_in_{st.session_state.trx_form_reset_id}"
    text_nama_key = f"nama_in_{st.session_state.trx_form_reset_id}"
    
    if text_bon_key not in st.session_state:
        st.session_state[text_bon_key] = default_no_bon
    if text_nama_key not in st.session_state:
        st.session_state[text_nama_key] = default_nama

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown("**No Bon**")
        input_no_bon = st.text_input(
            "No Bon Input", 
            key=text_bon_key,
            label_visibility="collapsed"
        )
    with col_h2:
        st.markdown("**Nama**")
        input_nama = st.text_input(
            "Nama Input", 
            placeholder="Nama Promotor / Team", 
            key=text_nama_key,
            label_visibility="collapsed"
        )

    st.markdown("---")

    active_merks = []
    current_active_bon = st.session_state.get(text_bon_key, "")
    current_active_nama = st.session_state.get(text_nama_key, "")

    if current_active_bon and not st.session_state.df_bon.empty:
        selected_bon_rows = st.session_state.df_bon[st.session_state.df_bon["ID"] == current_active_bon]
        if not selected_bon_rows.empty:
            active_merks = selected_bon_rows["Merk Rokok"].tolist()
    
    if not active_merks:
        active_merks = list_merk[:3]

    with st.form(f"form_transaksi_layout_{st.session_state.trx_form_reset_id}", clear_on_submit=True):
        
        st.markdown("**Pilih Merk Rokok & Stock Awal (Stok Akhir Terakhir + Bon Hari Ini)**")
        stok_awal_values = {}
        
        for merk in active_merks:
            stok_terakhir = 0
            if current_active_nama and not st.session_state.df_transaksi.empty:
                df_sorted_trx = st.session_state.df_transaksi.sort_values(by="Tanggal", ascending=False)
                match_terakhir = df_sorted_trx[
                    (df_sorted_trx["Team/Promotor"].str.lower() == current_active_nama.lower()) & 
                    (df_sorted_trx["Merk Rokok"] == merk)
                ]
                if not match_terakhir.empty:
                    stok_terakhir = int(match_terakhir.iloc[0]["Stok Akhir"])

            bon_hari_ini = 0
            if current_active_bon and not st.session_state.df_bon.empty:
                match_bon = st.session_state.df_bon[
                    (st.session_state.df_bon["ID"] == current_active_bon) & 
                    (st.session_state.df_bon["Merk Rokok"] == merk)
                ]
                if not match_bon.empty:
                    bon_hari_ini = int(match_bon.iloc[0]["Total Setara Bungkus"])

            val_awal = stok_terakhir + bon_hari_ini
            stok_awal_values[merk] = val_awal

            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.markdown(f"🔹 **{merk}**")
            with c_v:
                st.markdown(f"📦 **{val_awal:,} bks** *(Stok Terakhir: {stok_terakhir} + Bon: {bon_hari_ini})*")

        st.markdown("---")
        st.markdown("**Rokok Belum Selesai / Gantung** | **Jumlah (dalam satuan bungkus)**")
        gantung_inputs = {}
        for merk in active_merks:
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                gantung_inputs[merk] = st.number_input(
                    f"Gantung_{merk}", 
                    min_value=0, 
                    value=0, 
                    key=f"gantung_{st.session_state.trx_form_reset_id}_{merk}",
                    label_visibility="collapsed"
                )

        st.markdown("---")
        st.markdown("**Sisa Stock Akhir** | **Jumlah (dalam satuan bungkus)**")
        akhir_inputs = {}
        for merk in active_merks:
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                akhir_inputs[merk] = st.number_input(
                    f"Akhir_{merk}", 
                    min_value=0, 
                    value=0, 
                    key=f"akhir_{st.session_state.trx_form_reset_id}_{merk}",
                    label_visibility="collapsed"
                )

        st.markdown("---")
        st.markdown("**Harga Jual Konsumen (Satuan)** | **Harga Jual Konsumen (Satuan)**")
        harga_inputs = {}
        for merk in active_merks:
            def_harga = dict_master_detail.get(merk, {}).get("harga_kanvas", 10000)
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                harga_inputs[merk] = st.number_input(
                    f"Harga_{merk}", 
                    min_value=0, 
                    value=int(def_harga), 
                    key=f"harga_{st.session_state.trx_form_reset_id}_{merk}",
                    label_visibility="collapsed"
                )

        st.markdown("---")
        st.markdown("**Pengeluaran Rokok Lain-lain** | **Jumlah (dalam satuan bungkus)**")
        lain_inputs = {}
        for merk in active_merks:
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                lain_inputs[merk] = st.number_input(
                    f"Lain_{merk}", 
                    min_value=0, 
                    value=0, 
                    key=f"lain_{st.session_state.trx_form_reset_id}_{merk}",
                    label_visibility="collapsed"
                )

        st.markdown("")
        submitted_all = st.form_submit_button("💾 Simpan Seluruh Transaksi Harian Ini", type="primary")

        if submitted_all:
            final_input_bon = st.session_state.get(text_bon_key, "")
            final_input_nama = st.session_state.get(text_nama_key, "")

            if not final_input_bon:
                st.error("No Bon wajib diisi!")
            else:
                saved_count = 0
                for merk in active_merks:
                    s_awal = stok_awal_values[merk]
                    s_akhir = akhir_inputs[merk]
                    s_gantung = gantung_inputs[merk]
                    s_lain = lain_inputs[merk]  
                    h_konsumen = harga_inputs[merk]
                    
                    h_kanvas = dict_master_detail.get(merk, {}).get("harga_kanvas", 10000)
                    terjual = max(0, (s_awal - s_akhir) - s_gantung - s_lain)
                    tot_kanvas = terjual * h_kanvas
                    tot_konsumen = terjual * h_konsumen

                    new_row = {
                        "ID": str(uuid.uuid4())[:8],
                        "No Bon": final_input_bon,
                        "Tanggal": str(selected_date),
                        "Minggu": current_week,
                        "Team/Promotor": final_input_nama if final_input_nama else "Tanpa Nama",
                        "Merk Rokok": merk,
                        "Stok Awal": s_awal,
                        "Stok Akhir": s_akhir,
                        "Belum Selesai": s_gantung,
                        "Rokok Lain-lain": s_lain,                
                        "Terjual": terjual,
                        "Harga Kanvas": h_kanvas,
                        "Harga Konsumen": h_konsumen,
                        "Total Setoran Kanvas": tot_kanvas,
                        "Total Setoran Konsumen": tot_konsumen
                    }
                    st.session_state.df_transaksi = pd.concat([st.session_state.df_transaksi, pd.DataFrame([new_row])], ignore_index=True)
                    saved_count += 1

                st.session_state.trx_form_reset_id += 1
                if text_bon_key in st.session_state:
                    del st.session_state[text_bon_key]
                if text_nama_key in st.session_state:
                    del st.session_state[text_nama_key]

                st.session_state["last_trx_msg"] = f"✅ Berhasil menyimpan {saved_count} data transaksi untuk No Bon **{final_input_bon}**!"
                st.rerun()
                
# ================= TAB 2: TABEL REKAP & EDIT =================
with tab2:
    st.subheader("📊 Tabel Rekapitulasi & Edit Data Transaksi")
    
    if not st.session_state.df_transaksi.empty:
        if "No Bon" not in st.session_state.df_transaksi.columns:
            st.session_state.df_transaksi["No Bon"] = st.session_state.df_transaksi["ID"]

        st.markdown("### ✏️ Edit Data Transaksi Langsung")
        edited_df = st.data_editor(
            st.session_state.df_transaksi,
            num_rows="dynamic",
            use_container_width=True,
            key="editable_transaction_table"
        )
        if not edited_df.equals(st.session_state.df_transaksi):
            st.session_state.df_transaksi = edited_df
            st.rerun()

        st.divider()

        st.markdown("### 🔍 Filter Berdasarkan Team / Promotor")
        list_teams = ["Semua Team"] + st.session_state.df_transaksi["Team/Promotor"].unique().tolist()
        selected_filter_team = st.selectbox("Pilih Team / Promotor untuk Filter Ringkasan", options=list_teams, key="filter_team_tab2")

        if selected_filter_team == "Semua Team":
            df_filtered = st.session_state.df_transaksi
        else:
            df_filtered = st.session_state.df_transaksi[st.session_state.df_transaksi["Team/Promotor"] == selected_filter_team]

        st.markdown("---")

        st.markdown(f"### 💰 Grand Total & Ringkasan Keuangan ({selected_filter_team})")
        
        grand_total_konsumen = df_filtered["Total Setoran Konsumen"].sum()
        grand_total_kanvas = df_filtered["Total Setoran Kanvas"].sum()
        total_terjual = df_filtered["Terjual"].sum()
        total_lain = df_filtered["Rokok Lain-lain"].sum() if "Rokok Lain-lain" in df_filtered.columns else 0

        col_gt1, col_gt2, col_gt3, col_gt4 = st.columns(4)
        with col_gt1:
            st.metric("Total Rokok Terjual", f"{total_terjual:,.0f} Bks")
        with col_gt2:
            st.metric("Total Rokok Lain-lain", f"{total_lain:,.0f} Bks")
        with col_gt3:
            st.metric("Grand Total Kanvas", f"Rp {grand_total_kanvas:,.0f}")
        with col_gt4:
            st.metric("🎯 Total Setoran Konsumen", f"Rp {grand_total_konsumen:,.0f}")

        st.markdown("---")

        st.markdown(f"### 📦 Kondisi Sisa Stock Akhir Terakhir per Merk Rokok ({selected_filter_team})")
        if not df_filtered.empty:
            df_sorted_all = df_filtered.sort_values(by="Tanggal", ascending=False)
            df_latest_stock = df_sorted_all.drop_duplicates(subset=["Team/Promotor", "Merk Rokok"], keep="first")
            df_sisa_merk = df_latest_stock.groupby("Merk Rokok")["Stok Akhir"].sum().reset_index()
            df_sisa_merk.columns = ["Merk Rokok", "Sisa Stok Akhir Terakhir (Bungkus)"]
            st.dataframe(df_sisa_merk, use_container_width=True)
        else:
            st.info("Tidak ada data untuk team ini.")

        st.markdown("---")

        st.markdown("### 📋 Rekapitulasi Berdasarkan Nomor Bon")
        if "No Bon" in st.session_state.df_transaksi.columns:
            df_rekap_bon = st.session_state.df_transaksi.groupby("No Bon").agg({
                "Team/Promotor": "first",
                "Tanggal": "first",
                "Terjual": "sum",
                "Rokok Lain-lain": "sum",
                "Total Setoran Kanvas": "sum",
                "Total Setoran Konsumen": "sum"
            }).reset_index()
            st.dataframe(df_rekap_bon, use_container_width=True)

        st.markdown("---")

        st.markdown("### 👥 Rekapitulasi Berdasarkan Team / Promotor")
        df_rekap_team = st.session_state.df_transaksi.groupby("Team/Promotor").agg({
            "Terjual": "sum",
            "Rokok Lain-lain": "sum",
            "Total Setoran Kanvas": "sum",
            "Total Setoran Konsumen": "sum"
        }).reset_index()
        st.dataframe(df_rekap_team, use_container_width=True)

        st.divider()

        st.markdown("### 🗑️ Menu Hapus Data")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            row_ids = st.session_state.df_transaksi["ID"].tolist()
            selected_id_to_delete = st.selectbox("Pilih ID Baris yang ingin dihapus", options=["-"] + row_ids)
            if st.button("Hapus Baris Terpilih"):
                if selected_id_to_delete != "-":
                    st.session_state.df_transaksi = st.session_state.df_transaksi[st.session_state.df_transaksi["ID"] != selected_id_to_delete]
                    st.success("Baris berhasil dihapus!")
                    st.rerun()
        with col_del2:
            unique_dates = st.session_state.df_transaksi["Tanggal"].unique().tolist()
            selected_date_to_delete = st.selectbox("Pilih Tanggal yang ingin dihapus total", options=["-"] + unique_dates)
            if st.button("Hapus Data Hari Ini"):
                if selected_date_to_delete != "-":
                    st.session_state.df_transaksi = st.session_state.df_transaksi[st.session_state.df_transaksi["Tanggal"] != selected_date_to_delete]
                    st.success("Data tanggal terpilih berhasil dihapus!")
                    st.rerun()
    else:
        st.info("Belum ada data transaksi tercatat.")

# ================= TAB 3: LAPORAN PENJUALAN PER TEAM =================
with tab_lap_team:
    st.subheader("👥 Laporan Data Penjualan per Team / Promotor")
    st.markdown("Filter dan Analisis Penjualan berdasarkan Team/Promotor lengkap dengan opsi download Excel.")

    if not st.session_state.df_transaksi.empty:
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            list_teams_lap = ["Semua Team"] + st.session_state.df_transaksi["Team/Promotor"].unique().tolist()
            filter_team_chosen = st.selectbox("Pilih Team / Promotor", options=list_teams_lap, key="filter_team_lap")
        with c_f2:
            list_dates_lap = ["Semua Tanggal"] + sorted(st.session_state.df_transaksi["Tanggal"].unique().tolist(), reverse=True)
            filter_date_chosen = st.selectbox("Filter Tanggal", options=list_dates_lap, key="filter_date_lap")

        df_lap = st.session_state.df_transaksi.copy()
        if filter_team_chosen != "Semua Team":
            df_lap = df_lap[df_lap["Team/Promotor"] == filter_team_chosen]
        if filter_date_chosen != "Semua Tanggal":
            df_lap = df_lap[df_lap["Tanggal"] == filter_date_chosen]

        if not df_lap.empty:
            df_grouped_lap = df_lap.groupby("Merk Rokok").agg({
                "Harga Kanvas": "first",
                "Terjual": "sum",
                "Total Setoran Kanvas": "sum",
                "Total Setoran Konsumen": "sum"
            }).reset_index()

            df_grouped_lap.columns = [
                "Merk Rokok", 
                "Harga Kanvas (per Bungkus)", 
                "Jumlah Rokok Laku (Bks)", 
                "Total (Harga Kanvas)", 
                "Total (Harga Konsumen)"
            ]

            st.markdown("#### Tabel Ringkasan Penjualan")
            st.dataframe(df_grouped_lap, use_container_width=True)

            if not df_grouped_lap.empty:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_grouped_lap.to_excel(writer, index=False, sheet_name='Laporan Penjualan')
                excel_data = output.getvalue()

                filename_excel = f"Laporan_Penjualan_{filter_team_chosen.replace(' ', '_')}.xlsx"
                st.download_button(
                    label="📥 Download Excel Laporan Ini",
                    data=excel_data,
                    file_name=filename_excel,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
        else:
            st.info("Tidak ada data transaksi yang sesuai dengan filter yang dipilih.")
    else:
        st.info("Belum ada data transaksi tercatat untuk dibuatkan laporan.")
        

# ================= TAB 4: MANAJEMEN BON (DENGAN KONVERSI OTOMATIS DARI MASTER) =================
with tab3:
    st.subheader("📋 Manajemen & Rekap Data Bon Rokok")
    st.markdown("Pilih beberapa keterangan sekaligus, lalu lihat ringkasan gabungan jumlah merk rokok lengkap dengan konversi otomatis Ball, Slop, & Bungkus.")

    if not st.session_state.df_bon.empty:
        # Ambil daftar unik keterangan dan team
        list_keterangan = []
        if "Keterangan" in st.session_state.df_bon.columns:
            unique_ket = st.session_state.df_bon["Keterangan"].dropna().unique().tolist()
            list_keterangan = [str(k) for k in unique_ket if str(k).strip() != ""]

        list_team_bon = ["Semua Team"] + sorted(st.session_state.df_bon["Team/Promotor"].dropna().unique().tolist())

        # Layout Filter
        col_fk1, col_fk2 = st.columns(2)
        with col_fk1:
            selected_ket_filter = st.multiselect(
                "🔍 Filter Keterangan (Bisa Pilih Banyak)", 
                options=list_keterangan, 
                default=list_keterangan, 
                key="filter_keterangan_multi"
            )
        with col_fk2:
            selected_team_bon_filter = st.selectbox("👥 Filter Team / Promotor", options=list_team_bon, key="filter_team_bon_mgmt_multi")

        # Terapkan Filter pada DataFrame Bon
        df_bon_filtered = st.session_state.df_bon.copy()
        
        if selected_ket_filter:
            df_bon_filtered = df_bon_filtered[df_bon_filtered["Keterangan"].isin(selected_ket_filter)]
        else:
            df_bon_filtered = df_bon_filtered.iloc[0:0]

        if selected_team_bon_filter != "Semua Team":
            df_bon_filtered = df_bon_filtered[df_bon_filtered["Team/Promotor"] == selected_team_bon_filter]

        st.markdown("---")
        st.markdown("#### 📊 Ringkasan Gabungan Merk Rokok & Konversi Otomatis")

        if not df_bon_filtered.empty:
            # 1. Group by Merk Rokok untuk menjumlahkan total bungkus mentahnya
            df_grouped_merk = df_bon_filtered.groupby("Merk Rokok").agg({
                "Total Setara Bungkus": "sum"
            }).reset_index()

            # 2. Hubungkan (Merge) dengan Master Konversi dari file JSON (dict_master_detail)
            # Setiap merk akan membawa data 'slop' dan 'bungkus' per ball dari file JSON
            hasil_tabel_konversi = []
            for _, row in df_grouped_merk.iterrows():
                merk_name = row["Merk Rokok"]
                total_bks = row["Total Setara Bungkus"]

                # Ambil data master untuk merk ini (default 1 Ball = 20 Slop = 200 Bks jika tidak ditemukan)
                master_info = dict_master_detail.get(merk_name, {"slop": 20, "bungkus": 200, "harga_kanvas": 0})
                
                slop_per_ball = master_info.get("slop", 20)
                bungkus_per_ball = master_info.get("bungkus", 200)
                
                # Hitung konversi otomatis berdasarkan standar master JSON
                # Contoh: 1 Ball = slop_per_ball Slop = bungkus_per_ball Bungkus
                bungkus_per_slop = 10
                
                ball = total_bks // bungkus_per_ball
                sisa_bks_1 = total_bks % bungkus_per_ball
                
                slop = sisa_bks_1 // bungkus_per_slop
                bungkus = sisa_bks_1 % bungkus_per_slop

                hasil_tabel_konversi.append({
                    "Merk Rokok": merk_name,
                    "Konversi Ball": int(ball),
                    "Konversi Slop": int(slop),
                    "Konversi Bungkus": int(bungkus),
                })

            df_final_display = pd.DataFrame(hasil_tabel_konversi)

            # Tampilkan metrik ringkas
            total_bks_all = df_final_display["Total Bungkus (Bks)"].sum()
            total_merk_unik = len(df_final_display)
            
            mc1, mc2 = st.columns(2)
            with mc1:
                st.metric("Total Jenis Merk Rokok", f"{total_merk_unik} Merk")
            with mc2:
                st.metric("Total Keseluruhan", f"{total_bks_all:,.0f} Bks")

            st.markdown("")
            st.markdown("##### 📌 Tabel Rekap Gabungan & Konversi Satuan")
            st.dataframe(df_final_display, use_container_width=True)

            st.divider()

            # Tabel Detail Data Asli (Opsional)
            with st.expander("🔎 Lihat Detail Rincian Baris Bon Asli"):
                edited_bon_table = st.data_editor(
                    df_bon_filtered,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editable_bon_table_multi_filtered"
                )
                if not edited_bon_table.equals(df_bon_filtered):
                    for idx, row in edited_bon_table.iterrows():
                        st.session_state.df_bon.loc[st.session_state.df_bon["ID"] == row["ID"]] = row
                    st.rerun()

            st.divider()

            # Rekapitulasi Berdasarkan Keterangan
            st.markdown("#### 📑 Ringkasan Total Bon Berdasarkan Keterangan")
            if "Keterangan" in st.session_state.df_bon.columns:
                df_rekap_ket = st.session_state.df_bon.groupby("Keterangan").agg({
                    "ID": "count",
                    "Total Setara Bungkus": "sum"
                }).reset_index()
                df_rekap_ket.columns = ["Keterangan", "Jumlah Bon", "Total Setara Bungkus (Bks)"]
                st.dataframe(df_rekap_ket, use_container_width=True)

        else:
            st.warning("Tidak ada data bon yang sesuai dengan filter pilihan Anda.")

        st.divider()

        # Menu Hapus Bon
        st.markdown("### 🗑️ Hapus Data Bon")
        bon_ids = st.session_state.df_bon["ID"].unique().tolist()
        del_bon_id = st.selectbox("Pilih No Bon yang ingin dihapus total", options=["-"] + bon_ids, key="select_del_bon")
        if st.button("Hapus Bon Terpilih"):
            if del_bon_id != "-":
                st.session_state.df_bon = st.session_state.df_bon[st.session_state.df_bon["ID"] != del_bon_id]
                st.success(f"No Bon {del_bon_id} berhasil dihapus!")
                st.rerun()
    else:
        st.info("Belum ada data bon rokok tercatat.")

### Penjelasan Alur Penghubungnya:
# 1. **Pencocokan Nama Merk**: Script melakukan perulangan (`for`) pada hasil ringkasan bon (`df_grouped_merk`), lalu mencocokkan kolom `"Merk Rokok"` dengan data dictionary master (`dict_master_detail`) yang bersumber dari `master_harga_rokok.json`.
# 2. **Pengambilan Aturan Konversi**: Dari file JSON tersebut, sistem secara otomatis membaca spesifikasi `slop` (misal 10 atau 20) dan `bungkus` (misal 100 atau 200) yang dimiliki masing-masing merk[cite: 2].
# 3. **Kalkulasi Matematis Otomatis**: 
 #   * Jika total bungkus berjumlah **11** untuk merk berstandar 200 bks/ball dan 20 slop/ball, sistem otomatis menghitung: `0 Ball, 1 Slop, 1 Bungkus`.
  #  * Jika total bungkus berjumlah **22 slop** (atau setara 220 bungkus), sistem otomatis menghitung: `1 Ball, 2 Slop, 0 Bungkus`.
# 4. **Tampilan Bersih**: Data disajikan dalam kolom terpisah (`Konversi Ball`, `Konversi Slop`, `Konversi Bungkus`) serta diringkas dalam kolom teks `Format Otomatis` tanpa memunculkan baris yang duplikat[cite: 2].
        

# ================= TAB 5: RESET & HAPUS ALL (ADMIN ONLY) =================
with tab4:
    st.subheader("⚙️ Zona Administratif: Reset & Hapus Keseluruhan")
    if role != "Admin":
        st.warning("⚠️ Menu ini dikunci dan hanya dapat diakses oleh **Admin**.")
    else:
        confirm_checkbox = st.checkbox("Saya mengerti risiko dan ingin menghapus seluruh data.")
        if st.button("🗑️ HAPUS SEMUA DATA (RESET ALL)", type="primary"):
            if confirm_checkbox:
                st.session_state.df_transaksi = pd.DataFrame(columns=st.session_state.df_transaksi.columns)
                st.session_state.df_bon = pd.DataFrame(columns=st.session_state.df_bon.columns)
                st.success("Semua data berhasil dibersihkan!")
                st.rerun()
            else:
                st.warning("Centang kotak konfirmasi terlebih dahulu.")
