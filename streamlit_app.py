import streamlit as st
import tempfile
import zipfile
import os
from process_rbr import process_rbr_file  # your script function

st.title("RSK/RBR File Processor")

# --- File upload ---
uploaded_file = st.file_uploader("Upload RSK/RBR file", type=["rsk", "rbr"])

# --- Manual inputs ---
site_id = st.text_input("Site ID")
atmospheric_pressure = st.number_input("Atmospheric Pressure (dbar)", min_value=0.0)
pressure_threshold = st.number_input("Pressure Threshold", min_value=0.0)
conductivity_threshold = st.number_input("Conductivity Threshold", min_value=0.0)

# --- Process button ---
if st.button("Process File"):
    if not uploaded_file:
        st.error("Please upload a file first!")
    elif not site_id:
        st.error("Please enter Site ID")
    else:
        try:
            # Create temporary directory to store input & outputs
            with tempfile.TemporaryDirectory() as tmpdir:
                # Save uploaded file
                tmp_path = os.path.join(tmpdir, uploaded_file.name)
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_file.read())
                
                # Call your processing function
                # Replace with your actual script call
                # The function should return a folder path with all outputs
                output_folder = process_rbr_file(
                    file_path=tmp_path,
                    site_id=site_id,
                    atmospheric_pressure=atmospheric_pressure,
                    pressure_threshold=pressure_threshold,
                    conductivity_threshold=conductivity_threshold,
                    output_dir=tmpdir
                )
                
                # Create a zip file of all outputs
                zip_path = os.path.join(tmpdir, "processed_output.zip")
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(output_folder):
                        for file in files:
                            zipf.write(os.path.join(root, file), arcname=file)
                
                # Provide download button
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Download Processed Output",
                        data=f,
                        file_name="processed_output.zip",
                        mime="application/zip"
                    )
                st.success("Processing complete!")

        except Exception as e:
            st.error(f"Error processing file: {e}")
