#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 14:53:22 2026

@author: epoirier
"""

import streamlit as st
import tempfile
import zipfile
import os
import base64

import RSKsomlit_proc as rsksproc


# --- Background image ---
def set_bg_local(image_path):
    full_path = os.path.join(os.path.dirname(__file__), image_path)
    with open(full_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# Set background ONCE
set_bg_local("image/sondes_rz.jpg")


# ---- UI PANEL ----
st.markdown(
    """
    <style>
    .overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(255,255,255,0.75);  /* semi-transparent white */
        z-index: 0;
    }

    .content {
        position: relative;
        z-index: 1;           /* above overlay */
        max-width: 900px;
        margin: auto;
        padding: 2rem;
        border-radius: 12px;
        color: white;
    }

    .content input, .content textarea, .content select {
        color: black;  /* make input text readable */
    }
    </style>
    """,
    unsafe_allow_html=True
)
# render overlay
st.markdown('<div class="overlay"></div>', unsafe_allow_html=True)

# render content container
st.markdown('<div class="content">', unsafe_allow_html=True)


st.title("Somlit RSK/RBR File Processor")
st.write("Upload your RSK/RBR file and set processing parameters.")

# --- PRAMETERS ----
uploaded_file = st.file_uploader("Upload RSK/RBR file", type=["rsk", "rbr"])

# Site-ID dropdown with location of the Somlit point
site_options = {"Plouzané":5,"La Rochelle": 1, "Roscoff": 2, "Arcachon": 3, "Wimereux": 4}
selected_site = st.selectbox("SOMLIT Station", options=list(site_options.keys()))
site_id = site_options[selected_site]  # integer used internally

# atmospheric pressure the day of the profile
atmospheric_pressure = st.number_input(
    "Atmospheric Pressure (dbar)",
    min_value=9.5,
    max_value=10.8,   # optional max
    value=10.1325,       # optional default
    step=0.0001,
    format="%.4f"       # show as integer
)

# pressure threshold for compute_profile detection
pressure_threshold = st.number_input(
    "Pressure Threshold (dBar) - profile detection", 
    min_value=0.10,
    max_value=10.00,
    value=0.45,
    step=0.10,
    format="%.2f"
)

# conductivity_treshold for compute_profile detection
conductivity_threshold = st.number_input(
    "Conductivity Threshold (mS/cm) - profile detection",
    min_value=0.01,
    max_value=10.99,
    value=5.00,
    step=0.10,
    format="%.2f"
)

process = st.button(
    "Process File",
    disabled=not (uploaded_file and site_id)
)


# ---- PROCESSING ----
if process:
    try:
        with st.spinner("Processing RSK/RBR file..."):
            with tempfile.TemporaryDirectory() as tmpdir:

                tmp_path = os.path.join(tmpdir, uploaded_file.name)
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_file.read())

                proc_data_dir = os.path.join(tmpdir, "proc_data")
                os.makedirs(proc_data_dir, exist_ok=True)

                files_to_process = rsksproc.export_profiles2rsk(
                    tmp_path, proc_data_dir
                )

                rsksproc.process_rsk_folder(
                    path_in=proc_data_dir,
                    list_of_rsk=files_to_process,
                    site_id=site_id,
                    patm=atmospheric_pressure,
                    p_tresh=pressure_threshold,
                    c_tresh=conductivity_threshold,
                    param=[
                        'conductivity',
                        'temperature',
                        'temperature1',
                        'dissolved_o2_concentration',
                        'par',
                        'ph',
                        'chlorophyll-a',
                        'fdom',
                        'turbidity',
                        'depth',
                        'salinity',
                        'density_anomaly'
                    ]
                )
                
                st.write("RBR profiles identified (/outputs contains the figures):", os.listdir(proc_data_dir))

                zip_path = os.path.join(tmpdir, "processed_output.zip")
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    # Walk recursively through proc_data
                    for root, dirs, files in os.walk(proc_data_dir):
                        for file in files:
                            full_path = os.path.join(root, file)
                            # Compute relative path for the zip so folder structure is preserved
                            arcname = os.path.relpath(full_path, os.path.dirname(proc_data_dir))
                            zipf.write(full_path, arcname=arcname)
                            # Optional: include empty directories
                        for dir_ in dirs:
                            dir_path = os.path.join(root, dir_)
                            if not os.listdir(dir_path):  # folder is empty
                                arcname = os.path.relpath(dir_path, os.path.dirname(proc_data_dir))
                                zipf.writestr(arcname + '/', '')

                with open(zip_path, "rb") as f:
                    st.download_button(
                        "Download Processed Output",
                        data=f,
                        file_name="processed_output.zip",
                        mime="application/zip"
                    )

        st.success("Processing complete!")

    except Exception as e:
        st.error(f"Error processing file: {e}")
