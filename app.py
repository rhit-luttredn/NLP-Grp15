import os
import queue
import shutil
import tempfile
import time
import tkinter as tk
from multiprocessing import Pipe, Process, Queue
from threading import Thread
from tkinter import filedialog, scrolledtext, ttk

import dill
dill.settings['recurse'] = True

import docker
import grobid_tei_xml
from transformers import BertConfig, BertForSequenceClassification, BertTokenizerFast
import nltk 
import torch
import tensorflow as tf
import requests
import validators
from grobid_client.grobid_client import GrobidClient
from transformers import BertConfig, BertModel

###########
# GLOBALS #
###########
GROBID_CLIENT = None
BERT_PATH = "./models/bert-finetuned/"
BERT_MODEL = None
BERT_TOKENIZER = None
CURR_DOCUMENT_TEXT = None
CURR_EXTRACTED_TEXT = None
CURR_ABSTRACT_TEXT = None
DOWNLOADS_DIR = tempfile.mkdtemp()
DELAY = 500
q = Queue()


#############
# FUNCTIONS #
#############
def get_document_data(path):
    with open(path, 'r') as xml_file:
        doc = grobid_tei_xml.parse_document_xml(xml_file.read())
    
    data = doc.to_dict()
    document_data_dict = {
        "abstract": data["abstract"],
        "body": data["body"]
    }
    
    return document_data_dict

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
    document_data = None
    for file in os.listdir(temp_out_dir):
        if not file.endswith(".tei.xml"):
            continue
        document_data = get_document_data(temp_out_dir + "/" + file)

    # Close the output directory
    shutil.rmtree(temp_out_dir)

    # Get the document text
    if document_data is None:
        print("Error: Could not parse file.")
    return document_data["body"]

def extractive_summarization(document):
    # Tokenize the document body text
    doc_sents = nltk.sent_tokenize(document)
    tokenized_doc = [BERT_TOKENIZER(sent, return_tensors='pt').input_ids for sent in doc_sents]

    # Get extracted summary
    with torch.no_grad():
        berted_doc = [BERT_MODEL(sent).logits.argmax().item() for sent in tokenized_doc]
    
    # Get all the salient sentences
    salient_sents = [doc_sents[i] for i in range(len(berted_doc)) if berted_doc[i] == 1]
    return " ".join(salient_sents)

def load_models():
    global BERT_MODEL, BERT_TOKENIZER
    BERT_MODEL = BertForSequenceClassification.from_pretrained(BERT_PATH)
    BERT_TOKENIZER = BertTokenizerFast.from_pretrained('bert-base-uncased')

nltk.download('punkt')

def start_grobid_server():
    global GROBID_CLIENT
    GROBID_CLIENT = docker.from_env()
    GROBID_CLIENT.containers.run("lfoppiano/grobid:0.7.2", detach=True, ports={'8070/tcp':8070}, auto_remove=True)

def is_valid_url(url):
    return validators.url(url)

def is_valid_file(file_path):
    return os.path.exists(file_path)

def download_pdf(url):
    # Download the pdf
    response = requests.get(url)

    # Check if file is already downloaded
    if os.path.exists(DOWNLOADS_DIR + "/" + url.split("/")[-1]):
        return DOWNLOADS_DIR + "/" + url.split("/")[-1]

    # Create a temporary directory and save the pdf there
    temp_file_path = DOWNLOADS_DIR + "/" + url.split("/")[-1]
    with open(temp_file_path, 'wb') as pdf_file:
        pdf_file.write(response.content)

    return temp_file_path

################
# GUI COMMANDS #
################
# Keep these separate from the functions to indicate that they update the GUI
# and should only be called from the main thread
def on_closing():
    global GROBID_CLIENT
    if GROBID_CLIENT is not None:
        GROBID_CLIENT.containers.list()[0].stop()
    root.destroy()

def on_start():
    # Start grobid server in a new thread
    # grobid_server_thread = Thread(target=start_grobid_server)
    # grobid_server_thread.start()

    # Load the models in a new thread
    # load_models_thread = Thread(target=load_models)
    # load_models_thread.start()
    load_models()
    pass


class MainFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.curr_doc_text = None
        self.curr_extracted_text = None
        self.curr_abstract_text = None

        self._initUI()

    def _initUI(self):
        ### MAIN FRAME ###
        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=0)

        separator = ttk.Separator(self, orient='horizontal')
        separator.grid(row=1, sticky="ew", padx=10, pady=10)

        output_frame = tk.Frame(self)
        output_frame.grid(row=2)

        self.columnconfigure(0, weight=1)

        ### BUTTONS FRAME ###
        curr_file_label = tk.Label(buttons_frame, text="Current File")
        curr_file_label.grid(row=0)

        self.curr_file = tk.StringVar()
        self.curr_file_entry = tk.Entry(buttons_frame, width=40, textvariable=self.curr_file)
        self.curr_file_entry.insert(tk.END, "Enter a file or URL to summarize.")
        self.curr_file_entry.grid(row=1)

        # Upload 
        upload_frame = tk.Frame(buttons_frame)
        upload_frame.grid(row=2)

        self.upload_file_button = tk.Button(upload_frame, text="Upload File", command=self.on_upload_file)
        self.upload_file_button.grid(column=0)

        # Summarize
        self.summarize_button = tk.Button(buttons_frame, text="Summarize", command=self.on_summarize)
        self.summarize_button.grid(row=3)

        # dropdown menu
        self.output_display = tk.StringVar()
        self.output_combo = ttk.Combobox(buttons_frame, state="readonly")
        self.output_combo.bind("<<ComboboxSelected>>", self.update_output_text)
        self.output_combo['values'] = ('Document', 'Extracted', 'Abstract')
        print(self.output_combo.current())
        self.output_combo.current(0)
        self.output_combo.grid(row=4)

        ### OUTPUT FRAME ###
        self.pbar = ttk.Progressbar(output_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.pbar.grid(row=0, sticky=(tk.E, tk.W), pady=(0,10))

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD)
        self.output_text.grid(row=1, sticky=(tk.N, tk.S, tk.E, tk.W))

        output_frame.columnconfigure(0, weight=1)

    def on_summarize(self):
        file_path = self.curr_file.get()
        if not is_valid_file(file_path):
            if not is_valid_url(file_path):
                tk.messagebox.showerror("Error", "Please enter a valid file or URL.")
                return
            
            # Download file and save it to temp directory
            file_path = download_pdf(file_path)

        # Disable the summarize button
        self.pbar.start()

        self.summarize(file_path)

        # update output text
        self.update_output_text()

        # Enable the summarize button
        self.summarize_button.config(state=tk.NORMAL)
        self.pbar.stop()

    def summarize(self, file_path):
        
        self.summarize_button.config(state=tk.DISABLED)

        # Parse the file
        self.curr_doc_text = parse_file(file_path)        

        # Extractive summarization
        self.curr_extracted_text = extractive_summarization(self.curr_doc_text)

        # TODO Abstractive summarization
        # curr_abstract_text = abstractive_summarization(curr_extracted_text)
        # self.curr_abstract_text = curr_abstract_text

    def on_upload_file(self):
        # Open a file dialog to select a file
        file_path = filedialog.askopenfilename()

        # Parse the file and update the curr_file_text
        self.curr_file_entry.delete(0, tk.END)
        self.curr_file_entry.insert(tk.END, file_path)
    
    def update_progress_bar(self, value):
        self.pbar["value"] = value
        self.update_idletasks()

    def update_output_text(self):
        texts = [self.curr_doc_text, self.curr_extracted_text, self.curr_abstract_text]
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", texts[self.output_combo.current()])


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x400") 
    root.title("Article Summarizer")

    on_start()

    main_frame = MainFrame(root)
    main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
