import streamlit as st
import os
from PIL import Image
import random
import string

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

# get the value of the PATH environment variable
try:
    aiwhispr_home = os.environ['AIWHISPR_HOME']
except:
    print("Could not read environment variable AIWHISPR_HOME, exiting....")
else:
    image = Image.open(os.path.join(aiwhispr_home, 'python','streamlit', 'static', 'step2.png'))
    st.image(image)
    st.header('AIWhispr - Vector Database Configuration')
    st.sidebar.markdown("# Configure Vector Database Access")
    st.sidebar.markdown("This is the vector database which will be used to store the vector embeddings and the text extract")

    if 'select_vectordb_idx' not in st.session_state:
        st.session_state.select_vectordb_idx = 0

    if 'vectorDbModule' not in st.session_state:
        st.session_state.vectorDbModule = ""
    
    if 'api_address' not in st.session_state:
        st.session_state.api_address = ""
    
    if 'api_port' not in st.session_state:
        st.session_state.api_port = ""

    if 'vector_dim' not in st.session_state:
        st.session_state.vector_dim = ""
    
    if 'collection_name' not in st.session_state:
        st.session_state.collection_name = ""
 
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""

    if 'user_id' not in st.session_state:
        st.session_state.user_id = ""
    
    if 'user_pwd' not in st.session_state:
        st.session_state.user_pwd = ""
    

    
    col3,col4 = st.columns(2)
    
    #### Column 3(Page2) ####
    # Select the Vector Db
    add_selectbox_vector_db = col3.selectbox(
        label = 'Select the Vector Database',
        options = ('Typesense', 'Qdrant', 'Weaviate', 'Milvus'),
        index = st.session_state.select_vectordb_idx
    )
    if add_selectbox_vector_db == 'Typesense':
        st.session_state.vectorDbModule = 'typesenseVectorDb'
        hostaddress="0.0.0.0"
        hostport="8108"
        st.session_state.select_vectordb_idx = 0
    elif add_selectbox_vector_db == 'Qdrant':
        st.session_state.vectorDbModule = 'qdrantVectorDb'
        hostaddress="127.0.0.1"
        hostport="6333"
        st.session_state.select_vectordb_idx = 1
    elif add_selectbox_vector_db == 'Weaviate':
        st.session_state.vectorDbModule = 'weaviateVectorDb'
        hostaddress="127.0.0.1"
        hostport="8080"
        st.session_state.select_vectordb_idx = 2
    elif add_selectbox_vector_db == 'Milvus':
        st.session_state.vectorDbModule = 'milvusVectorDb'
        hostaddress="localhost"
        hostport="19530"
        st.session_state.select_vectordb_idx = 3
    
    col3.text_input("VectorDb IP Address/Hostname",value=hostaddress, key="api_address_in")
    # You can access the value at any point with:
    st.session_state.api_address = st.session_state.api_address_in
    
    #Api Port
    col3.text_input("VectorDb Port Number", value=hostport, key="api_port_in")
    # You can access the value at any point with:
    st.session_state.api_port = st.session_state.api_port_in

    #Vector Dimension
    if len(st.session_state.vector_dim) == 0:
        vectordim = "768"
    else:
        vectordim=st.session_state.vector_dim

    col3.text_input("Vector Dimension e.g. for SBert 768, for OpenAI 1536",value=vectordim, key="vector_dim_in")
    # You can access the value at any point with:
    st.session_state.vector_dim = st.session_state.vector_dim_in

    #Collection Name
    if len(st.session_state.collection_name)==0:
    #    collname="aiWhisprContentChunkMap"
        collname="aiWhisprChunkMap" +  get_random_string(9)
    else:
        collname=st.session_state.collection_name

    col3.text_input("Collection Name",value=collname, max_chars=27, key="collection_name_in")
    # You can access the value at any point with:
    st.session_state.collection_name = st.session_state.collection_name_in
    #Col4 Page2
    if st.session_state.vectorDbModule == 'typesenseVectorDb' or st.session_state.vectorDbModule == 'qdrantVectorDb' or st.session_state.vectorDbModule == 'weaviateVectorDb':
        col4.text_input("VectorDb API Key",value=st.session_state.api_key,key="api_key_in")
        st.session_state.api_key = st.session_state.api_key_in
    
    if st.session_state.vectorDbModule == 'milvusVectorDb':
        col4.text_input("VectorDb UserId",value=st.session_state.user_id,key="user_id_in")
        st.session_state.user_id = st.session_state.user_id_in
        col4.text_input("VectorDb Password",value=st.session_state.user_pwd,key="user_pwd_in")
        st.session_state.user_pwd = st.session_state.user_pwd_in
            
        
if st.button(label="Use This Vector Db Config", key="review_vector_db_btn", help="Click to review config"):

    st.session_state.vectordb_config = "[vectordb]\n"
    if st.session_state.vectorDbModule == None or len(st.session_state.vectorDbModule) == 0:
        st.write("ERROR: vectorDbModule not provided") 
    else:
        st.session_state.vectordb_config = st.session_state.vectordb_config + "vectorDbModule=" + st.session_state.vectorDbModule + "\n"
    
    if st.session_state.api_address == None or len(st.session_state.api_address) == 0:
        st.write("ERROR: VectorDB Host IP not provided") 
    else:
        st.session_state.vectordb_config = st.session_state.vectordb_config + "api-address=" + st.session_state.api_address + "\n"
    
    if st.session_state.api_port == None or len(st.session_state.api_port) == 0:
        st.write("ERROR: VectorDB Port Number not provided") 
    else:
        st.session_state.vectordb_config = st.session_state.vectordb_config + "api-port=" + st.session_state.api_port + "\n"
    
    if st.session_state.vector_dim == None or len(st.session_state.vector_dim) == 0:
        st.write("ERROR: Vector Dimension not provided") 
    else:
        st.session_state.vectordb_config = st.session_state.vectordb_config + "vector-dim=" + st.session_state.vector_dim + "\n"
    
    if st.session_state.collection_name == None or len(st.session_state.collection_name) == 0:
        st.write("ERROR: Collection Name not provided") 
    else:
        st.session_state.vectordb_config = st.session_state.vectordb_config + "collection-name=" + st.session_state.collection_name + "\n"
    
    if st.session_state.vectorDbModule == 'typesenseVectorDb':
        if st.session_state.api_key == None or len(st.session_state.api_key) == 0:
            st.write("ERROR: API Key not provided") 
        else:
            st.session_state.vectordb_config = st.session_state.vectordb_config + "api-key=" + st.session_state.api_key + "\n"
    
    if st.session_state.vectorDbModule == 'qdrantVectorDb' or st.session_state.vectorDbModule == 'weaviateVectorDb':
        if st.session_state.api_key == None or len(st.session_state.api_key) == 0:
            st.write("WARNING: API Key not provided") 
            st.session_state.vectordb_config = st.session_state.vectordb_config + "api-key=" + st.session_state.api_key + "\n"
        else:
            st.session_state.vectordb_config = st.session_state.vectordb_config + "api-key=" + st.session_state.api_key + "\n"
    
    if st.session_state.vectorDbModule == 'milvusVectorDb':
        if st.session_state.user_id == None or  len(st.session_state.user_id) == 0:
            st.write("ERROR: User ID not provided")
        else:
            st.session_state.vectordb_config = st.session_state.vectordb_config + "user=" + st.session_state.user_id + "\n"
        
        if st.session_state.user_pwd == None or  len(st.session_state.user_pwd) == 0:
            st.write("ERROR: Password not provided")
        else:
            st.session_state.vectordb_config = st.session_state.vectordb_config + "password=" + st.session_state.user_pwd + "\n"
        

    for i in st.session_state.content_site_config.splitlines():
        st.write(i.rstrip())
    for i in st.session_state.site_auth_config.splitlines():
        st.write(i.rstrip())
    for i in st.session_state.vectordb_config.splitlines():
        st.write(i.rstrip())
