import xml.etree.ElementTree 

def get(element, attribute_name):
  if attribute_name in element.attrib: 
       return element.attrib[attribute_name] 
  else: 
      return None

