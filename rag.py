import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction


ollama_ef = OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="mxbai-embed-large"
)

class Rag_Handler:
    """Handler for preparing and querying documents in a ChromaDB collection.

    Uses an Ollama embedding function to create embeddings and stores
    documents in a local ChromaDB collection. Provides methods to add
    documents (as pre-split chunks), query the collection, and chunk
    local text files.
    """

    def __init__(self):
        """Instantiate the Chroma client and obtain/create the target collection.

        The collection is created (or retrieved if existing) with the
        `ollama_ef` embedding function configured at module level.
        """
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(
            name="local_docs_collection",
            embedding_function=ollama_ef
        )

    def add_document(self, chunks):
        """Add a list of textual chunks to the Chroma collection.

        Args:
            chunks (List[str]): Pre-split document chunks to add as documents.
        """
        self.collection.add(
            ids = [f'id{i}' for i in range(len(chunks))],
            documents = chunks
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
            n_results=1
        )
        return results['documents'][0]

    def chunking(self, file_path, ch_size, ch_overlap):
        """Read a local file and split it into overlapping chunks.

        Args:
            file_path (str): Path to a local text file to chunk.
            ch_size (int): Target chunk size in characters.
            ch_overlap (int): Overlap between consecutive chunks.

        Returns:
            List[str]: List of text chunks.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            document = f.read()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=ch_size, chunk_overlap=ch_overlap)
        chunks = text_splitter.split_text(document)
        return chunks

def main():
    rag_handler = Rag_Handler()
    
    # Assuming you have a file named "first.txt"
    print("Chunking document...")
    chunks = rag_handler.chunking("first.txt", 1000, 200)
    
    print(f"Adding {len(chunks)} chunks to ChromaDB using Ollama (This might take a few seconds on CPU)...")
    rag_handler.add_document(chunks)
    
    print("Querying the database...")
    query = "How to set cloudclient?"
    results = rag_handler.query(query)
    
    print("\n--- Top Result ---")
    print(results)

if __name__ == "__main__":
    main()