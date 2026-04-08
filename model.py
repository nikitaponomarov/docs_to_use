

from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from dotenv import load_dotenv
import os 
from google import genai
from google import genai
from google.genai import types

class ModelHandler:
    """Handler for preparing and querying documents in a ChromaDB collection.

    This class provides methods to add pre-split document chunks to a ChromaDB collection,
    query the collection for relevant documents based on a textual query, and chunk local
    text files into manageable pieces. The collection is configured to use the `ollama_ef`
    embedding function for vectorizing the documents, enabling efficient similarity search.
    Attributes:
        ollama_ef (OllamaEmbeddingFunction): The embedding function used for vectorizing documents.
    """
    def __init__(self):
        """Instantiate the Chroma client and obtain/create the target collection.

        The collection is created (or retrieved if existing) with the
        `ollama_ef` embedding function configured at module level.
        """
        self.ollama_ef = OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="mxbai-embed-large"
        )
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        
        self.client = genai.Client(api_key=gemini_api_key)
    def ask_for_code(self, query: str,config:dict) -> str:
        """Generate a response from the model based on the provided query.
        This method is a placeholder for the actual implementation of querying the model
        and generating a response based on the input query. The implementation would typically involve processing the query, generating a response using the model, and returning the response to the user.

        Args:
            query (str): The input query for which a response is to be generated.
            config (dict): Configuration parameters for the system instruction.
        Returns:
            str: The generated response from the model based on the input query.
        """
        system_prompt = self._system_instruction(config)
        generate_config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=generate_config
        )
        return response.text
    def _system_instruction(self,config:dict = None) -> str:
        """Generate a system instruction for the model.

        This method is a placeholder for the actual implementation of generating
        system instructions that guide the model's behavior during response generation.
        The implementation would typically involve defining specific instructions or
        guidelines that the model should follow when processing queries and generating
        responses.

        Returns:
            str: The generated system instruction for the model.
        """
        instruction =f"""
        # ROLE & PERSONA
        Act as: {config.get('persona', 'You are computer science expert')}
        
        # DOMAIN (EXPERTISE)
        Your area of expertise is: {config.get('domain', 'Computer Science')}
        
        # GOAL
        The primary objective of your response is: {config.get('goal', 'Provide a clear and structured answer to the user query,based on library documentation and best practices in computer science')}
        
        # AUDIENCE
        Your target audience is: {config.get('audience', 'General users with an interest in computer science')}
        
        # TONE & STYLE
        Tone: {config.get('tone', 'Professional and helpful')}
        Style: {config.get('style', 'Concise')}
        
        # FORMAT & LENGTH
        Required format: {config.get('format', 'Continuous text')}
        Expected length: {config.get('length', 'Medium')}
        """
        # Placeholder for actual implementation
        return instruction

config_for_rag_coder = {
    "persona": "Senior Staff Software Engineer and Technical Architect",
    "domain": "Software development, API integration, and clean code architecture",
    "goal": "Generate production-ready, error-free code strictly based on the provided documentation chunks. Do not hallucinate methods not present in the context.",
    "audience": "Other software developers",
    "tone": "Direct, technical, and precise. No fluff or unnecessary pleasantries.",
    "style": "Code-first. Provide brief, architectural explanations followed by heavily commented, runnable code.",
    "format": "Markdown with syntax-highlighted code blocks. Include step-by-step usage instructions if necessary.",
    "length": "Concise explanations, but complete and un-truncated code blocks."
}


if __name__ == "__main__":    
    model_handler = ModelHandler()
    query = "What is the best way to implement a binary search tree in Python?"
    response = model_handler.ask_for_code(query, config_for_rag_coder)
    print("Model Response:")
    print(response)