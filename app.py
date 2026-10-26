import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Domain Intelligence Dashboard", layout="wide")

st.title("🎯 High-Authority Filtered Domains Dashboard")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Check which files exist in the directory
p_none_file = os.path.join(BASE_DIR, "POWER_p_none_domains.csv")
no_dmarc_file = os.path.join(BASE_DIR, "POWER_no_dmarc_domains.csv")
quarantine_file = os.path.join(BASE_DIR, "POWER_p_quarantine_domains.csv")
legacy_usable_file = os.path.join(BASE_DIR, "POWER_inbox_usable_domains.csv")

@st.cache_data
def load_all_data():
    data_dict = {}
    
    # Mode A: If separate files exist
    if os.path.exists(p_none_file):
        df_p_none = pd.read_csv(p_none_file)
        data_dict["p=none Policy"] = df_p_none
    if os.path.exists(no_dmarc_file):
        df_no_dmarc = pd.read_csv(no_dmarc_file)
        data_dict["no_dmarc Policy"] = df_no_dmarc
        
    # Mode B: If only legacy combined usable file exists
    if not data_dict and os.path.exists(legacy_usable_file):
        df_legacy = pd.read_csv(legacy_usable_file)
        if 'DMARC_Policy' in df_legacy.columns:
            data_dict["p=none Policy"] = df_legacy[df_legacy['DMARC_Policy'].str.lower() == 'p=none']
            data_dict["no_dmarc Policy"] = df_legacy[df_legacy['DMARC_Policy'].str.lower() != 'p=none']
        else:
            data_dict["All Usable Domains"] = df_legacy

    # Load Quarantine if available
    if os.path.exists(quarantine_file):
        df_quarantine = pd.read_csv(quarantine_file)
        data_dict["p=quarantine Policy"] = df_quarantine
        
    # Clean up numerical columns for all dataframes
    for key in data_dict:
        df = data_dict[key].copy()
        if 'Referring_Domains' in df.columns:
            df['Referring_Domains'] = pd.to_numeric(df['Referring_Domains'], errors='coerce').fillna(0).astype(int)
        if 'OpenPageRank_Score' in df.columns:
            df['OpenPageRank_Score'] = pd.to_numeric(df['OpenPageRank_Score'], errors='coerce').fillna(0.0)
        data_dict[key] = df

    return data_dict

all_data = load_all_data()

if not all_data:
    st.error("No CSV files found in this folder! Make sure either `POWER_inbox_usable_domains.csv` or `POWER_p_none_domains.csv` is present in the repository/folder.")
else:
    # Sidebar Selection
    selected_policy = st.sidebar.selectbox("Select DMARC Policy File", list(all_data.keys()))
    df = all_data[selected_policy]

    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    
    # 1. TLD Specification Filter
    if 'Extension' in df.columns:
        available_tlds = sorted(df['Extension'].dropna().astype(str).unique().tolist())
        selected_tlds = st.sidebar.multiselect("Select TLDs", options=available_tlds)
    else:
        selected_tlds = []
    
    # 2. Domain Keyword Search
    search_keyword = st.sidebar.text_input("Search Domain Name (Contains)")

    # 3. Referring Domains Range Filter
    if 'Referring_Domains' in df.columns and len(df) > 0:
        min_ref = int(df['Referring_Domains'].min())
        max_ref = int(df['Referring_Domains'].max())
        if min_ref == max_ref:
            max_ref += 1
        ref_range = st.sidebar.slider("Referring Domains Range", min_ref, max_ref, (min_ref, max_ref))
    else:
        ref_range = (0, 0)

    # Apply Filters
    filtered_df = df.copy()
    
    if selected_tlds and 'Extension' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Extension'].isin(selected_tlds)]
        
    if search_keyword and 'Domain' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Domain'].astype(str).str.contains(search_keyword.lower(), na=False)]
        
    if 'Referring_Domains' in filtered_df.columns and len(df) > 0:
        filtered_df = filtered_df[
            (filtered_df['Referring_Domains'] >= ref_range[0]) & 
            (filtered_df['Referring_Domains'] <= ref_range[1])
        ]

    # Sort Options (Default: Low to High)
    sort_order = st.sidebar.radio("Sort Referring Domains", ["Low to High (Ascending)", "High to Low (Descending)"])
    if 'Referring_Domains' in filtered_df.columns:
        if sort_order == "Low to High (Ascending)":
            filtered_df = filtered_df.sort_values(by="Referring_Domains", ascending=True)
        else:
            filtered_df = filtered_df.sort_values(by="Referring_Domains", ascending=False)

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Domains in File", f"{len(df):,}")
    col2.metric("Filtered Domains", f"{len(filtered_df):,}")
    col3.metric("Selected TLDs Count", len(selected_tlds) if selected_tlds else "All")

    # Display Data Table
    st.subheader(f"Showing Results for: {selected_policy}")
    st.dataframe(filtered_df, use_container_width=True)

    # Download Filtered CSV Button
    csv_download = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Download Filtered Domains (CSV)",
        data=csv_download,
        file_name=f"{selected_policy.replace(' ', '_').lower()}_result.csv",
        mime="text/csv"
    )
