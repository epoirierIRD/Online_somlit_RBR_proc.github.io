import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import zipfile

# --- Page title ---
st.title("My Data Processing Web App")

# --- File uploads ---
uploaded_files = st.file_uploader("Upload data files", type=["csv", "txt"], accept_multiple_files=True)

# --- Options for the script ---
option = st.radio("Choose processing method:", ["Method A", "Method B", "Method C"])

# --- Button to run script ---
if st.button("Process Files"):
    if not uploaded_files:
        st.error("Please upload at least one file!")
    else:
        # Create a zip file to store processed results
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for file in uploaded_files:
                try:
                    # Example: read CSV
                    df = pd.read_csv(file)
                    
                    # Example processing depending on option
                    if option == "Method A":
                        df_processed = df.describe()
                    elif option == "Method B":
                        df_processed = df  # Replace with your real method
                    else:
                        df_processed = df.cumsum()
                    
                    # Save processed CSV to zip
                    csv_bytes = df_processed.to_csv(index=False).encode("utf-8")
                    zip_file.writestr(f"processed_{file.name}", csv_bytes)
                    
                    # Plot example figure
                    st.subheader(f"Plot for {file.name}")
                    fig, ax = plt.subplots()
                    df_processed.hist(ax=ax)
                    st.pyplot(fig)
                except Exception as e:
                    st.error(f"Error processing {file.name}: {e}")

        # Provide download link for zip
        st.download_button(
            label="Download all processed files",
            data=zip_buffer.getvalue(),
            file_name="processed_files.zip",
            mime="application/zip"
        )
