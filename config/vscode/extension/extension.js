const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

// Exception data storage
let currentException = null;
let exceptionHistory = [];
const MAX_HISTORY_SIZE = 10;

// Tree data providers
let exceptionTreeProvider;
let variablesTreeProvider;

/**
 * Activate the extension
 * @param {vscode.ExtensionContext} context 
 */
function activate(context) {
    console.log('MicroPython Debugger extension is now active');

    // Create tree data providers
    exceptionTreeProvider = new ExceptionTreeDataProvider();
    variablesTreeProvider = new VariablesTreeDataProvider();

    // Register tree views
    vscode.window.registerTreeDataProvider('micropythonExceptions', exceptionTreeProvider);
    vscode.window.registerTreeDataProvider('micropythonVariables', variablesTreeProvider);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('micropython-debugger.visualizeException', visualizeException),
        vscode.commands.registerCommand('micropython-debugger.showExceptionHistory', showExceptionHistory),
        vscode.commands.registerCommand('micropython-debugger.navigateException', navigateException),
        vscode.commands.registerCommand('micropython-debugger.refreshExceptionView', refreshExceptionView),
        vscode.commands.registerCommand('micropython-debugger.viewExceptionDetails', viewExceptionDetails),
        vscode.commands.registerCommand('micropython-debugger.viewVariableDetails', viewVariableDetails)
    );

    // Set up file system watcher for exception info file
    const workspaceRoot = vscode.workspace.workspaceFolders[0].uri.fsPath;
    const exceptionInfoPath = path.join(workspaceRoot, '.vscode', 'exception_info.json');
    const exceptionHistoryPath = path.join(workspaceRoot, '.vscode', 'exception_history.json');

    // Create .vscode directory if it doesn't exist
    const vscodePath = path.join(workspaceRoot, '.vscode');
    if (!fs.existsSync(vscodePath)) {
        fs.mkdirSync(vscodePath, { recursive: true });
    }

    // Watch for changes to exception info file
    const fileWatcher = vscode.workspace.createFileSystemWatcher(exceptionInfoPath);
    fileWatcher.onDidChange(() => {
        loadExceptionInfo(exceptionInfoPath);
    });
    fileWatcher.onDidCreate(() => {
        loadExceptionInfo(exceptionInfoPath);
    });

    // Watch for changes to exception history file
    const historyWatcher = vscode.workspace.createFileSystemWatcher(exceptionHistoryPath);
    historyWatcher.onDidChange(() => {
        loadExceptionHistory(exceptionHistoryPath);
    });
    historyWatcher.onDidCreate(() => {
        loadExceptionHistory(exceptionHistoryPath);
    });

    // Load initial data if available
    if (fs.existsSync(exceptionInfoPath)) {
        loadExceptionInfo(exceptionInfoPath);
    }
    if (fs.existsSync(exceptionHistoryPath)) {
        loadExceptionHistory(exceptionHistoryPath);
    }

    // Register debug session event handlers
    vscode.debug.onDidStartDebugSession(session => {
        console.log('Debug session started');
    });

    vscode.debug.onDidTerminateDebugSession(session => {
        console.log('Debug session terminated');
    });

    // Add to context
    context.subscriptions.push(fileWatcher);
    context.subscriptions.push(historyWatcher);
}

/**
 * Deactivate the extension
 */
function deactivate() {
    console.log('MicroPython Debugger extension is now deactivated');
}

/**
 * Load exception information from file
 * @param {string} filePath 
 */
function loadExceptionInfo(filePath) {
    try {
        const data = fs.readFileSync(filePath, 'utf8');
        currentException = JSON.parse(data);
        
        // Add to history if not already there
        addToHistory(currentException);
        
        // Refresh views
        exceptionTreeProvider.refresh();
        variablesTreeProvider.refresh();
        
        // Auto-visualize if enabled
        const config = vscode.workspace.getConfiguration('micropythonDebugger');
        if (config.get('autoVisualizeExceptions')) {
            visualizeException();
        }
    } catch (error) {
        console.error('Error loading exception info:', error);
    }
}

/**
 * Load exception history from file
 * @param {string} filePath 
 */
function loadExceptionHistory(filePath) {
    try {
        const data = fs.readFileSync(filePath, 'utf8');
        exceptionHistory = JSON.parse(data);
        
        // Refresh views
        exceptionTreeProvider.refresh();
    } catch (error) {
        console.error('Error loading exception history:', error);
    }
}

/**
 * Add exception to history
 * @param {object} exception 
 */
function addToHistory(exception) {
    // Check if exception is already in history
    const exists = exceptionHistory.some(e => 
        e.type === exception.type && 
        e.value === exception.value &&
        e.timestamp === exception.timestamp
    );
    
    if (!exists) {
        // Add to history
        exceptionHistory.push(exception);
        
        // Limit history size
        const config = vscode.workspace.getConfiguration('micropythonDebugger');
        const maxSize = config.get('exceptionHistorySize') || MAX_HISTORY_SIZE;
        
        if (exceptionHistory.length > maxSize) {
            exceptionHistory = exceptionHistory.slice(-maxSize);
        }
    }
}

/**
 * Visualize the current exception
 */
function visualizeException() {
    if (!currentException) {
        vscode.window.showInformationMessage('No exception information available');
        return;
    }
    
    // Create and show exception panel
    const panel = vscode.window.createWebviewPanel(
        'exceptionVisualization',
        `Exception: ${currentException.type}`,
        vscode.ViewColumn.Two,
        {
            enableScripts: true
        }
    );
    
    // Set panel content
    panel.webview.html = getExceptionWebviewContent(currentException);
}

/**
 * Show exception history
 */
function showExceptionHistory() {
    if (exceptionHistory.length === 0) {
        vscode.window.showInformationMessage('No exception history available');
        return;
    }
    
    // Create quick pick items
    const items = exceptionHistory.map((exception, index) => {
        let timestamp = exception.timestamp;
        try {
            // Format timestamp if possible
            const date = new Date(timestamp);
            timestamp = date.toLocaleString();
        } catch (error) {
            // Use raw timestamp if formatting fails
        }
        
        return {
            label: `${exception.type}`,
            description: exception.value,
            detail: `Time: ${timestamp}`,
            exception: exception,
            index: index
        };
    }).reverse(); // Show newest first
    
    // Show quick pick
    vscode.window.showQuickPick(items, {
        placeHolder: 'Select an exception to visualize'
    }).then(selected => {
        if (selected) {
            currentException = selected.exception;
            visualizeException();
        }
    });
}

/**
 * Navigate through exception frames
 */
function navigateException() {
    if (!currentException || !currentException.traceback || currentException.traceback.length === 0) {
        vscode.window.showInformationMessage('No exception traceback available');
        return;
    }
    
    // Create quick pick items
    const items = currentException.traceback.map((frame, index) => {
        let label = `Frame #${index}`;
        let description = '';
        let detail = '';
        
        if (typeof frame === 'string') {
            detail = frame;
        } else {
            description = frame.function || 'unknown';
            detail = `${frame.file || 'unknown'}:${frame.line || 0}`;
        }
        
        return {
            label: label,
            description: description,
            detail: detail,
            frame: frame,
            index: index
        };
    });
    
    // Show quick pick
    vscode.window.showQuickPick(items, {
        placeHolder: 'Select a frame to navigate to'
    }).then(selected => {
        if (selected && selected.frame && typeof selected.frame !== 'string') {
            // Try to open the file at the specified line
            const file = selected.frame.file;
            const line = selected.frame.line;
            
            if (file && line) {
                // Try to find the file in the workspace
                const workspaceRoot = vscode.workspace.workspaceFolders[0].uri.fsPath;
                let filePath = path.join(workspaceRoot, file);
                
                // Check if file exists
                if (fs.existsSync(filePath)) {
                    vscode.workspace.openTextDocument(filePath).then(doc => {
                        vscode.window.showTextDocument(doc).then(editor => {
                            // Go to line
                            const position = new vscode.Position(line - 1, 0);
                            editor.selection = new vscode.Selection(position, position);
                            editor.revealRange(
                                new vscode.Range(position, position),
                                vscode.TextEditorRevealType.InCenter
                            );
                        });
                    });
                } else {
                    vscode.window.showErrorMessage(`File not found: ${file}`);
                }
            }
        }
    });
}

/**
 * Refresh the exception view
 */
function refreshExceptionView() {
    exceptionTreeProvider.refresh();
    variablesTreeProvider.refresh();
}

/**
 * View exception details
 * @param {object} exception 
 */
function viewExceptionDetails(exception) {
    currentException = exception;
    visualizeException();
}

/**
 * View variable details
 * @param {object} variable 
 */
function viewVariableDetails(variable) {
    vscode.window.showInformationMessage(`${variable.name}: ${variable.value}`);
}

/**
 * Get HTML content for exception webview
 * @param {object} exception 
 * @returns {string} HTML content
 */
function getExceptionWebviewContent(exception) {
    // Format traceback
    let tracebackHtml = '';
    if (exception.traceback && exception.traceback.length > 0) {
        tracebackHtml = '<h3>Traceback</h3><ul>';
        exception.traceback.forEach((frame, index) => {
            if (typeof frame === 'string') {
                tracebackHtml += `<li>${frame}</li>`;
            } else {
                const func = frame.function || 'unknown';
                const file = frame.file || 'unknown';
                const line = frame.line || 0;
                tracebackHtml += `<li><strong>Frame #${index}:</strong> ${func} in ${file}:${line}</li>`;
            }
        });
        tracebackHtml += '</ul>';
    }
    
    // Format attributes
    let attributesHtml = '';
    if (exception.attributes && Object.keys(exception.attributes).length > 0) {
        attributesHtml = '<h3>Attributes</h3><ul>';
        for (const [key, value] of Object.entries(exception.attributes)) {
            attributesHtml += `<li><strong>${key}:</strong> ${value}</li>`;
        }
        attributesHtml += '</ul>';
    }
    
    // Format locals
    let localsHtml = '';
    if (exception.locals && Object.keys(exception.locals).length > 0) {
        localsHtml = '<h3>Local Variables</h3><ul>';
        for (const [key, value] of Object.entries(exception.locals)) {
            localsHtml += `<li><strong>${key}:</strong> ${value}</li>`;
        }
        localsHtml += '</ul>';
    }
    
    // Format timestamp
    let timestamp = exception.timestamp || '';
    try {
        const date = new Date(timestamp);
        timestamp = date.toLocaleString();
    } catch (error) {
        // Use raw timestamp if formatting fails
    }
    
    return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Exception: ${exception.type}</title>
        <style>
            body {
                font-family: var(--vscode-editor-font-family);
                padding: 20px;
                color: var(--vscode-editor-foreground);
                background-color: var(--vscode-editor-background);
            }
            .exception-header {
                background-color: var(--vscode-editorError-foreground);
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .exception-value {
                background-color: var(--vscode-editor-inactiveSelectionBackground);
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                font-family: monospace;
            }
            h3 {
                color: var(--vscode-editorLink-activeForeground);
                border-bottom: 1px solid var(--vscode-editorLink-activeForeground);
                padding-bottom: 5px;
            }
            ul {
                list-style-type: none;
                padding-left: 10px;
            }
            li {
                margin-bottom: 5px;
                font-family: monospace;
            }
            .timestamp {
                color: var(--vscode-descriptionForeground);
                font-style: italic;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="exception-header">
            <h2>Exception: ${exception.type}</h2>
        </div>
        
        <div class="exception-value">
            ${exception.value}
        </div>
        
        <div class="timestamp">
            Time: ${timestamp}
        </div>
        
        ${tracebackHtml}
        
        ${attributesHtml}
        
        ${localsHtml}
    </body>
    </html>
    `;
}

/**
 * Exception tree data provider
 */
class ExceptionTreeDataProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    
    getTreeItem(element) {
        return element;
    }
    
    getChildren(element) {
        if (!element) {
            // Root level - show current exception and history
            const items = [];
            
            // Current exception
            if (currentException) {
                items.push(new ExceptionItem(
                    'Current Exception',
                    `${currentException.type}: ${currentException.value}`,
                    currentException,
                    vscode.TreeItemCollapsibleState.Expanded
                ));
            }
            
            // Exception history
            if (exceptionHistory.length > 0) {
                items.push(new ExceptionItem(
                    'Exception History',
                    `${exceptionHistory.length} exceptions`,
                    { type: 'history' },
                    vscode.TreeItemCollapsibleState.Collapsed
                ));
            }
            
            return items;
        } else if (element.contextValue === 'exception') {
            // Exception details
            const exception = element.exception;
            const items = [];
            
            // Type and value
            items.push(new ExceptionItem(
                'Type',
                exception.type,
                { type: 'property', name: 'Type', value: exception.type },
                vscode.TreeItemCollapsibleState.None
            ));
            
            items.push(new ExceptionItem(
                'Value',
                exception.value,
                { type: 'property', name: 'Value', value: exception.value },
                vscode.TreeItemCollapsibleState.None
            ));
            
            // Traceback
            if (exception.traceback && exception.traceback.length > 0) {
                items.push(new ExceptionItem(
                    'Traceback',
                    `${exception.traceback.length} frames`,
                    { type: 'traceback', traceback: exception.traceback },
                    vscode.TreeItemCollapsibleState.Collapsed
                ));
            }
            
            // Attributes
            if (exception.attributes && Object.keys(exception.attributes).length > 0) {
                items.push(new ExceptionItem(
                    'Attributes',
                    `${Object.keys(exception.attributes).length} attributes`,
                    { type: 'attributes', attributes: exception.attributes },
                    vscode.TreeItemCollapsibleState.Collapsed
                ));
            }
            
            // Locals
            if (exception.locals && Object.keys(exception.locals).length > 0) {
                items.push(new ExceptionItem(
                    'Local Variables',
                    `${Object.keys(exception.locals).length} variables`,
                    { type: 'locals', locals: exception.locals },
                    vscode.TreeItemCollapsibleState.Collapsed
                ));
            }
            
            return items;
        } else if (element.contextValue === 'history') {
            // Exception history
            return exceptionHistory.map((exception, index) => {
                let timestamp = exception.timestamp;
                try {
                    // Format timestamp if possible
                    const date = new Date(timestamp);
                    timestamp = date.toLocaleString();
                } catch (error) {
                    // Use raw timestamp if formatting fails
                }
                
                return new ExceptionItem(
                    `${exception.type}`,
                    `${exception.value} (${timestamp})`,
                    exception,
                    vscode.TreeItemCollapsibleState.None,
                    {
                        command: 'micropython-debugger.viewExceptionDetails',
                        title: 'View Exception Details',
                        arguments: [exception]
                    }
                );
            }).reverse(); // Show newest first
        } else if (element.contextValue === 'traceback') {
            // Traceback frames
            return element.exception.traceback.map((frame, index) => {
                let label = `Frame #${index}`;
                let description = '';
                
                if (typeof frame === 'string') {
                    description = frame;
                } else {
                    description = `${frame.function || 'unknown'} in ${frame.file || 'unknown'}:${frame.line || 0}`;
                }
                
                return new ExceptionItem(
                    label,
                    description,
                    { type: 'frame', frame: frame, index: index },
                    vscode.TreeItemCollapsibleState.None
                );
            });
        } else if (element.contextValue === 'attributes') {
            // Exception attributes
            return Object.entries(element.exception.attributes).map(([key, value]) => {
                return new ExceptionItem(
                    key,
                    String(value),
                    { type: 'property', name: key, value: value },
                    vscode.TreeItemCollapsibleState.None
                );
            });
        } else if (element.contextValue === 'locals') {
            // Local variables
            return Object.entries(element.exception.locals).map(([key, value]) => {
                return new ExceptionItem(
                    key,
                    String(value),
                    { type: 'property', name: key, value: value },
                    vscode.TreeItemCollapsibleState.None,
                    {
                        command: 'micropython-debugger.viewVariableDetails',
                        title: 'View Variable Details',
                        arguments: [{ name: key, value: value }]
                    }
                );
            });
        }
        
        return [];
    }
}

/**
 * Variables tree data provider
 */
class VariablesTreeDataProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    
    getTreeItem(element) {
        return element;
    }
    
    getChildren(element) {
        if (!element) {
            // Root level - show variables from current exception
            if (!currentException || !currentException.locals) {
                return [];
            }
            
            return Object.entries(currentException.locals).map(([key, value]) => {
                return new VariableItem(
                    key,
                    String(value),
                    { name: key, value: value },
                    vscode.TreeItemCollapsibleState.None,
                    {
                        command: 'micropython-debugger.viewVariableDetails',
                        title: 'View Variable Details',
                        arguments: [{ name: key, value: value }]
                    }
                );
            });
        }
        
        return [];
    }
}

/**
 * Exception tree item
 */
class ExceptionItem extends vscode.TreeItem {
    constructor(label, description, exception, collapsibleState, command) {
        super(label, collapsibleState);
        this.description = description;
        this.exception = exception;
        this.contextValue = exception.type;
        
        if (command) {
            this.command = command;
        }
        
        // Set icon based on type
        if (exception.type === 'history') {
            this.iconPath = new vscode.ThemeIcon('history');
        } else if (label === 'Current Exception') {
            this.iconPath = new vscode.ThemeIcon('bug');
        } else if (label === 'Traceback') {
            this.iconPath = new vscode.ThemeIcon('list-ordered');
        } else if (label === 'Attributes') {
            this.iconPath = new vscode.ThemeIcon('symbol-property');
        } else if (label === 'Local Variables') {
            this.iconPath = new vscode.ThemeIcon('symbol-variable');
        } else if (exception.type === 'frame') {
            this.iconPath = new vscode.ThemeIcon('debug-stackframe');
        } else if (exception.type === 'property') {
            this.iconPath = new vscode.ThemeIcon('symbol-field');
        }
    }
}

/**
 * Variable tree item
 */
class VariableItem extends vscode.TreeItem {
    constructor(label, description, variable, collapsibleState, command) {
        super(label, collapsibleState);
        this.description = description;
        this.variable = variable;
        this.contextValue = 'variable';
        
        if (command) {
            this.command = command;
        }
        
        this.iconPath = new vscode.ThemeIcon('symbol-variable');
    }
}

module.exports = {
    activate,
    deactivate
}; 