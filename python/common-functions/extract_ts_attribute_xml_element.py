import datetime
import xml.etree.ElementTree 

### Convert date into unix timestamp ####
def convert_to_unix_timestamp(in_date):
    date_format = datetime.datetime.strptime(in_date, "%Y-%m-%dT%H:%M:%S.%f")
    unix_time = datetime.datetime.timestamp(date_format)
    return unix_time

def get(element, attribute_name):
  if attribute_name in element.attrib: 
       return convert_to_unix_timestamp(element.attrib[attribute_name]) 
  else: 
      return None

