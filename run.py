import streamlit as st
import streamlit.web.cli as stcli
import pandas as pd
import io
import os, sys

st.set_page_config(
        page_title="App Data Shuffler",
)

# https://ploomber.io/blog/streamlit_exe/

def resolve_path(path):
    resolved_path = os.path.abspath(os.path.join(os.getcwd(), path))
    return resolved_path

# Streamlit App
def main():
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
        try:
            if uploaded_file.name.endswith(".CSV") or uploaded_file.name.endswith(".TXT") or uploaded_file.name.endswith(".csv") or uploaded_file.name.endswith(".txt"):
                df = pd.read_csv(uploaded_file, delimiter=delimiter, decimal=decimal_separator,dtype=str)
            elif uploaded_file.name.endswith(".xlsx") or uploaded_file.name.endswith(".XLSX"):
                df = pd.read_excel(uploaded_file,engine='openpyxl',dtype=str)
            
            df.index.name = 'Index'

        except Exception as e:
            st.error(f"Error reading file: {e}")
            return

        # Shuffle rows
        def shuffle_dataframe(data):
            return data.sample(frac=1)

        st.subheader("Filter Data")
        
        filters = {}
        na_fix = {}

        # Wrap the filter UI in an expander
        with st.expander("Show Filters"):
            for col in df.columns:
                if df[col].dtype == 'object':  # For categorical data
                    unique_values = df[col].dropna().unique().tolist()
                    filters[col] = st.multiselect(f"Filter {col}", options=unique_values)

                    if df[col].isna().any():
                        na_fix[col] = st.checkbox(f"{col} - Include Empty values",value=False,key=col)
                    else:
                        na_fix[col] = True

                elif pd.api.types.is_numeric_dtype(df[col]):  # For numeric data
                    col_min = df[col].dropna().min()
                    col_max = df[col].dropna().max()

                    # Handle constant values
                    if col_min == col_max:
                        filters[col] = (col_min, col_max)
                        st.write(f"Filter {col}: Single value {col_min}")
                    else:
                        min_val, max_val = st.slider(
                            f"Filter {col} (Range)", float(col_min), float(col_max), (float(col_min), float(col_max))
                        )
                        filters[col] = (min_val, max_val)

                    if df[col].isna().any():
                        na_fix[col] = st.checkbox(f"{col} Include Empty values",value=True,key=col)
                    else:
                        na_fix[col] = True

        # Apply filters
        for col, filter_value in filters.items():
            if isinstance(filter_value, list) and filter_value:  # For categorical filters
                df = df[(df[col].isin(filter_value)) | ((df[col].isna()) & (na_fix[col]))]     
            elif isinstance(filter_value, tuple):  # For numeric range filters
                min_val, max_val = filter_value
                df = df[((df[col] >= min_val) & (df[col] <= max_val)) | ((df[col].isna()) & (na_fix[col]))]

        # Shuffle button
        if st.button("Shuffle Data"):
            df = shuffle_dataframe(df)

        # Display shuffled data (first 30 rows)
        st.subheader(f"Data (First 30 Rows of {len(df)})")
        st.dataframe(df.head(30))

        # Export options
        st.subheader("Export Filtered Data")
        num_rows = st.number_input(f"Select number of rows to export (max {len(df)})", min_value=0, value=len(df), step=1)

        # File export options
        export_file_format = st.radio("Select export format", options=["CSV", "Excel"])
        if st.button("Export File"):
            if export_file_format == "CSV":
                csv_data = df.head(num_rows).to_csv(index=False,sep=delimiter,decimal=decimal_separator)
                st.download_button(label="Download CSV", data=csv_data, file_name="data.csv", mime="text/csv")
            elif export_file_format == "Excel":
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.head(num_rows).to_excel(writer, index=False, sheet_name='Sheet1')
                st.download_button(label="Download Excel", data=buffer, file_name="data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
