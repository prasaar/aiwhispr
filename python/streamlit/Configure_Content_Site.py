import streamlit as st
import os
from PIL import Image
from io import StringIO
import random

# get the value of the PATH environment variable
try:
    aiwhispr_home = os.environ['AIWHISPR_HOME']
except:
    print("Could not read environment variable AIWHISPR_HOME, exiting....")
else:
    image = Image.open(os.path.join(aiwhispr_home, 'python','streamlit', 'static', 'step1.png'))
    st.image(image)
    st.header('AIWhispr - Content Site Configuration')
    if 'sitename' not in st.session_state:
        st.session_state.sitename = ""
    
    if 'select_srctype_idx' not in st.session_state:
        st.session_state.select_srctype_idx = 3

    if 'srctype' not in st.session_state:
        st.session_state.srctype = ""
    
    if 'srcpath' not in st.session_state:
        st.session_state.srcpath = ""
    
    if 'displaypath' not in st.session_state:
        st.session_state.displaypath = ""

    if 'contentSiteModule' not in st.session_state:
        st.session_state.contentSiteModule = ""

    if 'authtype' not in st.session_state:
        st.session_state.authtype = ""

    if 'aws_access_key_id' not in st.session_state:
        st.session_state.aws_access_key_id = ""
    
    if 'aws_secret_access_key' not in st.session_state:
        st.session_state.aws_secret_access_key = ""
    
    if 'select_azureauthtype_idx' not in st.session_state:
        st.session_state.select_azureauthtype_idx = 0

    if 'key' not in st.session_state:
        st.session_state.key = ""

    if 'sastoken' not in st.session_state:
        st.session_state.sastoken = ""
    
    if 'google_project_id' not in st.session_state:
        st.session_state.google_project_id = ""
    
    if 'google_storage_api_key' not in st.session_state:
        st.session_state.google_storage_api_key = ""

    
    col1, col2 = st.columns(2)
    st.sidebar.markdown("# Configure Content Site.")
    st.sidebar.markdown("This is the storage location of your files")
    
    #### Column 1 ####
    #Sitename
    if len(st.session_state.sitename) == 0:
        this_sitename = 'testsite' + str( random.randint(1, 9999) )
    else:
        this_sitename = st.session_state.sitename
    col1.text_input("Enter a unique name for this configuration", value=this_sitename, key="sitename_in")
    # You can access the value at any point with:
    st.session_state.sitename = st.session_state.sitename_in
    

    # Select the Content Storage
    add_selectbox_content_site = col1.selectbox(
        label = 'Select the storage type from which files will be read',
        options = ('AWS S3', 'Azure Blob', 'Google Cloud Storage', 'Local Directory path'),
        index = st.session_state.select_srctype_idx
    )
    if add_selectbox_content_site == 'AWS S3':
        st.session_state.srctype = 's3'
        st.session_state.contentSiteModule = 'awsS3ContentSite'
        st.session_state.select_srctype_idx = 0
    elif add_selectbox_content_site == 'Azure Blob':
        st.session_state.srctype = 'azureblob'
        st.session_state.contentSiteModule = 'azureContentSite'
        st.session_state.select_srctype_idx = 1
    elif add_selectbox_content_site == 'Google Cloud Storage':
        st.session_state.srctype = 'google-cloud'
        st.session_state.contentSiteModule = 'googleContentSite'
        st.session_state.select_srctype_idx = 2
    elif add_selectbox_content_site == 'Local Directory path':
        st.session_state.srctype = 'filepath'
        st.session_state.contentSiteModule = 'filepathContentSite'
        st.session_state.select_srctype_idx = 3

    #Get the path
    if st.session_state.srctype == 's3':
        col1.text_input('Path to S3 Bucket e.g. s3://mybucket',value=st.session_state.srcpath, key="srcpath_in")
        st.session_state.srcpath = st.session_state.srcpath_in
    if st.session_state.srctype == 'azureblob':
        col1.text_input('Path to Blob Container e.g. https://<storage>.blob.core.windows.net/<container>',value=st.session_state.srcpath, key="srcpath_in")
        st.session_state.srcpath = st.session_state.srcpath_in
    if st.session_state.srctype == 'google-cloud':
        col1.text_input('Path to Google Storage e.g. gs://<storage>',value=st.session_state.srcpath, key="srcpath_in")
        st.session_state.srcpath = st.session_state.srcpath_in
    if st.session_state.srctype == 'filepath':
        if len(st.session_state.srcpath)==0:
            topdir=os.path.join(aiwhispr_home,'examples','http','bbc')
        else:
            topdir=st.session_state.srcpath

        col1.text_input('Full path to top directory e.g. /Users/myname/myfiles',value=topdir, key="srcpath_in")
        st.session_state.srcpath = st.session_state.srcpath_in

    #Get the displaypath
    if len(st.session_state.displaypath)==0:
        if st.session_state.srctype == 'filepath':
            displayprefix='http://localhost:9100/bbc/'
        else:
            displayprefix=""
    else:
        displayprefix=st.session_state.displaypath

    col1.text_input('Prefix path to display link to the file e.g. http://localhost/myfiles',value=displayprefix, key="displaypath_in")
    st.session_state.displaypath = st.session_state.displaypath_in

    #Set the authtype
    
    if st.session_state.srctype == 's3':
        add_selectbox_aws_auth_type = col1.selectbox(
        'Select the type of authentication for Azure',
        ('AWS Key', 'AWS Unsigned Access')
        )
        if add_selectbox_aws_auth_type == 'AWS Key':
            st.session_state.authtype = 'aws-key'
        elif add_selectbox_aws_auth_type == 'AWS Unsigned Access':
            st.session_state.authtype = 'aws-key-unsigned'
    
    if st.session_state.srctype == 'azureblob':
        add_selectbox_azure_auth_type = col1.selectbox(
        label = 'Select the type of authentication for Azure',
        options = ('Azure Storage Key', 'Azure SAS Token'),
        index = st.session_state.select_azureauthtype_idx
        )

        if add_selectbox_azure_auth_type == 'Azure Storage Key':
            st.session_state.authtype = 'az-storage-key'
            st.session_state.select_azureauthtype_idx = 0
        elif add_selectbox_azure_auth_type == 'Azure SAS Token':
            st.session_state.authtype = 'sas'
            st.session_state.select_azureauthtype_idx = 1
    
    if st.session_state.srctype == 'google-cloud':
        st.session_state.authtype = 'google-cred-key'

    if st.session_state.srctype == 'filepath':
        st.session_state.authtype = 'filechecks'
    
    
    #### Column 2 : Authentication keys ####
    if st.session_state.srctype == 's3' and st.session_state.authtype == 'aws-key':
        col2.text_input("Configure AWS KEY",value=st.session_state.aws_access_key_id, key="aws_key_in")
        st.session_state.aws_access_key_id = st.session_state.aws_key_in
        col2.text_input("Configure AWS SECRET",value=st.session_state.aws_secret_access_key, key="aws_secret_in")
        st.session_state.aws_secret_access_key = st.session_state.aws_secret_in

    if st.session_state.srctype == 's3' and st.session_state.authtype == 'aws-key-unsigned':
        st.session_state.authtype = 'aws-key'  ##Reset to what's required in config file
        st.session_state.aws_access_key_id = 'UNSIGNED'
        st.session_state.aws_secret_access_key = 'UNSIGNED'


    if st.session_state.srctype == 'azureblob' and st.session_state.authtype == 'az-storage-key':
        col2.text_input("Configure Azure Key",value=st.session_state.key, key="key_input")
        st.session_state.key = st.session_state.key_input

    if st.session_state.srctype == 'azureblob' and st.session_state.authtype == 'sas':
        col2.text_input("Configure Azure SAS Token",value=st.session_state.sastoken, key="sastoken_in")
        st.session_state.sastoken = st.session_state.sastoken_in

    if st.session_state.srctype == 'google-cloud' and st.session_state.authtype == 'google-cred-key':
        col2.text_input("Configure Google Project Id",value=st.session_state.google_project_id, key="google_project_id_in")
        st.session_state.google_project_id = st.session_state.google_project_id_in
        col2.text_input("Configure Google Storage API Key",value=st.session_state.google_storage_api_key, key="google_storage_api_key_in")
        st.session_state.google_storage_api_key = st.session_state.google_storage_api_key_in
        uploaded_file = col2.file_uploader("Upload Credential Json")
        if uploaded_file is not None:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            string_data = stringio.read()
            st.write(string_data)
            st.session_state.google_cred_path = os.path.join(aiwhispr_home,'config', 'content-site', 'sites-available',st.session_state.sitename + '.google_cred.json')
            cred_file = open(st.session_state.google_cred_path, "w")
            cred_file.write(string_data)
            cred_file.close()

            
    if st.session_state.srctype == 'filepath' and st.session_state.authtype == 'filechecks':
        col2.checkbox(label="Check read permission for each file", value=True, key="check_file_permission_in")
        if st.session_state.check_file_permission_in == True:
            st.session_state.check_file_permission = 'Y'
        else:
            st.session_state.check_file_permission = 'N'

        
if st.button(label="Use This Content Site Config", key="review_content_site_btn", help="Click to review config"):

    st.session_state.content_site_config = "[content-site]\n"
    if st.session_state.sitename == None or len(st.session_state.sitename) == 0:
        st.write("ERROR: Sitename not provided") 
    else:
        st.session_state.content_site_config = st.session_state.content_site_config + "sitename=" + st.session_state.sitename + "\n"
    
    if st.session_state.srctype == None or len(st.session_state.srctype) == 0:
        st.write("ERROR: Storage type from which files will be read is not provided") 
    else:
        st.session_state.content_site_config = st.session_state.content_site_config + "srctype=" + st.session_state.srctype + "\n"

    if st.session_state.srcpath == None or len(st.session_state.srcpath) == 0:
        st.write("ERROR: Path from which files will be read is not provided") 
    else:
        st.session_state.content_site_config = st.session_state.content_site_config + "srcpath=" + st.session_state.srcpath + "\n"

    if st.session_state.displaypath == None or len(st.session_state.displaypath) == 0:
        st.write("ERROR: Prefix Path for search results is not provided") 
    else:
        st.session_state.content_site_config = st.session_state.content_site_config + "displaypath=" + st.session_state.displaypath + "\n"

    if st.session_state.contentSiteModule == None or len(st.session_state.contentSiteModule) == 0:
        st.write("ERROR: could not set contentSiteModule configuration") 
    else:
        st.session_state.content_site_config = st.session_state.content_site_config + "contentSiteModule=" + st.session_state.contentSiteModule + "\n"


    st.session_state.site_auth_config = "[content-site-auth]\n"
    if st.session_state.authtype == None or len(st.session_state.authtype)==0:
        st.write("ERROR:authtype not configured")
    else:
        st.session_state.site_auth_config = st.session_state.site_auth_config + "authtype=" + st.session_state.authtype + "\n"
    
    if st.session_state.srctype == "s3" and st.session_state.authtype == "aws-key":
        if st.session_state.aws_access_key_id == None or len(st.session_state.aws_access_key_id) == 0:
            st.write("ERROR: AWS KEY is not provided")
        elif st.session_state.aws_secret_access_key == None or len(st.session_state.aws_secret_access_key) == 0:
            st.write("ERROR: AWS SECRET is not provided")
        else:
            st.session_state.site_auth_config = st.session_state.site_auth_config + "aws-access-key-id=" + st.session_state.aws_access_key_id + "\n"
            st.session_state.site_auth_config = st.session_state.site_auth_config + "aws-secret-access-key=" + st.session_state.aws_secret_access_key + "\n"
            
    if st.session_state.srctype == "azureblob" and st.session_state.authtype == "az-storage-key":
        if st.session_state.key == None or len(st.session_state.key) == 0:
            st.write("ERROR: Azure Storage Key not provided")
        else:
            st.session_state.site_auth_config = st.session_state.site_auth_config + "key=" + st.session_state.key + "\n"

    if st.session_state.srctype == "azureblob" and st.session_state.authtype == "sas":
        if st.session_state.sastoken == None or len(st.session_state.sastoken) == 0:
            st.write("ERROR: Azure SAS Token not provided")
        else:
            st.session_state.site_auth_config = st.session_state.site_auth_config + "sastoken=" + st.session_state.sastoken + "\n"

    if st.session_state.srctype == "filepath" and st.session_state.authtype == "filechecks":
        if st.session_state.check_file_permission == None or len(st.session_state.check_file_permission) == 0:
            st.write("ERROR: check file permission config is missing")
        else:
            st.session_state.site_auth_config = st.session_state.site_auth_config + "check-file-permission=" + st.session_state.check_file_permission + "\n"

    if st.session_state.srctype == "google-cloud" and st.session_state.authtype == "google-cred-key":
        if st.session_state.google_project_id == None or len(st.session_state.google_project_id) == 0:
            st.write("ERROR: Google Project ID is not provided")
        else:
            st.session_state.site_auth_config = st.session_state.site_auth_config + "google-project-id=" + st.session_state.google_project_id + "\n"
        
        if st.session_state.google_storage_api_key == None or len(st.session_state.google_storage_api_key) == 0:
            st.write("ERROR: Google Storage API Key is not provided")
        else:
            st.session_state.site_auth_config = st.session_state.site_auth_config + "google-storage-api-key=" + st.session_state.google_storage_api_key + "\n"
        
        if st.session_state.google_cred_path == None or len(st.session_state.google_cred_path) == 0:
            st.write("ERROR: Google Cred Path is not provided")
        else:
            st.session_state.site_auth_config = st.session_state.site_auth_config + "google-cred-path=" + st.session_state.google_cred_path + "\n"
        


    for i in st.session_state.content_site_config.splitlines():
        st.write(i.rstrip())
    for i in st.session_state.site_auth_config.splitlines():
        st.write(i.rstrip())