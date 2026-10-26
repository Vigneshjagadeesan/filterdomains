import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Domain Intelligence Dashboard", layout="wide")

st.title("🎯 High-Authority Filtered Domains Dashboard")

# CSV Files list
files = {
    "p=none Policy": "POWER_p_none_domains.csv",
    "no_dmarc Policy": "POWER_no_dmarc_domains.csv",
    "p=quarantine Policy": "POWER_p_quarantine_domains.csv"
}

# Sidebar - Policy Selection
selected_policy = st.sidebar.selectbox("Select DMARC Policy File", list(files.keys()))
csv_path = files[selected_policy]

@st.cache_data
def load_data(filepath):
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        # Clean & format numeric columns
        df['Referring_Domains'] = pd.to_numeric(df['Referring_Domains'], errors='coerce').fillna(0).astype(int)
        df['OpenPageRank_Score'] = pd.to_numeric(df['OpenPageRank_Score'], errors='coerce').fillna(0.0)
        return df
    return None

df = load_data(csv_path)

if df is not None:
    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    
    # 1. TLD Specification Filter
    available_tlds = sorted(df['Extension'].dropna().unique().tolist())
    selected_tlds = st.sidebar.multiselect("Select TLDs", options=available_tlds)
    
    # 2. Domain Keyword Search
    search_keyword = st.sidebar.text_input("Search Domain Name (Contains)")

    # 3. Referring Domains Range Filter
    min_ref = int(df['Referring_Domains'].min())
    max_ref = int(df['Referring_Domains'].max())
    ref_range = st.sidebar.slider("Referring Domains Range", min_ref, max_ref, (min_ref, max_ref))

    # Apply Filters
    filtered_df = df.copy()
    
    if selected_tlds:
        filtered_df = filtered_df[filtered_df['Extension'].isin(selected_tlds)]
        
    if search_keyword:
        filtered_df = filtered_df[filtered_df['Domain'].str.contains(search_keyword.lower(), na=False)]
        
    filtered_df = filtered_df[
        (filtered_df['Referring_Domains'] >= ref_range[0]) & 
        (filtered_df['Referring_Domains'] <= ref_range[1])
    ]

    # Sort Options (Default: Low to High)
    sort_order = st.sidebar.radio("Sort Referring Domains", ["Low to High (Ascending)", "High to Low (Descending)"])
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
        file_name="filtered_result.csv",
        mime="text/csv"
    )

else:
    st.error(f"File not found: `{csv_path}`. Please verify the folder contents!")