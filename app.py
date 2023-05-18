import tempfile, shutil, os, json
import tkinter as tk
from tkinter import filedialog
from grobid_client.grobid_client import GrobidClient
import grobid_tei_xml

def get_document_data(path):
    with open(path, 'r') as xml_file:
        doc = grobid_tei_xml.parse_document_xml(xml_file.read())
    
    data = doc.to_dict()
    document_data_dict = {
        "abstract": data["abstract"],
        "body": data["body"]
    }
    
    return document_data_dict

def upload_file():
    # Clear the output text box
    output_text.delete("1.0", tk.END)

    # Open a file dialog to select a file
    file_path = filedialog.askopenfilename()

    parse_file(file_path)

def parse_file(file_path):
    # Create a temporary directory and copy the file there
    temp_in_dir = tempfile.mkdtemp()
    temp_file_path = temp_in_dir + "/" + file_path.split("/")[-1]
    shutil.copyfile(file_path, temp_file_path)

    # Create a temporary directory for the output
    temp_out_dir = tempfile.mkdtemp()
    
    client = GrobidClient(config_path="./data/config.json")
    client.process("processFulltextDocument", temp_in_dir, output=temp_out_dir, 
                   consolidate_citations=True, tei_coordinates=False, force=True)
    
    # Close the input directory
    shutil.rmtree(temp_in_dir)

    # Read all files in the output directory
    for file in os.listdir(temp_out_dir):
        if not file.endswith(".tei.xml"):
            continue
        document_data = get_document_data(temp_out_dir + "/" + file)

    # Close the output directory
    shutil.rmtree(temp_out_dir)

    # Get the document text
    document = document_data["abstract"] + "\n" + document_data["body"]

    # Write the output to the text box
    output_text.insert(tk.END, document)

    # # Attach the scrollbar with the text widget
    # v.config(command=output_text.yview)
    # output_text.pack()




root = tk.Tk()
root.geometry("400x400") 
root.title("Article Summarizer")  

frame = tk.Frame(root)
frame.pack(expand=True)

button = tk.Button(frame, text="Upload File", command=upload_file)
button.pack() 

# v=tk.Scrollbar(frame, orient='vertical')
# v.pack(side=tk.RIGHT, fill='y')

output_text = tk.Text(root, height=10, wrap=tk.WORD)
output_text.pack(padx=10, pady=10)

# Write the output to the text box
output_text.insert(tk.END, "Upload a file to summarize.")

# Attach the scrollbar with the text widget
# v.config(command=output_text.yview)
# output_text.pack()

root.mainloop()