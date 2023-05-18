import tkinter as tk
from tkinter import filedialog
from grobid_client.grobid_client import GrobidClient

def upload_file():
    file_path = filedialog.askopenfilename()
    output_text.insert(tk.END, f"Selected file: {file_path}\n")
    
    client = GrobidClient(config_path="./config.json")
    client.process("processFulltextDocument", file_path, output="../example_out/", 
                   consolidate_citations=True, tei_coordinates=False, force=True)


root = tk.Tk()
root.geometry("400x400") 
root.title("Article Summarizer")  

frame = tk.Frame(root)
frame.pack(expand=True)

button = tk.Button(frame, text="Upload File", command=upload_file)
button.pack() 

output_text = tk.Text(root, height=10)
output_text.pack(padx=10, pady=10)

root.mainloop()