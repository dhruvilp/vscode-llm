import requests
import json
from typing import Generator, Optional, Dict, Any

class LLMApiClient:
    """
    A Python client to interact with the LLM Bridge server hosted by the VS Code extension.
    """
    def __init__(self, host: str = "localhost", port: int = 3000):
        """
        Initializes the API client.

        Args:
            host (str): The hostname of the LLM Bridge server.
            port (int): The port of the LLM Bridge server.
        """
        self.base_url = f"http://{host}:{port}"
        self.chat_url = f"{self.base_url}/chat"

    def get_chat_completion_stream(
        self,
        prompt: str,
        vendor: Optional[str] = "copilot",
        family: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Generator[str, None, None]:
        """
        Sends a prompt to the LLM and streams the response.

        Args:
            prompt (str): The user's prompt for the language model.
            vendor (Optional[str]): The vendor of the language model (e.g., "copilot").
            family (Optional[str]): The family of the language model (e.g., "gpt-4o", "gpt-3.5-turbo").
            options (Optional[Dict[str, Any]]): Additional options for the language model request
                                                (e.g., {"temperature": 0.7}).

        Yields:
            str: Chunks of the language model's response as they arrive.

        Raises:
            requests.exceptions.RequestException: If the request fails.
            ValueError: If the server returns an error.
        """
        payload = {"prompt": prompt}
        if vendor:
            payload["vendor"] = vendor
        if family:
            payload["family"] = family
        if options:
            payload["options"] = options

        try:
            with requests.post(self.chat_url, json=payload, stream=True, timeout=300) as response: # 5 minute timeout for long responses
                if response.status_code == 200:
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            yield chunk
                else:
                    error_content = ""
                    try:
                        error_content = response.json() # Try to parse JSON error
                    except json.JSONDecodeError:
                        error_content = response.text # Fallback to text
                    raise ValueError(
                        f"API request failed with status {response.status_code}: {error_content}"
                    )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to LLM Bridge server at {self.chat_url}: {e}")


    def get_chat_completion(
        self,
        prompt: str,
        vendor: Optional[str] = "copilot",
        family: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Sends a prompt to the LLM and returns the complete response as a single string.

        Args:
            prompt (str): The user's prompt for the language model.
            vendor (Optional[str]): The vendor of the language model.
            family (Optional[str]): The family of the language model.
            options (Optional[Dict[str, Any]]): Additional options for the request.

        Returns:
            str: The complete response from the language model.

        Raises:
            requests.exceptions.RequestException: If the request fails.
            ValueError: If the server returns an error.
        """
        chunks = []
        for chunk in self.get_chat_completion_stream(prompt, vendor, family, options):
            chunks.append(chunk)
        return "".join(chunks)

# --- Example Usage ---
if __name__ == "__main__":
    client = LLMApiClient() # Assumes server is running on localhost:3000

    # Example 1: Streaming response
    print("--- Streaming Response Example ---")
    user_prompt_stream = "Write a short poem about a curious cat exploring a new room."
    print(f"User: {user_prompt_stream}")
    print("LLM:")
    try:
        for chunk in client.get_chat_completion_stream(
            prompt=user_prompt_stream,
            vendor="copilot", # Be specific or remove to let server default
            family="gpt-4o" # Optional: specify model family
        ):
            print(chunk, end="", flush=True)
        print("\n--- Stream Ended ---")
    except (ConnectionError, ValueError) as e:
        print(f"\nError during streaming: {e}")

    print("\n" + "="*50 + "\n")

    # Example 2: Full response
    print("--- Full Response Example ---")
    user_prompt_full = "What are the main benefits of using Python for web development?"
    print(f"User: {user_prompt_full}")
    try:
        full_response = client.get_chat_completion(
            prompt=user_prompt_full,
            options={"temperature": 0.5} # Example of sending options
        )
        print("LLM:")
        print(full_response)
        print("--- Full Response Received ---")
    except (ConnectionError, ValueError) as e:
        print(f"Error getting full response: {e}")

    print("\n" + "="*50 + "\n")

    # Example 3: Specific model family (if available and supported by your VS Code LLM provider)
    print("--- Specific Model Family Example (e.g., gpt-4o if available) ---")
    user_prompt_family = "Explain the concept of 'recursion' to a 5-year-old."
    print(f"User: {user_prompt_family}")
    print("LLM:")
    try:
        # Note: The actual availability of "gpt-4o" depends on your GitHub Copilot subscription
        # and VS Code's ability to select it via the 'copilot' vendor.
        # If not found, the extension will likely fall back or error as per its logic.
        for chunk in client.get_chat_completion_stream(
            prompt=user_prompt_family,
            vendor="copilot",
            family="gpt-4o" # Requesting a specific family
        ):
            print(chunk, end="", flush=True)
        print("\n--- Stream Ended (Specific Model) ---")
    except (ConnectionError, ValueError) as e:
        print(f"\nError during streaming with specific model: {e}")