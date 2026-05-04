import requests
from dotenv import load_dotenv
import os
from google import genai
from google.genai import types


class ModelHandler:
    def __init__(self):
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=gemini_api_key) if gemini_api_key else None

    def ask_for_code(
        self,
        query: str,
        config: dict,
        provider: str = "gemini",
        model: str = "gemini-2.5-flash",
        base_url: str = "http://localhost:11434",
    ) -> str:
        system_prompt = self._system_instruction(config)
        if provider == "ollama":
            return self._ask_ollama(query, system_prompt, model, base_url)
        return self._ask_gemini(query, system_prompt, model)

    def _ask_gemini(self, query: str, system_prompt: str, model: str) -> str:
        if not self.client:
            raise ValueError("GEMINI_API_KEY is not set — cannot use Gemini provider.")
        generate_config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=8192,
        )
        response = self.client.models.generate_content(
            model=model,
            contents=query,
            config=generate_config,
        )
        return response.text

    def _ask_ollama(self, query: str, system_prompt: str, model: str, base_url: str) -> str:
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "system": system_prompt, "prompt": query, "stream": False},
        )
        response.raise_for_status()
        return response.json()["response"]

    def _system_instruction(self, config: dict = None) -> str:
        return f"""
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


config_for_rag_coder = {
    "persona": "Senior Staff Software Engineer and Technical Architect",
    "domain": "Software development, API integration, and clean code architecture",
    "goal": "Generate production-ready, error-free code strictly based on the provided documentation chunks. Do not hallucinate methods not present in the context.",
    "audience": "Other software developers",
    "tone": "Direct, technical, and precise. No fluff or unnecessary pleasantries.",
    "style": "Code-first. Provide brief, architectural explanations followed by heavily commented, runnable code.",
    "format": "Markdown with syntax-highlighted code blocks. Include step-by-step usage instructions if necessary.",
    "length": "Concise explanations, but complete and un-truncated code blocks.",
}


if __name__ == "__main__":
    model_handler = ModelHandler()
    query = "What is the best way to implement a binary search tree in Python?"
    response = model_handler.ask_for_code(query, config_for_rag_coder)
    print("Model Response:")
    print(response)
