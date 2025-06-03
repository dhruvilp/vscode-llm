import requests
import json
from typing import Generator, Optional, Dict, Any, List, Union
# Corrected imports for AutoGen v0.2+ (and especially v0.4+)
from autogen.models import ChatCompletionClient, ModelClient
from autogen import ChatCompletion # Still needed for message types

class LLMBridgeClient(ChatCompletionClient):
    """
    A Python client to interact with the LLM Bridge server hosted by the VS Code extension,
    adapted to extend AutoGen's ChatCompletionClient.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the API client.

        Args:
            config (Dict[str, Any]): Configuration dictionary. Expected keys:
                - "host" (str): The hostname of the LLM Bridge server (default: "localhost").
                - "port" (int): The port of the LLM Bridge server (default: 3000).
                - "vendor" (Optional[str]): Default vendor for the language model (e.g., "copilot").
                                            Can be overridden in messages.
                - "family" (Optional[str]): Default family for the language model (e.g., "gpt-4o").
                                            Can be overridden in messages.
                - "request_timeout" (Optional[int]): Timeout for HTTP requests in seconds (default: 300).
        """
        self.config = config
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 3000)
        self.base_url = f"http://{self.host}:{self.port}"
        self.chat_url = f"{self.base_url}/chat"
        self.default_vendor = config.get("vendor", "copilot")
        self.default_family = config.get("family")
        self.request_timeout = config.get("request_timeout", 300) # Default 5 minutes

    def _send_request_stream(
        self,
        prompt: str,
        vendor: Optional[str] = None,
        family: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Generator[str, None, None]:
        """
        Internal method to send a prompt to the LLM and stream the response.
        This is essentially your original `get_chat_completion_stream`.
        """
        payload = {"prompt": prompt}
        if vendor:
            payload["vendor"] = vendor
        elif self.default_vendor:
            payload["vendor"] = self.default_vendor
        if family:
            payload["family"] = family
        elif self.default_family:
            payload["family"] = self.default_family
        if options:
            payload["options"] = options

        try:
            with requests.post(self.chat_url, json=payload, stream=True, timeout=self.request_timeout) as response:
                if response.status_code == 200:
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            yield chunk
                else:
                    error_content = ""
                    try:
                        error_content = response.json()
                    except json.JSONDecodeError:
                        error_content = response.text
                    raise ValueError(
                        f"API request failed with status {response.status_code}: {error_content}"
                    )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to LLM Bridge server at {self.chat_url}: {e}")

    def create(self, params: Dict[str, Any]) -> Union[str, Generator[str, None, None]]:
        """
        AutoGen's required method to create a chat completion.
        This method must handle both streaming and non-streaming requests.

        Args:
            params (Dict[str, Any]): A dictionary containing the request parameters.
                                      Expected to conform to OpenAI's Chat Completion API format,
                                      but we'll adapt it for our LLM Bridge server.
                                      Key parameters for our client:
                                      - "messages" (List[Dict]): A list of message dictionaries.
                                                                 We'll primarily use the last user message.
                                      - "stream" (bool): If True, return a generator.
                                      - "config" (Optional[Dict]): Additional config for the client (e.g., vendor, family).
                                                                  This allows per-request overrides.

        Returns:
            Union[str, Generator[str, None, None]]: The chat completion result (string or generator).
        """
        messages = params.get("messages")
        if not messages:
            raise ValueError("Messages are required for chat completion.")

        # Get the last user message as the prompt
        prompt = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                prompt = message.get("content", "")
                break
        if not prompt:
            raise ValueError("No user message found in the 'messages' list to use as a prompt.")

        # Extract client-specific configuration from params or use defaults
        client_config = params.get("config", {})
        vendor = client_config.get("vendor", self.default_vendor)
        family = client_config.get("family", self.default_family)

        llm_options = client_config.get("options", {})
        if "temperature" in params:
            llm_options["temperature"] = params["temperature"]
        if "max_tokens" in params:
            llm_options["max_tokens"] = params["max_tokens"]

        stream = params.get("stream", False)

        if stream:
            def stream_generator() -> Generator[ChatCompletion.CreateResponse, None, None]:
                for text_chunk in self._send_request_stream(prompt, vendor, family, llm_options):
                    yield ChatCompletion.CreateResponse(
                        id="chatcmpl-custom-id",
                        choices=[
                            ChatCompletion.Choice(
                                index=0,
                                delta={"content": text_chunk},
                                finish_reason=None
                            )
                        ],
                        created=0, # Placeholder
                        model="llm-bridge-model", # Placeholder
                        object="chat.completion.chunk"
                    )
            return stream_generator()
        else:
            full_response_content = ""
            for text_chunk in self._send_request_stream(prompt, vendor, family, llm_options):
                full_response_content += text_chunk

            return ChatCompletion.CreateResponse(
                id="chatcmpl-custom-id",
                choices=[
                    ChatCompletion.Choice(
                        index=0,
                        message=ChatCompletion.Message(
                            role="assistant",
                            content=full_response_content
                        ),
                        finish_reason="stop"
                    )
                ],
                created=0, # Placeholder
                model="llm-bridge-model", # Placeholder
                object="chat.completion"
            )

    # --- Methods required by AutoGen's ModelClient (parent of ChatCompletionClient) ---
    def message_to_dict(self, message: Union[Dict, str]) -> Dict:
        """Converts a message to a dictionary format suitable for the model."""
        if isinstance(message, str):
            return {"role": "user", "content": message}
        return message

    def cost(self, response: ChatCompletion.CreateResponse) -> float:
        """Estimates the cost of a response. Implement as needed."""
        return 0.0

    def get_usage(self, response: ChatCompletion.CreateResponse) -> Dict:
        """Extracts usage statistics from a response. Implement as needed."""
        return {}

    def get_config(self) -> Dict:
        """Returns the client's configuration."""
        return self.config

    def get_default_config(self) -> Dict:
        """Returns the default configuration for this client type."""
        return {
            "host": "localhost",
            "port": 3000,
            "vendor": "copilot",
            "family": "gpt-4o",
            "temperature": 0.7,
            "request_timeout": 300
        }

    def get_available_models(self) -> List[str]:
        """Returns a list of available models for this client."""
        return ["llm-bridge-model"]

    def is_empty(self) -> bool:
        """Checks if the client is empty (e.g., no config provided)."""
        return not bool(self.config)

    def is_compatible(self, config: Dict) -> bool:
        """Checks if the provided config is compatible with this client type."""
        return "host" in config and "port" in config