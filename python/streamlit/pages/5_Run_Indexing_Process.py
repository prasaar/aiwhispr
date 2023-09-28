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
        program_cmd='python3' + ' ' +  os.path.join(aiwhispr_home,"python","common-functions", "index_content_site.py") + ' ' + '-C ' + st.session_state.config_filepath
        full_cmd = set_log_level_cmd + program_cmd
    else:
        st.write("ERROR: Please check if configuration file was created.")

    if len(full_cmd) > 0:
        st.write("Start indexing process with the configuration file")
        st.write(st.session_state.config_filepath)
        p_logfilepath = os.path.join(st.session_state.working_dir,st.session_state.sitename + '.streamlit.log')
        if 'indexing_started_flag' not in st.session_state:
            st.session_state.indexing_started_flag=False  
        elif st.session_state.indexing_started_flag==True:
            st.write("Looks like Indexing process has been started. Please monitor the log file")
            st.write(p_logfilepath)
            

        if st.button(label="Start Indexing", key="run_indexing_btn", help="Click to run indexing", type="primary", disabled=st.session_state.indexing_started_flag):
            st.write("#### Please do not navigate away. ###")
            st.write("#### This takes approximately 15 minutes to create vector embeddings for 2000 files. ####")
            st.write("########################################")
            fwrite_in_this_process_flag= False
            if st.session_state.indexing_started_flag == False: ##If this is the first time
                fwrite=open(p_logfilepath,"w")
                p = subprocess.Popen(full_cmd, shell=True, stdout=fwrite, stderr=fwrite, text=True)
                fwrite_in_this_process_flag= True

            fread=open(p_logfilepath,"r")
            error_strings = []
            dummy_counter=0
            while p.poll() == None:
                st.session_state.indexing_started_flag=True
                st.write("########################################")
                st.write("Streamlit polling the process log file")
                st.write("########################################")
                try:
                    p.communicate(timeout=15)
                    for line in fread:
                        st.write(line + '\n')
                        if ( line.find('] ERROR [') != -1):
                            error_strings.append(line)
                
                except subprocess.TimeoutExpired:
                    for line in fread:
                        st.write(line + '\n')
                        if ( line.find('] ERROR [') != -1):
                            error_strings.append(line)

                        
            if len(error_strings) == 0:
                st.write('### NO ERRORS ###')
            else:
                st.write('### ERRORS ###')
                for i in error_strings:
                    st.write(i + '\n')

            st.session_state.indexing_started_flag=False
            fread.close()
            if fwrite_in_this_process_flag == True:
                fwrite.close()
