#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 14:53:22 2026

@author: epoirier

Script file name: streamlit_app.py
Author: Etienne Poirier, IRD, Plouzané
Date created: 2026-01-12
Last update: 2026-01-13
Description: code for streamlit page https://online-somlit-rbr-proc.streamlit.app/
"""

import streamlit as st
import tempfile
import zipfile
import os
import base64
import shutil

import RSKsomlit_proc as rsksproc

# function to deal with duplicate files given in upload widget
def deduplicate_by_filename(uploaded_files):
    """
    Keep only one file per filename.
    Returns unique files and discarded filenames.
    """
    seen_names = set()
    unique_files = []
    discarded = []

    for f in uploaded_files:
        if f.name in seen_names:
            discarded.append(f.name)
        else:
            seen_names.add(f.name)
            unique_files.append(f)

    return unique_files, discarded


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

# %%
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


# logo image, handle relative path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "image")

LOGO_1 = os.path.join(IMG_DIR, "logo_iuem_rz.jpg")
LOGO_2 = os.path.join(IMG_DIR, "logo_somlit.png")

# function to deal with the logo
def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

encoded_logo_1 = encode_image(LOGO_1)
encoded_logo_2 = encode_image(LOGO_2)


st.markdown(
    f"""
    <a href="https://www.iuem.univ-brest.fr" target="_blank">
        <img src="data:image/jpg;base64,{encoded_logo_1}" width="160">
    </a>
    <a href="https://www.somlit.fr" target="_blank">
        <img src="data:image/png;base64,{encoded_logo_2}" width="160">
    </a>
    """,
    unsafe_allow_html=True
)

# %%
# --- PRAMETERS ----

st.title("Somlit RSK/RBR Maestro File Processor")
st.write("Upload your RSK/RBR file()s and set processing parameters.")

# File uploader widget
uploaded_files_raw = st.file_uploader(
    "Upload RSK/RBR file(s)",
    type=["rsk"],
    accept_multiple_files=True
)

uploaded_files = []
discarded_files = []
# handle if duplicated filenames are selected by user
if uploaded_files_raw:
    uploaded_files, discarded_files = deduplicate_by_filename(uploaded_files_raw)

    if discarded_files:
        st.warning(
            "Duplicate filename(s) ignored:\n- " + "\n- ".join(discarded_files)
        )

# Processing parameters
if uploaded_files:
    st.markdown("---")
    st.subheader("Processing Parameters")
    
    # Site-ID dropdown with location of the Somlit station
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
        "Pressure Threshold (dbar) - profile detection", 
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
    # process button
    process = st.button(
        "Process File(s)",
        disabled=not (uploaded_files and site_id)
    )

# %%
# ---- PROCESSING CODE for single file then multiple files----
    if process:
        try:
            with st.spinner("Processing RSK/RBR file..."):
                with tempfile.TemporaryDirectory() as tmpdir:
                    
                    # create proc_data folder
                    proc_data_dir = os.path.join(tmpdir, "proc_data")
                    # Delete previous content if it exists
                    if os.path.exists(proc_data_dir):
                        shutil.rmtree(proc_data_dir)

                    # Recreate empty folder
                    os.makedirs(proc_data_dir, exist_ok=True)
                    
                    # Save all uploaded files to tmpdir
                    tmp_paths = []
                    for f in uploaded_files:
                        path = os.path.join(tmpdir, f.name)
                        with open(path, "wb") as out:
                            out.write(f.read())
                        tmp_paths.append(path)
                                        
                    # %%
                    # Smart processing based on number of files selected
                    # Starting with one file first
                    if len(uploaded_files) == 1: # if only one file selected
                        st.write("Single file selected. Using standard processing...")
                        # Call your normal processing function here
                        files_to_process = rsksproc.export_profiles2rsk(
                            tmp_paths[0], proc_data_dir
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
                        # writing the identified days with somlit profile
                        st.write("RBR profiles identified (/outputs contains the figures):", os.listdir(proc_data_dir))
                        # writing the ouptput                                                                                                                                                                                                                                                                                                                                                                                                                                                                
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
                        # more than one file selected
                        
                        # case with several files given by user
                        # %%
                    else:
                        st.write(f"{len(uploaded_files)} files selected. Using multi-file processing...")
                        # Call the special multi-file processing function here
                        
                        # first step processing, scanning for multiple days
                        files_to_process = rsksproc.scan_rsk(tmpdir)
                        
                        # second step processing of _YYYYMMDD.rsk files created above
                        rsksproc.process_rsk_folder(
                            path_in = proc_data_dir,
                            list_of_rsk = files_to_process,
                            site_id =5,
                            patm = 10.1325,
                            p_tresh = 0.4, #0.4 for multiple rsk // 0.05 for simple profile
                            c_tresh = 5, #5 for multiple rsk // 0.5 for simple profile
                            param = ['conductivity',
                                  'temperature',
                                  #'pressure',
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
                                  ] )
                        st.write("SOMLIT days identified _YYYYMMDD.rsk (/outputs contains profiles data and figures):", os.listdir(proc_data_dir))
                        # preparing the zip export
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
# %%
# Contact panel at the bottom
st.markdown(
    """
    <div style="
        background-color: rgba(0, 0, 0, 0.65); 
        color: white; 
        padding: 20px; 
        border-radius: 10px;
        max-width: 900px;
        margin: 50px auto 20px auto;  /* top margin pushes it down */
        text-align: center;
    ">
        <strong>Contact:</strong> Etienne Poirier (IRD - IUEM) &nbsp;|&nbsp;
        <a href='mailto:etienne.poirier@ird.fr' style='color:white;'>etienne.poirier@ird.fr</a> &nbsp;|&nbsp;
        <a href='https://github.com/epoirierIRD/Online_somlit_RBR_proc.github.io' target='_blank' style='color:white;'>GitHub</a>
    </div>
    """,
    unsafe_allow_html=True
)
