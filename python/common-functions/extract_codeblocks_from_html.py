import re

# as per recommendation, compile once only
#CLEANR = re.compile('<.*?>') 
CLEANR = re.compile('&lt;pre&gt;|&lt;/pre&gt;|&lt;code&gt|&lt;/code&gt;|p&gt;|/p&gt;|&#xA;|<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')


def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

def get(text_in):
  out_array = []
#  print('\n=====INPUT TEXT FOR extract code block function =======\n')
#  print(text_in)
  
  #code_block_pattern = '&lt;code&gt;(.*?)&lt;/code&gt;'
  #match_code_block = re.findall(code_block_pattern,text_in,re.MULTILINE|re.DOTALL)
  #match_code_block = re.findall(code_block_pattern,text_in)
  #match_code_block = re.finditer(r'&lt;code&gt;(.*?)&lt;/code&gt;',text_in,re.MULTILINE|re.DOTALL)
  match_code_block = re.finditer(r'<code>(.*?)</code>',text_in,re.MULTILINE|re.DOTALL)
#  print('\n=====IN extract code block function =======\n')

  for code_block in match_code_block:
#      print(code_block.group())
      out_array.append(cleanhtml(code_block.group()))

#  print('\n=====EXITING extract code block function =======\n')
  return out_array
