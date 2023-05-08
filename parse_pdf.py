from grobid_client.grobid_client import GrobidClient

if __name__ == "__main__":
    client = GrobidClient(config_path="./config.json")
    client.process("processFulltextDocument", "../example_data/", output="../example_out/", 
                   consolidate_citations=True, tei_coordinates=False, force=True)
