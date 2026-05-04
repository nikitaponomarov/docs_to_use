import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
import uuid

def get_embedding_function(model_name: str = "mxbai-embed-large", url: str = "http://localhost:11434/api/embeddings"):
    return OllamaEmbeddingFunction(url=url, model_name=model_name)

class Rag_Handler:
    """Handler for preparing and querying documents in a ChromaDB collection.

    Uses an Ollama embedding function to create embeddings and stores
    documents in a local ChromaDB collection. Provides methods to add
    documents (as pre-split chunks), query the collection, and chunk
    local text files.
    """

    def __init__(self, ollama_ef, collection_name="chroma_docs_collection"):
        """Instantiate the Chroma client and obtain/create the target collection.

        The collection is created (or retrieved if existing) with the
        `ollama_ef` embedding function configured at module level.
        """
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=ollama_ef
        )

    def add_document(self, documents):
        """Add a list of Langchain Document objects to the Chroma collection.

        Args:
            documents (List[Document]): Processed document chunks with metadata to add.
        """
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata if doc.metadata else {} for doc in documents]
        
        self.collection.add(
            ids=[str(uuid.uuid4()) for _ in documents],
            documents=texts,
            metadatas=metadatas
        )

    def query(self, query):
        """Query the collection for the most similar document to `query`.

        Args:
            query (str): Textual query to search for.

        Returns:
            str: The top-matching document text.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=10
        )
        return results['documents'][0]

    def chunking(self, document, ch_size, ch_overlap):
        """Read a local file, clean web noise, and split it contextually.

        Args:
            document (str): The raw text document to chunk.
            ch_size (int): Target chunk size in characters.
            ch_overlap (int): Overlap between consecutive chunks.

        Returns:
            List[Document]: List of Langchain Document objects with metadata.
        """
        raw_text = document
        
        # 1. Clean the raw text of web noise (Flexible/Dynamic)
        # Find the very first H1 tag, stripping all navigation metadata before it
        h1_index = raw_text.find("# ")
        if h1_index != -1:
            raw_text = raw_text[h1_index:]
            
        # Strip common documentation footer signatures
        footer_markers = ["Was this page helpful?", "Powered by", "Copyright ©", "Docs home page"]
        for marker in footer_markers:
            idx = raw_text.rfind(marker)
            if idx != -1 and idx > len(raw_text) * 0.6: # Verify it's situated at the bottom
                raw_text = raw_text[:idx]

        # 2. Define Header splitting to retain semantic meaning
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]

        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_header_splits = markdown_splitter.split_text(raw_text)

        # 3. Further refine large sections into smaller chunks without exceeding AI context win
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=ch_size,
            chunk_overlap=ch_overlap,
            separators=["\n\n", "\n", ". "]
        )

        final_chunks = text_splitter.split_documents(md_header_splits)
        return final_chunks

