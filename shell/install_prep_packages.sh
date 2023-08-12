echo "Running pip3 and python command"s
echo "pip3 install -U pip setuptools wheel"
pip3 install -U pip setuptools wheel
echo "pip3 install -U spacy"
pip3 install -U spacy
echo "python -m spacy download en_core_web_sm"
python -m spacy download en_core_web_sm
echo "pip3 install spacy-language-detection"
pip3 install spacy-language-detection
echo "pip3 install -U sentence-transformers"
pip3 install -U sentence-transformers
