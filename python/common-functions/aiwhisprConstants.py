#List of of all file extensions[document types] that the app will read, extract text and then encode using LLM
FILEXTNLIST = ['.txt', '.csv', '.pdf', '.xlsx', '.docx', '.pptx']

TXTCHUNKSIZE = 700
S3MAXKEYS=1000   #MAXIMUM ALLOWED VALUE IS 1000
BUFFERSIZEFORCOPY = 1024*1024*100

# This is a dictionary that maps the file suffix to the moduleName that can process the document
# Edit this when you add a module to handle a new document type (.suffix)
# The python module is loaded dynamically
DOCPROCESSORMODULES={
    '.txt': 'aiwhisprTextDocProcessor',
    '.csv': 'aiwhisprTextDocProcessor',
    '.py': 'aiwhisprTextDocProcessor',
    '.js': 'aiwhisprTextDocProcessor',
    '.php': 'aiwhisprTextDocProcessor',
    '.sh': 'aiwhisprTextDocProcessor',
    '.c': 'aiwhisprTextDocProcessor',
    '.pl':'aiwhisprTextDocProcessor',
    '.cpp':'aiwhisprTextDocProcessor',
    '.cs':'aiwhisprTextDocProcessor',
    '.h':'aiwhisprTextDocProcessor',
    '.java':'aiwhisprTextDocProcessor',
    '.swift':'aiwhisprTextDocProcessor',
    '.pdf':'aiwhisprPdfDocProcessor',
    '.docx':'aiwhisprMSdocxDocProcessor',
    '.xlsx':'aiwhisprMSxlsxDocProcessor',
    '.pptx':'aiwhisprMSpptxDocProcessor'
}

#A list of all text file extension types. We will not do an extractText operation on them.
#TXTFILEXTN = ['.txt', '.csv', '.py', '.js', '.php' , '.sh', '.c' , '.pl', '.cpp', '.cs', '.h', '.java', '.swift']
