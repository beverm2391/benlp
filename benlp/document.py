from pathlib import Path
import os
from .loaders import create_loader
from .utils import random_6_digit_id, DefaultSplitter, PythonSplitter, TikTokenSplitter
from .llms import embed_ada_list

class Document:
    """
    A class to represent a single file document.
    """

    def __init__(self, fpath: str):
        """
        Initialize the Document class with the given file path.

        :param fpath: str, the file path of the document
        """
        self.fpath = None
        self.ext = None
        self.fname = None
        self.text = None
        self.metadata = None
        self.chunks = None
        self.chunk_metadata = None
        self.embeddings = None

        self.parse_filepath(fpath)

    def parse_filepath(self, fpath: str) -> None:
        """
        Parse the file path, check if it exists, and set the file path, extension, and file name.

        :param fpath: str, the file path of the document
        :raises FileNotFoundError: if the file does not exist
        :raises Exception: if the path is a directory (only single files are supported)
        """
        file_path = Path(fpath)

        if not file_path.exists():
            raise FileNotFoundError(f"Document at {fpath} does not exist.")

        if file_path.is_dir():
            raise Exception(
                "Only single files are supported at this time. Use multiple instances of Document for multiple files.")

        if file_path.is_file():
            self.fpath = fpath
            self.ext = file_path.suffix
            self.fname = file_path.name
            print(f"Document at {fpath} loaded.")

    def parse(self):
        """
        Parse the file
        """
        # load it
        loader = create_loader(self.fpath)
        doc_obj = loader.load()

        # parse it
        text = [item.page_content for item in doc_obj]
        metadata = [item.metadata for item in doc_obj]

        self.text = text
        print("self.text", self.text)
        self.metadata = metadata

        print(f"Document at {self.fpath} parsed.")
        return self

    def chunk(self, chunk_size=1024, chunk_overlap=0, splitter_type='default'):
        """
        Chunk the document into smaller pieces for indexing.
        """
        # ! check if the file extension has a default chunker
        if self.ext == '.py':
            return self.chunk_python()
        elif self.ext == '.ipynb':
            return self.chunk_jupyter()

        #! else you can specify the chunker type if the file extension doesn't have a defauult
        valid_splitter_types = ['default', 'tiktoken', 'python']
        if splitter_type not in valid_splitter_types:
            raise Exception(
                f"Chunk type must be one of {valid_splitter_types}.")
        
        # create the splitter
        if splitter_type == 'default':
            splitter = DefaultSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        elif splitter_type == 'tiktoken':
            splitter = TikTokenSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # split the text
        split_text_obj = splitter.create_documents(self.text)
        self.chunks = [item.page_content for item in split_text_obj]

        return self
    
    def chunk_python(self):
        """
        Chunk a python file into smaller pieces for indexing.
        """
        splitter = PythonSplitter()
        split_text_obj = splitter.create_documents(self.text)
        self.chunks = [item.page_content for item in split_text_obj]
        return self
    
    def chunk_jupyter(self):
        """
        Chunk a jupyter notebook into smaller pieces for indexing. Separate class because of file ext and the splitter returns metadata.
        """
        splitter = PythonSplitter()
        split_text_obj = splitter.create_documents(self.text)
        self.chunks = [item.page_content for item in split_text_obj]
        return self

    def embed(self):
        """
        Embed the document.
        """
        if self.chunks is None:
            print("Document not chunked. Chunking now...")
            self.chunk()

        self.embeddings = embed_ada_list(self.chunks)
        print(f"Document at {self.fpath} embedded.")
        return self
    
    def process(self):
        """
        Process the document, returning a dictionary.
        """
        self.parse()
        self.chunk()
        self.embed()
        return self

    def to_dict(self):
        """
        Convert the Document to a dictionary.

        :return: dict, the Document as a dictionary
        """
        # ! if the document hasn't been processed, process it
        if any([self.chunks, self.embeddings]) is None:
            self.process()
        
        doc_id = random_6_digit_id()
        doc_dict = {
            "id": doc_id,
            "fpath": self.fpath,
            "ext": self.ext,
            "fname": self.fname,
            "metadata": self.metadata,
            "data" : [
                {
                    "id": f"{doc_id}-{idx + 1}",
                    "text": chunk,
                    "embedding": self.embeddings[idx],
                } for idx, chunk in enumerate(self.chunks)
            ]
        }

        return doc_dict
    
class JupyterSimple:
    def __init__(self, fpath):
        self.fpath = fpath

        self.read_file(fpath)
        self.parse_cells()

    def read_file(self, fpath):
        with open(fpath, "r") as f:
            code = f.read()
        self.code = code

    def parse_cells(self):
        # replace null with empty string to avoid errors
        self.code = self.code.replace('null', '""')

        # parse the cells
        cells = eval(self.code)['cells']
        code_cells = [c for c in cells if c['cell_type'] == 'code']
        markdown_cells = [c for c in cells if c['cell_type'] == 'markdown']

        self.cells = cells
        self.code_cells = code_cells
        self.markdown_cells = markdown_cells

    def create_prompt(self, prompt=None):
        default_prompt = """Write detailed documentation explaining how the code below works.
                        
                        FORMATTING:

                        - Use markdown to format your response.
                        - Use the following markdown to indicate code blocks: ```code```
                        - Use the following markdown to indicate code blocks with a language: ```python
                        - rewrite the code, then write your docs

                        EXAMPLE OUTPUT:

                        ```python
                        def add(a, b):
                            return a + b
                        ```

                        This function adds two numbers together.
                        
                        ```python
                        add(1, 2)
                        ```

                        Here we call the function with 1 and 2 as arguments, which returns 3.
                        
                        ...
                        """
        
        source_code = [c['source'] for c in self.code_cells]
        final_prompt = f"""
        INSTRUCTIONS: {prompt if prompt else default_prompt}
        SOURCE CODE:
        {source_code}

        OUTPUT:
        """
        self.final_prompt = final_prompt
        return final_prompt

    def document(self, prompt=None, model='gpt-3.5-turbo-16k-0613'):
        try:
            from benlp.llms import Chat
        except:
            raise Exception("benlp must be installed to use the document function since it relies on an import from benlp.llms")

        print("Generating docs...")

        self.create_prompt(prompt)
        
        chat = Chat(model=model, max_tokens=2048)
        docs = chat(self.final_prompt)['response']
        print("Complete.")
        self.docs = docs
        return self
    
    def export(self):
        if self.docs is None:
            raise Exception("You must run the document method first. with obj.document()")
        
        print("Exporting docs...")

        fpath = self.fpath
        file_name, _ = os.path.splitext(os.path.basename(fpath))
        new_file_name = f"{file_name}_docs_{random_6_digit_id()}.md"
        write_fpath = os.path.join(os.path.dirname(fpath), new_file_name)
        with open(write_fpath, 'w') as f:
            f.write(self.docs)

        print(f"Docs exported to {write_fpath}")

    def run(self):
        print("Running...")
        self.document()
        self.export()
        print("Complete.")

class JupyterSimpleServer:
    def __init__(self, file_contents):
        self.code = file_contents
        self.parse_cells()

    def parse_cells(self):
        # replace null with empty string to avoid errors
        self.code = self.code.replace('null', '""')

        # parse the cells
        cells = eval(self.code)['cells']
        code_cells = [c for c in cells if c['cell_type'] == 'code']
        markdown_cells = [c for c in cells if c['cell_type'] == 'markdown']

        self.cells = cells
        self.code_cells = code_cells
        self.markdown_cells = markdown_cells

    def create_prompt(self, prompt=None):
        default_prompt = """Write detailed documentation explaining how the code below works.
                        
                        FORMATTING:

                        - Use markdown to format your response.
                        - Use the following markdown to indicate code blocks: ```code```
                        - Use the following markdown to indicate code blocks with a language: ```python
                        - rewrite the code, then write your docs

                        EXAMPLE OUTPUT:

                        ```python
                        def add(a, b):
                            return a + b
                        ```

                        This function adds two numbers together.
                        
                        ```python
                        add(1, 2)
                        ```

                        Here we call the function with 1 and 2 as arguments, which returns 3.
                        
                        ...
                        """
        
        source_code = [c['source'] for c in self.code_cells]
        final_prompt = f"""
        INSTRUCTIONS: {prompt if prompt else default_prompt}
        SOURCE CODE:
        {source_code}

        OUTPUT:
        """
        self.final_prompt = final_prompt
        return final_prompt

    def document(self, prompt=None, model='gpt-3.5-turbo-16k-0613'):
        try:
            from benlp.llms import Chat
        except:
            raise Exception("benlp must be installed to use the document function since it relies on an import from benlp.llms")

        print("Generating docs...")

        self.create_prompt(prompt)
        
        chat = Chat(model=model, max_tokens=2048)
        docs = chat(self.final_prompt)['response']
        print("Complete.")
        self.docs = docs
        return self
    
    def export(self):
        if self.docs is None:
            raise Exception("You must run the document method first. with obj.document()")
        
        print("Exporting docs...")

        fpath = self.fpath
        file_name, _ = os.path.splitext(os.path.basename(fpath))
        new_file_name = f"{file_name}_docs_{random_6_digit_id()}.md"
        write_fpath = os.path.join(os.path.dirname(fpath), new_file_name)
        with open(write_fpath, 'w') as f:
            f.write(self.docs)

        print(f"Docs exported to {write_fpath}")

    def run(self):
        print("Running...")
        self.document()
        self.export()
        print("Complete.")