import xml.etree.ElementTree as ET
try:
    ET.parse('Base Application.ar-JO.xlf')
    print('OK')
except Exception as e:
    print(f'Error: {e}')
