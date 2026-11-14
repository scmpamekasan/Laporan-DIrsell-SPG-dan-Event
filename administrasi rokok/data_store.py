import streamlit as st
import pandas as pd
import json
import os

def load_master_harga():
    # Cek apakah file berada di dalam folder reportspg/ atau di root
    possible_paths = [
        "master_harga_rokok.json",
        "administrasirokok/master_harga_rokok.json",
        "./master_harga_rokok.json"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
                
    # Fallback jika benar-benar tidak ketemu
    return [
        {"merk": "D 76 12", "harga_kanvas": 15500, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "LA Bold 16", "harga_kanvas": 29300, "ball": 1, "slop": 10, "bungkus": 100}
    ]
