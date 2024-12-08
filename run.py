import streamlit as st
import streamlit.web.cli as stcli
import pandas as pd
import io
import os, sys
import hashlib
st.set_page_config(
        page_title="App Data Shuffler",
)

# https://ploomber.io/blog/streamlit_exe/

def resolve_path(path):
    resolved_path = os.path.abspath(os.path.join(os.getcwd(), path))
    return resolved_path

def shuffle_dataframe(data):
    return data.sample(frac=1)

def calculate_file_hash(file):
    """Calculate the hash of the file content."""
    hasher = hashlib.md5()
    # Read file content and update the hash
    file.seek(0)  # Ensure the file pointer is at the start
    hasher.update(file.read())
    file.seek(0)  # Reset the file pointer for further use
    return hasher.hexdigest()

if "df" not in st.session_state:
    st.session_state.df = None
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "file_hash" not in st.session_state:
    st.session_state.file_hash = None

# Streamlit App
st.title("App data Shuffler")

# File upload
col1, col2, col3 = st.columns([3, 1,1])  # Define column widths

# First item spans two rows and two columns
with col1:
    uploaded_file = st.file_uploader("Upload file", type=["csv", "xlsx","txt"])

# Second row in the last column for delimiter and decimal separator
with col2:
    st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)  # Spacer to align height
    delimiter = st.text_input("Delimiter", value=",")

with col3:
    st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)  # Spacer to align height
    decimal_separator = st.text_input("Decimal Separator", value=".")

if uploaded_file:
    # Read file
    uploaded_file_hash = calculate_file_hash(uploaded_file)

    # Check if the file is new (either name or content has changed)
    if st.session_state.uploaded_file_name != uploaded_file.name or st.session_state.file_hash != uploaded_file_hash:
        # Reset state for a new upload
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.file_hash = uploaded_file_hash
        st.session_state.df = pd.DataFrame()  # Clear existing DataFrame

        try:
            if uploaded_file.name.endswith(".CSV") or uploaded_file.name.endswith(".TXT") or uploaded_file.name.endswith(".csv") or uploaded_file.name.endswith(".txt"):
                st.session_state.df = pd.read_csv(uploaded_file, delimiter=delimiter, decimal=decimal_separator,dtype=str)
            elif uploaded_file.name.endswith(".xlsx") or uploaded_file.name.endswith(".XLSX"):
                st.session_state.df = pd.read_excel(uploaded_file,engine='openpyxl',dtype=str)
            
            st.session_state.df.index.name = 'Index'

        except Exception as e:
            st.error(f"Error reading file: {e}")
        

    st.subheader("Filter Data")
    
    filters = {}
    na_fix = {}

    # Wrap the filter UI in an expander
    with st.expander("Show Filters"):
        for col in st.session_state.df.columns:
            if st.session_state.df[col].dtype == 'object':  # For categorical data
                unique_values = st.session_state.df[col].dropna().unique().tolist()
                filters[col] = st.multiselect(f"Filter {col}", options=unique_values)

                if st.session_state.df[col].isna().any():
                    na_fix[col] = st.checkbox(f"{col} - Include Empty values",value=False,key=col)
                else:
                    na_fix[col] = True

            elif pd.api.types.is_numeric_dtype(st.session_state.df[col]):  # For numeric data
                col_min = st.session_state.df[col].dropna().min()
                col_max = st.session_state.df[col].dropna().max()

                # Handle constant values
                if col_min == col_max:
                    filters[col] = (col_min, col_max)
                    st.write(f"Filter {col}: Single value {col_min}")
                else:
                    min_val, max_val = st.slider(
                        f"Filter {col} (Range)", float(col_min), float(col_max), (float(col_min), float(col_max))
                    )
                    filters[col] = (min_val, max_val)

                if st.session_state.df[col].isna().any():
                    na_fix[col] = st.checkbox(f"{col} Include Empty values",value=True,key=col)
                else:
                    na_fix[col] = True

    # Apply filters
    for col, filter_value in filters.items():
        if isinstance(filter_value, list) and filter_value:  # For categorical filters
            st.session_state.df = st.session_state.df[(st.session_state.df[col].isin(filter_value)) | ((st.session_state.df[col].isna()) & (na_fix[col]))]     
        elif isinstance(filter_value, tuple):  # For numeric range filters
            min_val, max_val = filter_value
            st.session_state.df = st.session_state.df[((st.session_state.df[col] >= min_val) & (st.session_state.df[col] <= max_val)) | ((st.session_state.df[col].isna()) & (na_fix[col]))]

    # Shuffle button
    if st.button("Shuffle Data"):
        st.session_state.df = shuffle_dataframe(st.session_state.df)

    # Display shuffled data (first 30 rows)
    st.subheader(f"Data (First 30 Rows of {len(st.session_state.df)})")
    st.dataframe(st.session_state.df.head(30))

    # Export options
    st.subheader("Export Filtered Data")
    num_rows = st.number_input(f"Select number of rows to export (max {len(st.session_state.df)})", min_value=0, value=len(st.session_state.df), step=1)

    # File export options
    export_file_format = st.radio("Select export format", options=["CSV", "Excel"])
    if st.button("Export File"):
        if export_file_format == "CSV":
            csv_data = st.session_state.df.head(num_rows).to_csv(index=False,sep=delimiter,decimal=decimal_separator)
            st.download_button(label="Download CSV", data=csv_data, file_name="data.csv", mime="text/csv")
        elif export_file_format == "Excel":
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                st.session_state.df.head(num_rows).to_excel(writer, index=False, sheet_name='Sheet1')
            st.download_button(label="Download Excel", data=buffer, file_name="data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
