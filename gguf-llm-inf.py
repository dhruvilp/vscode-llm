#-------------------------------

# main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from llama_cpp import Llama

# Path to your GGUF model file
MODEL_PATH = "path/to/your/model.gguf"

# Initialize the Llama model
llm = Llama(
    model_path=MODEL_PATH,
    chat_format="llama-2"  # or use "chatml", "gemma", etc. as appropriate for your model
)

app = FastAPI()

# Define request and response schemas
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Message]
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
def chat_completions(request: ChatCompletionRequest):
    try:
        # Format messages for llama-cpp-python
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        result = llm.create_chat_completion(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        # Extract response
        response_message = result["choices"][0]["message"]
        return ChatCompletionResponse(
            id=result.get("id", "chatcmpl-1"),
            object="chat.completion",
            created=result.get("created", 0),
            model=request.model or "llama-gguf",
            choices=[
                Choice(
                    index=0,
                    message=Message(**response_message),
                    finish_reason=result["choices"][0].get("finish_reason", "stop")
                )
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# To run: uvicorn main:app --host 0.0.0.0 --port 8080

#----------------------

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
gguf_filename = "tinyllama-1.1b-chat-v1.0.Q6_K.gguf"

tokenizer = AutoTokenizer.from_pretrained(model_id, gguf_file=gguf_filename)
model = AutoModelForCausalLM.from_pretrained(model_id, gguf_file=gguf_filename, torch_dtype=torch.float32)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Load GGUF model and tokenizer
model_id = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
gguf_filename = "tinyllama-1.1b-chat-v1.0.Q6_K.gguf"
tokenizer = AutoTokenizer.from_pretrained(model_id, gguf_file=gguf_filename)
model = AutoModelForCausalLM.from_pretrained(model_id, gguf_file=gguf_filename, torch_dtype=torch.float32)

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = 128
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95

@app.post("/v1/chat/completions")
def chat_completions(request: ChatRequest):
    try:
        # Simple prompt concatenation (adjust for your model's chat format)
        prompt = "\n".join([f"{m.role}: {m.content}" for m in request.messages]) + "\nassistant:"
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            pad_token_id=tokenizer.eos_token_id
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract only the assistant's reply
        reply = response.split("assistant:")[-1].strip()
        return {"choices": [{"message": {"role": "assistant", "content": reply}}]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#-------------------------------

"""
pip install 'llama-cpp-python[server]'

python3 -m llama_cpp.server --model path/to/your/model.gguf

python3 -m llama_cpp.server --model path/to/your/model.gguf --host 0.0.0.0

python3 -m llama_cpp.server --model path/to/your/model.gguf --chat_format chatml

"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="sk-anything")
response = client.chat.completions.create(
    model="your-model",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

#-----------------------------------






































