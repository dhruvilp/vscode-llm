# VSCode Github Copilot Extension API Enablement Experiments

## VSCode Extension Setup
* Create a new VS Code extension project (e.g., using `yo code` and choosing TypeScript).
* Replace the content of `src/extension.ts` with the code above.
* Update package.json as shown.
* Run `npm install`.
* Compile: `npm run compile`.
* Open `extension.ts` file in VSCode
* Press `F5` in VS Code to launch the Extension Development Host. The extension will activate, and the server will start. Check the Debug Console for messages

## LLM Api Client Setup
* To run this CLIENT script:

* Located at `llm_api_client.py`

* `curl -X POST -H "Content-Type: application/json" \
     -d '{"prompt": "Write a haiku about coding.", "vendor": "copilot", "family": "gpt-4o"}' \
     http://localhost:3000/chat`


## Google ADK Setup
* **DEV UI** Run the following command to launch the dev UI `adk web` from parent folder at `http://localhost:8000`
* **Terminal** Run the following command, to chat with your Weather agent. `adk run multi_tool_agent`
* **API Server** (adk api_server) `adk api_server`