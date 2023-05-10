import json
import grobid_tei_xml

xml_path = "./example_out/test_pdf1.tei.xml"

#entry point
def get_document_data(path):
    with open(path, 'r') as xml_file:
        doc = grobid_tei_xml.parse_document_xml(xml_file.read())
    
    data = doc.to_dict()
    document_data_dict = {
        "abstract": data["abstract"],
        "body": data["body"]
    }
    
    return document_data_dict

test_data = get_document_data(xml_path)
print(test_data["abstract"])
print(test_data["body"])



