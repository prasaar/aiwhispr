import re

# as per recommendation, compile once only
#CLEANR = re.compile('<.*?>') 
CLEANR = re.compile('&lt;pre&gt;|&lt;/pre&gt;|&lt;code&gt|&lt;/code&gt;|p&gt;|/p&gt;|&#xA;|<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')


def get(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext


#code_block_pattern = '&lt;code&gt;(.*?)&lt;/code&gt;'
#match_code_block = re.findall(code_block_pattern,text_in,re.MULTILINE|re.DOTALL)
#for code_block in match_code_block:
#    print('CODE:' + cleanhtml(code_block))

