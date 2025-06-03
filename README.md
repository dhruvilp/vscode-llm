To run SERVER extension:

Create a new VS Code extension project (e.g., using `yo code` and choosing TypeScript).
Replace the content of `src/extension.ts` with the code above.
Update package.json as shown.
Run `npm install`.
Compile: `npm run compile`.
Open `extension.ts` file in VSCode
Press `F5` in VS Code to launch the Extension Development Host. The extension will activate, and the server will start. Check the Debug Console for messages

To run this CLIENT script:

Located at `llm_api_client.py`

`curl -X POST -H "Content-Type: application/json" \
     -d '{"prompt": "Write a haiku about coding.", "vendor": "copilot", "family": "gpt-4o"}' \
     http://localhost:3000/chat`