import streamlit as st
import tempfile
import zipfile
import os
import base64

import RSKsomlit_proc as rsksproc

# --- Background image ---
# Function to set local background image
def set_bg_local(image_path):
    # Get absolute path
    full_path = os.path.join(os.path.dirname(__file__), image_path)
    
    # Read image and encode to base64
    with open(full_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    
    # Inject CSS
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;         /* Fill the page */
            background-repeat: no-repeat;
            background-attachment: fixed;  /* Stay in place on scroll */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Usage
set_bg_local("image/sondes_rz.jpg")

# ---- UI PANEL ---

with st.container():
    st.markdown(
        """
        <div style="background-color: rgba(0,0,0,0.6); padding: 2rem; border-radius: 10px;">
        """,
        unsafe_allow_html=True)
    
    
    # Title
    st.title("Somlit RSK/RBR File Processor")
    st.write('Your content goes here')
    
    # --- File upload ---
    uploaded_file = st.file_uploader("Upload RSK/RBR file", type=["rsk", "rbr"])
    
    # --- Manual inputs ---
    site_id = st.text_input("Site ID")
    atmospheric_pressure = st.number_input("Atmospheric Pressure (dbar)", min_value=1.1325)
    pressure_threshold = st.number_input("Pressure Threshold", min_value=0.4)
    conductivity_threshold = st.number_input("Conductivity Threshold", min_value=5)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
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
                    
                    # Create a subfolder for first-step processing
                    proc_data_dir = os.path.join(tmpdir, "proc_data")
                    os.makedirs(proc_data_dir, exist_ok=True)

                    # first step processing
                    files_to_process = rsksproc.export_profiles2rsk(tmp_path, proc_data_dir)
                    
                    # second step processing
                    
                    rsksproc.process_rsk_folder(
                        path_in = proc_data_dir,
                        list_of_rsk = files_to_process,
                        site_id = site_id,
                        patm = atmospheric_pressure,
                        p_tresh = pressure_threshold,  # 0.4 for multiple rsk // 0.05 for simple profile
                        c_tresh = conductivity_threshold,  # 5 for multiple rsk // 0.5 for simple profile
                        param=['conductivity',
                               'temperature',
                               # 'pressure',
                               'temperature1',
                               'dissolved_o2_concentration',
                               'par',
                               'ph',
                               'chlorophyll-a',
                               'fdom',
                               'turbidity',
                               # 'sea_pressure',
                               'depth',
                               'salinity',
                               # 'speed_of_sound',
                               # 'specific_conductivity',
                               # 'dissolved_o2_saturation',
                               # 'velocity',
                               'density_anomaly'
                               ])
                    
                    
                    # Create a zip file of all outputs
                    zip_path = os.path.join(tmpdir, "processed_output.zip")
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(proc_data_dir):
                            for file in files:
                                full_path = os.path.join(root, file)
                                # Make arcname relative to proc_data_dir
                                arcname = os.path.relpath(full_path, proc_data_dir)
                                zipf.write(full_path, arcname=arcname)
                    
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
