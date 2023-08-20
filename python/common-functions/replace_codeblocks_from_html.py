import re

# as per recommendation, compile once only
#CLEANR = re.compile('<.*?>') 
CLEANR = re.compile('&lt;pre&gt;|&lt;/pre&gt;|&lt;code&gt|&lt;/code&gt;|p&gt;|/p&gt;|&#xA;|<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')


def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

def replace(text_in, no_of_replacements):
#  print('\n===== IN replacing code block function  =======\n')
#  print(text_in)

  text_out = text_in
  
  i=0
  while i < no_of_replacements:
      count = 1
      text_out = re.sub( r'<code>(.*?)</code>', '[#CODEBLOCK][' + str(i) + ']' , text_out,count,re.MULTILINE|re.DOTALL )
      i = i + 1
#  print('\n=====EXITING replacing code block function =======\n')
  return  text_out

