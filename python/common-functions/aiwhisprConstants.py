
#FILEXTNLIST = ['.txt', '.csv', '.pdf', '.xls', '.xlsx', '.doc', '.docx', '.ppt', '.pptx', '.wiki', '.md', '.py', '.js', '.php' , '.sh', '.c' , '.pl', '.cpp', '.cs', '.h', '.java', '.swift']

#List of of all file extensions[document types] that the app will read, extract text and then encode using LLM
FILEXTNLIST = ['.txt', '.csv', '.pdf', '.xlsx', '.docx', '.pptx']

#A list of all text file extension types. We will not do an extractText operation on them.
TXTFILEXTN = ['.txt', '.csv', '.py', '.js', '.php' , '.sh', '.c' , '.pl', '.cpp', '.cs', '.h', '.java', '.swift']

TXTCHUNKSIZE = 700
S3MAXKEYS=1000   #MAXIMUM ALLOWED VALUE IS 1000
