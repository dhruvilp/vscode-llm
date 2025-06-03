import * as vscode from 'vscode';
import * as http from 'http';
import { Readable } from 'stream'; // Although Readable is imported, it's not directly used in the provided code for stream handling.

const PORT = 3000; // Port for the local HTTP server
let llmBridgeServer: http.Server | null = null; // Store server instance to manage its lifecycle

// Helper to parse JSON body
async function parseJsonBody(req: http.IncomingMessage): Promise<any> {
    return new Promise((resolve, reject) => {
        let body = '';
        req.on('data', chunk => {
            body += chunk.toString();
        });
        req.on('end', () => {
            try {
                resolve(JSON.parse(body));
            } catch (e) {
                reject(new Error('Invalid JSON body: ' + e));
            }
        });
        req.on('error', reject);
    });
}

function startLlmBridgeServer(context: vscode.ExtensionContext) {
    if (llmBridgeServer && llmBridgeServer.listening) {
        console.log('LLM Bridge server is already running.');
        vscode.window.showInformationMessage(`LLM Bridge server is already running on http://localhost:${PORT}.`);
        return;
    }

    console.log('Starting LLM Bridge HTTP server.');

    llmBridgeServer = http.createServer(async (req, res) => {
        if (req.method === 'POST' && req.url === '/chat') {
            try {
                const requestBody = await parseJsonBody(req);
                const userPrompt = requestBody.prompt;
                // Default to 'copilot' if no vendor is specified in the request
                const modelVendor = requestBody.vendor || 'copilot';
                // modelFamily is optional (e.g., 'gpt-4o', 'gpt-3.5-turbo')
                const modelFamily = requestBody.family;

                if (!userPrompt) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Prompt is required in the request body.' }));
                    return;
                }

                const modelSelector: vscode.LanguageModelChatSelector = { vendor: modelVendor };
                if (modelFamily) {
                    modelSelector.family = modelFamily;
                }

                const models = await vscode.lm.selectChatModels(modelSelector);

                if (!models || models.length === 0) {
                    res.writeHead(503, { 'Content-Type': 'application/json' }); // Service Unavailable
                    res.end(JSON.stringify({ error: `No suitable language model found for vendor '${modelVendor}'${modelFamily ? ` and family '${modelFamily}'` : ''}. Ensure the provider (e.g., GitHub Copilot) is active and available.` }));
                    return;
                }
                const model = models[0]; // Use the first suitable model

                const messages: vscode.LanguageModelChatMessage[] = [
                    vscode.LanguageModelChatMessage.User(userPrompt)
                ];

                // Set headers for streaming the response
                res.writeHead(200, {
                    'Content-Type': 'text/plain; charset=utf-8',
                    'Transfer-Encoding': 'chunked',
                    'X-Content-Type-Options': 'nosniff' // Prevents browser MIME sniffing
                });

                // Optional chat request options from the client
                const chatRequestOptions: vscode.LanguageModelChatRequestOptions = requestBody.options || {};
                const cancellationTokenSource = new vscode.CancellationTokenSource();

                // It's good practice to handle client disconnection for cancellation
                req.on('close', () => {
                    if (!res.writableEnded) {
                        console.log('Client disconnected during LLM request. Cancelling.');
                        cancellationTokenSource.cancel();
                    }
                });

                try {
                    const chatResponse = await model.sendRequest(messages, chatRequestOptions, cancellationTokenSource.token);

                    for await (const fragment of chatResponse.text) {
                        if (!res.writableEnded) { // Ensure response stream is still open
                            res.write(fragment); // Stream each fragment
                        } else {
                            console.warn('Response stream ended prematurely while streaming LLM response.');
                            break;
                        }
                    }
                } catch (llmError: any) {
                    console.error('Error during LLM request:', llmError);
                    if (!res.writableEnded) {
                        res.write(`\nError from LLM service: ${llmError.message || String(llmError)}\n`);
                    }
                } finally {
                    if (!res.writableEnded) {
                        res.end(); // End the chunked response
                    }
                }

            } catch (error: any) {
                console.error('Error processing /chat request:', error);
                // Ensure headers are not sent again if already sent
                if (!res.headersSent) {
                    res.writeHead(500, { 'Content-Type': 'application/json' });
                }
                // Check if we can still write to the response
                if (!res.writableEnded) {
                    res.end(JSON.stringify({ error: 'Failed to process chat request.', details: error.message || String(error) }));
                }
            }
        } else {
            res.writeHead(404, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Not Found. Use POST /chat' }));
        }
    });

    llmBridgeServer.listen(PORT, () => {
        console.log(`LLM Bridge server listening on http://localhost:${PORT}`);
        vscode.window.showInformationMessage(`LLM Bridge server started on port ${PORT}. You can send POST requests to http://localhost:${PORT}/chat`);
    });

    llmBridgeServer.on('error', (err) => {
        console.error('LLM Bridge Server error:', err);
        vscode.window.showErrorMessage(`LLM Bridge server error: ${err.message}`);
        llmBridgeServer?.close(); // Attempt to close on error
        llmBridgeServer = null; // Clear the reference
    });

    // Add server closing to disposables
    context.subscriptions.push(new vscode.Disposable(() => {
        if (llmBridgeServer) {
            llmBridgeServer.close(() => {
                console.log('LLM Bridge server stopped.');
                llmBridgeServer = null; // Clear the reference after close
            });
        }
    }));
}


export function activate(context: vscode.ExtensionContext) {
    console.log('Congratulations, your extension "llm-bridge-extension" is now active!');

    // Register the command that will start the HTTP server
    let disposable = vscode.commands.registerCommand('llm-chat-example.askLlm', () => {
        startLlmBridgeServer(context);
    });

    context.subscriptions.push(disposable);

    // Optional: Start the server immediately on activation if you want it to be always on
    // without requiring the command to be run manually.
    // Uncomment the line below if you want the server to start as soon as the extension activates.
    // startLlmBridgeServer(context);
}

export function deactivate() {
    console.log('Your extension "llm-bridge-extension" is being deactivated.');
    // The server is automatically closed via the disposable in activate
}