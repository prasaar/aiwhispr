import streamlit as st
import os
from PIL import Image
import subprocess


# get the value of the PATH environment variable
try:
    aiwhispr_home = os.environ['AIWHISPR_HOME']
except:
    print("Could not read environment variable AIWHISPR_HOME, exiting....")
    st.write("Could not read environment variable AIWHISPR_HOME, exiting....")
else:
    full_cmd = ""
    if ('config_filepath' in st.session_state) and  ( len(st.session_state.config_filepath) > 0 ) and ( os.path.isfile(st.session_state.config_filepath) == True ) :
        set_log_level_cmd="AIWHISPR_LOG_LEVEL=INFO; export AIWHISPR_LOG_LEVEL;"
        program_cmd='python3' + ' ' +  os.path.join(aiwhispr_home,"python","common-functions", "test_content_site_connection.py") + ' ' + '-C ' + st.session_state.config_filepath
        full_cmd = set_log_level_cmd + program_cmd
    else:
        st.write("ERROR: Please check if configuration file was created.")

    if len(full_cmd) > 0:
        st.write("Testing the configuration file")
        st.write(st.session_state.config_filepath)    
        if st.button(label="Test Configfile", key="test_config_btn", help="Click to test config", type="primary"):
            st.write("########################################")
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
            res_stdout = result.stdout
            res_stderr = result.stderr
            for i in res_stdout.splitlines():
                st.write(i + '\n')

            st.write("### LOGS ###")
            error_strings = []
            for i in res_stderr.splitlines():
                if ( i.find('] ERROR [') != -1):
                    error_strings.append(i)
                st.write(i + '\n')
            
            if len(error_strings) == 0:
                st.write('### NO ERRORS ###')
            else:
                st.write('### ERRORS ###')
                for i in error_strings:
                    st.write(i + '\n')
            

        
