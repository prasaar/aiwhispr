echo "###List of python packages before install ####"
pip3 list 


echo "Running pip3 and python commands"
echo "pip3 install -U pip setuptools wheel"
pip3 install -U pip setuptools wheel
echo "pip3 install -U spacy"
pip3 install -U spacy
echo "python3 -m spacy download en_core_web_sm"
python3 -m spacy download en_core_web_sm
echo "pip3 install spacy-language-detection"
pip3 install spacy-language-detection
echo "pip3 install -U sentence-transformers"
pip3 install -U sentence-transformers
echo "pip3 install typesense"
pip3 install typesense
echo "pip3 install azure-storage-blob" 
pip3 install azure-storage-blob 
echo "pip3 install azure-identity"
pip3 install azure-identity
echo "pip3 install boto3"
pip3 install boto3 
echo "pip3 install pytest-shutil"
pip3 install pytest-shutil
echo "pip3 install pypdf"
pip3 install pypdf
echo "pip3 install textract"
pip3 install textract
echo "pip3 install flask"
pip3 install flask
echo "pip3 install uwsgi"
pip3 install uwsgi
echo "pip3 install qdrant-client"
pip3 install qdrant-client
echo "pip3 install weaviate-client"
pip3 install weaviate-client
echo "pip3 install --upgrade google-cloud-storage"
pip3 install --upgrade google-cloud-storage

echo "###List of python packages after install ####"
pip3 list 

