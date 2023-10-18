import streamlit as st
import os
from PIL import Image
import multiprocessing as mp
import json

# get the value of the PATH environment variable
try:
    aiwhispr_home = os.environ['AIWHISPR_HOME']
except:
    print("Could not read environment variable AIWHISPR_HOME, exiting....")
else:

    image = Image.open(os.path.join(aiwhispr_home, 'python','streamlit', 'static', 'step3.png'))
    st.image(image)
    st.header('AIWhispr - LLM Service Configuration for vector embeddings')
  
    if 'select_llm_idx' not in st.session_state:
        st.session_state.select_llm_idx = 0
    
    if 'select_llm_model_name_idx' not in st.session_state:
        st.session_state.select_llm_model_name_idx = 0
    
    if 'llmServiceModule' not in st.session_state:
        st.session_state.llmServiceModule = ""
    
    if 'model_family' not in st.session_state:
        st.session_state.model_family = ""

    if 'model_name' not in st.session_state:
        st.session_state.model_name = ""
    
    if 'llm_service_api_key' not in st.session_state:
        st.session_state.llm_service_api_key = ""

    if 'working_dir' not in st.session_state:
        st.session_state.working_dir = ""
    
    if 'index_dir' not in st.session_state:
        st.session_state.index_dir = ""
    
    if 'indexing_processes' not in st.session_state:
        st.session_state.indexing_processes = ""
    

    col5,col6 = st.columns(2)
    #### Column 5(Page3) ####
    # Select the LLM Service
    add_selectbox_llm_service = col5.selectbox(
        label = 'Select the LLM Service',
        options = ('S-Bert', 'OpenAI'),
        index = st.session_state.select_llm_idx
    )

    if add_selectbox_llm_service == 'S-Bert':
        st.session_state.llmServiceModule = "libSbertLlmService"
        st.session_state.model_family = "sbert"
        st.session_state.llm_service_api_key = ""
        st.session_state.select_llm_idx = 0
    
        

    if add_selectbox_llm_service == 'OpenAI':
        st.session_state.llmServiceModule = "openaiLlmService"
        st.session_state.model_family = "openai"
        st.session_state.select_llm_idx = 1
    
    #Select the Model Name
    modellistfiename=add_selectbox_llm_service + '.models.json'
    modellistfilepath=os.path.join(aiwhispr_home,'python','streamlit','app-config','llm',modellistfiename)
    model_names = []
    f=open(modellistfilepath)
    models_list=json.load(f)
    for model in models_list['models']:
        model_names.append(model['name'])
    f.close()

    
    add_selectbox_model_name = col5.selectbox(  #then show options for selecting the model name
        label = 'Select the Model',
        options = model_names,
        index = st.session_state.select_llm_model_name_idx
    )
    
    modelname=add_selectbox_model_name
     #Now write the model details in the second column
    f=open(modellistfilepath)
    models_list=json.load(f)
    model_dimensions=0
    for model in models_list['models']:
        if modelname == model['name']:
            col5.json(model,expanded=False)
            model_dimensions=model['dimensions']
            model_max_sequence_length=model['max_sequence_length']
    if int(st.session_state.vector_dim) != model_dimensions:
        col5.write("ERROR: Vector Dimensions mismatch for this model. Please review the vector dimension configured in your vector database configuration")
    f.close()

    #Set the text chunk size
    chunksize=0.8*int(model_max_sequence_length)
    col5.text_input("Text Chunk Size", value=str(int(chunksize)), key="text_chunk_size_in")
    st.session_state.text_chunk_size = st.session_state.text_chunk_size_in

    #col5.text_input("Model Name", value=modelname, key="model_name_in")
    #st.session_state.model_name = st.session_state.model_name_in
    st.session_state.model_name = modelname

    if st.session_state.llmServiceModule == "openaiLlmService":
        col5.text_input("Open AI Key", value="", key="llm_service_api_key_in")
        st.session_state.llm_service_api_key = st.session_state.llm_service_api_key_in

    col5.text_input("Working Directory in which extracted text is stored",value='/tmp', key="working_dir_in")
    st.session_state.working_dir = st.session_state.working_dir_in

    col5.text_input("Index Directory in which local indices are stored",value='/tmp', key="index_dir_in")
    st.session_state.index_dir = st.session_state.index_dir_in

    col5.text_input("Number of parallel indexing processes, this should be 1 or below the total number of CPU",value="1", key="indexing_processes_in")
    st.session_state.indexing_processes = st.session_state.indexing_processes_in


    
    if st.button(label="Use This LLM Service Config", key="review_llm_service_btn", help="Click to review config"):
        st.session_state.llm_config = "[llm-service]\n"
        st.session_state.local_config = "[local]\n"

        if st.session_state.llmServiceModule == None or len(st.session_state.llmServiceModule) == 0:
            st.write("ERROR: could not configure llmServiceModule")
        else:
            st.session_state.llm_config = st.session_state.llm_config + "llmServiceModule=" + st.session_state.llmServiceModule + "\n"
        
        if st.session_state.model_family == None or len(st.session_state.model_family) == 0:
            st.write("ERROR: could not configure Model Family")
        else:
            st.session_state.llm_config = st.session_state.llm_config + "model-family=" + st.session_state.model_family + "\n"
        
        if st.session_state.model_name == None or len(st.session_state.model_name) == 0:
            st.write("ERROR: could not configure Model Name")
        else:
            st.session_state.llm_config = st.session_state.llm_config + "model-name=" + st.session_state.model_name + "\n"

        if st.session_state.llmServiceModule != "libSbertLlmService" and ( st.session_state.llm_service_api_key == None or len(st.session_state.llm_service_api_key) == 0):
            st.write("ERROR: could not configure LLM Service API Key")
        else:
            st.session_state.llm_config = st.session_state.llm_config + "llm-service-api-key=" + st.session_state.llm_service_api_key + "\n"

        if st.session_state.text_chunk_size == None or len(st.session_state.text_chunk_size) == 0:
            st.write("ERROR: could not configure chunk-size")
        else:
            st.session_state.llm_config = st.session_state.llm_config + "chunk-size=" + st.session_state.text_chunk_size + "\n"


        if st.session_state.working_dir == None or len(st.session_state.working_dir)==0:
            st.write("ERROR: could not configure working_dir")
        else:
            st.session_state.local_config = st.session_state.local_config + "working-dir=" + st.session_state.working_dir + "\n"

        if st.session_state.index_dir == None or len(st.session_state.index_dir)==0:
            st.write("ERROR: could not configure index_dir")
        else:
            st.session_state.local_config = st.session_state.local_config + "index-dir=" + st.session_state.index_dir + "\n"

        if st.session_state.indexing_processes == None or len(st.session_state.indexing_processes)==0:
            st.write("ERROR: could not configure indexing_processes")
        else:
            st.session_state.local_config = st.session_state.local_config + "indexing-processes=" + st.session_state.indexing_processes + "\n"

        for i in st.session_state.content_site_config.splitlines():
            st.write(i.rstrip())
        for i in st.session_state.site_auth_config.splitlines():
            st.write(i.rstrip())
        for i in st.session_state.vectordb_config.splitlines():
            st.write(i.rstrip())
        for i in st.session_state.llm_config.splitlines():
            st.write(i.rstrip())
        for i in st.session_state.local_config.splitlines():
            st.write(i.rstrip())
        

        st.write("########################################")
        st.write("    ################################    ")
        
        config_filename=st.session_state.sitename + '.cfg'
        config_filepath=os.path.join(aiwhispr_home,'config','content-site','sites-available',config_filename)
        st.write("Config file will be saved in")
        st.write(config_filepath)
        write_file_flag=False

        if os.path.isfile(config_filepath):
                write_file_flag=False
                st.write("ERROR: A config already exists. We cannot overwrite. Try changing the sitename in the first page")
        else:
            write_file_flag=True
            
        if write_file_flag == True:
            f = open(config_filepath, "w")
            for i in st.session_state.content_site_config.splitlines():
                f.write(i+"\n")
            for i in st.session_state.site_auth_config.splitlines():
                f.write(i+"\n")
            for i in st.session_state.vectordb_config.splitlines():
                f.write(i+"\n")
            for i in st.session_state.llm_config.splitlines():
                f.write(i+"\n")
            for i in st.session_state.local_config.splitlines():
                f.write(i+"\n")
            f.close()
            st.write("Config file now saved in " + config_filepath)
            st.session_state.config_filepath=config_filepath


        


    

    
