import autogen

from api_client.llm_bridge_client import LLMBridgeClient


# 1. Instantiate your custom client
llm_bridge_client = LLMBridgeClient(
    config={
        "host": "localhost",
        "port": 3000,
        "vendor": "copilot", # Default vendor for all requests
        "request_timeout": 600 # Longer timeout if needed
    }
)

# 2. Define your LLM configuration for AutoGen
# The key is to specify your custom client class and pass its config
llm_config = {
    "config_list": [
        {
            "model": "llm-bridge-model", # This is a placeholder model name for AutoGen
                                        # It maps to your custom client.
            "client": "LLMBridgeClient", # Reference your custom client class name
            "client_kwargs": {
                "config": { # This config dictionary will be passed to LLMBridgeClient.__init__
                    "host": "localhost",
                    "port": 3000,
                    "vendor": "copilot",
                    "family": "gpt-4o", # You can set a default family here
                    "request_timeout": 600
                }
            }
        }
    ],
    "client_map": {
        "LLMBridgeClient": LLMBridgeClient # Map the client name to your class
    },
    "temperature": 0.7,
    "max_tokens": 500,
    "stream": True # Set to True for streaming, False for non-streaming
}


# 3. Create an AutoGen agent
assistant = autogen.AssistantAgent(
    name="assistant",
    system_message="You are a helpful AI assistant.",
    llm_config=llm_config,
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir": "coding", "use_docker": False},
)

# 4. Initiate the chat
user_proxy.initiate_chat(
    assistant,
    message="What is the capital of France?",
    # You can override client-specific config per chat if needed
    llm_config={
        "client_kwargs": {
            "config": {
                "family": "gpt-40" # Use a different family for this specific chat
            }
        }
    }
)

# Example with a different prompt
user_proxy.initiate_chat(
    assistant,
    message="Write a 2-sentence summary of the plot of 'The Lord of the Rings'. TERMINATE",
)