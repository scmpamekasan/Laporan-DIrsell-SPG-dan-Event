import json
import os

import pandas as pd
import streamlit as st


def _master_file_path():
    """Return the JSON path alongside this module."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "master_harga_rokok.json")


def _master_file_signature():
    """Return a signature that changes when the JSON file is updated."""
    try:
        stat = os.stat(_master_file_path())
        return (stat.st_mtime_ns, stat.st_size)
    except OSError:
        return None


def save_master_harga(master_data):
    """Persist cigarette master data to the JSON file next to this module."""
    try:
        with open(_master_file_path(), "w", encoding="utf-8") as f:
            json.dump(master_data, f, indent=4, ensure_ascii=False)
        return True
    except (OSError, TypeError) as e:
        st.error(f"⚠️ Gagal menyimpan file `master_harga_rokok.json`: {e}")
        return False


class _AutoSavingDict(dict):
    """A master row that saves JSON immediately when a field is edited."""

    def __init__(self, values, on_change):
        super().__init__(values)
        self._on_change = on_change

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._on_change()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._on_change()

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self._on_change()


class _AutoSavingList(list):
    """A master list that saves JSON immediately when brands are added/removed."""

    def __init__(self, values=()):
        super().__init__()
        self._saving = False
        self.extend(values, save=False)
        self._saving = True

    def _notify_change(self):
        if self._saving:
            save_master_harga(self)

    def _wrap(self, value):
        if isinstance(value, dict) and not isinstance(value, _AutoSavingDict):
            return _AutoSavingDict(value, self._notify_change)
        return value

    def append(self, value):
        super().append(self._wrap(value))
        self._notify_change()

    def extend(self, values, save=True):
        super().extend(self._wrap(value) for value in values)
        if save:
            self._notify_change()

    def insert(self, index, value):
        super().insert(index, self._wrap(value))
        self._notify_change()

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            value = [self._wrap(item) for item in value]
        else:
            value = self._wrap(value)
        super().__setitem__(index, value)
        self._notify_change()

    def __delitem__(self, index):
        super().__delitem__(index)
        self._notify_change()

    def pop(self, index=-1):
        value = super().pop(index)
        self._notify_change()
        return value

    def remove(self, value):
        super().remove(value)
        self._notify_change()

    def clear(self):
        super().clear()
        self._notify_change()


_DEFAULT_MASTER_DATA = [
    {"merk": "Black Matcha K12", "harga_kanvas": 15000, "harga_konsumen": 18000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "D.Super 12", "harga_kanvas": 21000, "harga_konsumen": 25000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "D.76 Apel Royal", "harga_kanvas": 12000, "harga_konsumen": 15000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "D.76 Apel", "harga_kanvas": 12000, "harga_konsumen": 15000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "Djarum 76 Aksara", "harga_kanvas": 11000, "harga_konsumen": 14000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "Djarum Black Siro", "harga_kanvas": 22000, "harga_konsumen": 26000, "ball": 1, "slop": 20, "bungkus": 200},
    {"merk": "Djarum Black Kuro", "harga_kanvas": 22000, "harga_konsumen": 26000, "ball": 1, "slop": 20, "bungkus": 200},
]


def _autosaving_master(data):
    return _AutoSavingList(data)


def load_master_harga():
    """Load master data from master_harga_rokok.json in this folder."""
    file_path = _master_file_path()

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and all(isinstance(item, dict) and item.get("merk") for item in data):
                return _autosaving_master(data)
            st.error("⚠️ Format master_harga_rokok.json tidak valid. Setiap data harus berupa objek dengan kolom 'merk'.")
        except (OSError, json.JSONDecodeError) as e:
            st.error(f"⚠️ Gagal membaca file `master_harga_rokok.json`: {e}")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(_DEFAULT_MASTER_DATA, f, indent=4, ensure_ascii=False)
    except OSError as e:
        st.error(f"⚠️ Gagal membuat file `master_harga_rokok.json`: {e}")

    return _autosaving_master(_DEFAULT_MASTER_DATA)


def _sync_master_file():
    """Reload externally changed JSON or persist in-memory master edits."""
    file_path = _master_file_path()
    current_signature = _master_file_signature()
    previous_signature = st.session_state.get("master_rokok_file_signature")

    # JSON is the source of truth for a new session and whenever the file changes.
    if previous_signature is None or current_signature != previous_signature:
        st.session_state.master_rokok_data = load_master_harga()
        st.session_state.master_rokok_file_signature = _master_file_signature()
        return

    master_data = st.session_state.get("master_rokok_data")
    if not isinstance(master_data, list):
        st.session_state.master_rokok_data = load_master_harga()
        st.session_state.master_rokok_file_signature = _master_file_signature()
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
    except (OSError, json.JSONDecodeError):
        saved_data = None

    if saved_data != master_data and save_master_harga(master_data):
        st.session_state.master_rokok_file_signature = _master_file_signature()


def init_session_state():
    """Initialize application tables and synchronize the master JSON."""
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

    _sync_master_file()
