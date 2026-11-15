import json
import os

import pandas as pd
import streamlit as st


def _master_file_path():
    """Return the master JSON path in the same folder as this module."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "master_harga_rokok.json")


def save_master_harga(master_data):
    """Persist master brands/prices to master_harga_rokok.json."""
    try:
        # Convert subclasses to plain containers before serializing.
        data = [dict(item) for item in master_data]
        with open(_master_file_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except (OSError, TypeError) as e:
        st.error(f"⚠️ Gagal menyimpan file `master_harga_rokok.json`: {e}")
        return False


class _MasterItem(dict):
    """Dictionary row that writes changes to the JSON file immediately."""

    def __init__(self, value, on_change):
        super().__init__(value)
        self._on_change = on_change

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._on_change()

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self._on_change()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._on_change()


class _MasterList(list):
    """List that persists additions/removals and nested row edits immediately."""

    def __init__(self, values=()):
        self._saving = False
        super().__init__(_MasterItem(row, self._save) for row in values)
        self._saving = True

    def _save(self):
        if self._saving:
            save_master_harga(self)

    def append(self, value):
        super().append(_MasterItem(value, self._save))
        self._save()

    def extend(self, values):
        super().extend(_MasterItem(row, self._save) for row in values)
        self._save()

    def insert(self, index, value):
        super().insert(index, _MasterItem(value, self._save))
        self._save()

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            value = [_MasterItem(row, self._save) for row in value]
        else:
            value = _MasterItem(value, self._save)
        super().__setitem__(index, value)
        self._save()

    def __delitem__(self, index):
        super().__delitem__(index)
        self._save()

    def pop(self, index=-1):
        value = super().pop(index)
        self._save()
        return value

    def remove(self, value):
        super().remove(value)
        self._save()

    def clear(self):
        super().clear()
        self._save()


_DEFAULT_MASTER_DATA = [
    {"merk": "Black Matcha K12", "harga_kanvas": 15000, "harga_konsumen": 18000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "D.Super 12", "harga_kanvas": 21000, "harga_konsumen": 25000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "D.76 Apel Royal", "harga_kanvas": 12000, "harga_konsumen": 15000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "D.76 Apel", "harga_kanvas": 12000, "harga_konsumen": 15000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "Djarum 76 Aksara", "harga_kanvas": 11000, "harga_konsumen": 14000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "Djarum Black Siro", "harga_kanvas": 22000, "harga_konsumen": 26000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "Djarum Black Kuro", "harga_kanvas": 22000, "harga_konsumen": 26000, "ball": 1, "slop": 20, "bungkus": 200},
]


def load_master_harga():
    """Read and validate the JSON master file and return an auto-saving list."""
    file_path = _master_file_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and all(
                isinstance(item, dict) and str(item.get("merk", "")).strip()
                for item in data
            ):
                return _MasterList(data)
            st.error("⚠️ Format master_harga_rokok.json tidak valid; setiap item harus memiliki kolom 'merk'.")
        except (OSError, json.JSONDecodeError) as e:
            st.error(f"⚠️ Gagal membaca file `master_harga_rokok.json`: {e}")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(_DEFAULT_MASTER_DATA, f, indent=4, ensure_ascii=False)
    except OSError as e:
        st.error(f"⚠️ Gagal membuat file `master_harga_rokok.json`: {e}")
    return _MasterList(_DEFAULT_MASTER_DATA)


def init_session_state():
    """Initialize application tables if they do not exist yet."""
    if "df_transaksi" not in st.session_state:
        st.session_state.df_transaksi = pd.DataFrame(columns=[
            "ID", "No Bon", "Tanggal", "Minggu", "Team/Promotor", "Merk Rokok",
            "Stock Awal", "Stock Akhir", "Belum Selesai", "Rokok Lain-lain",
            "Terjual", "Harga Kanvas", "Harga Konsumen", "Total Setoran Kanvas", "Total Setoran"
        ])

    if "df_bon" not in st.session_state:
        st.session_state.df_bon = pd.DataFrame(columns=[
            "ID", "Tanggal", "Team/Promotor", "Merk Rokok", "Ball", "Slop", "Bungkus",
            "Total Setara Bungkus", "Keperluan", "Keterangan"
        ])

    if "df_pre_entry_bon" not in st.session_state:
        st.session_state.df_pre_entry_bon = pd.DataFrame(columns=[
            "ID Draft", "Tanggal", "Rencana Penyelesaian", "Team/Promotor", "Merk Rokok",
            "Ball", "Slop", "Bungkus", "Total Setara Bungkus", "Keperluan", "Keterangan"
        ])

    if "df_penyelesaian_gudang" not in st.session_state:
        st.session_state.df_penyelesaian_gudang = pd.DataFrame(columns=[
            "ID Penyelesaian", "Tanggal", "Team/Promotor", "Merk Rokok", "Jumlah Bungkus", "Keterangan"
        ])
