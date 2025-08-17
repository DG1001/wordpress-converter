/**
 * AI Chat Interface JavaScript
 * Handles chat communication with AI system
 */

class AIChatInterface {
    constructor() {
        this.socket = null;
        this.currentSiteId = null;
        this.currentSessionId = null;
        this.isProcessing = false;
        
        this.initializeElements();
        this.initializeSocketIO();
        this.loadAIStatus();
        this.loadAvailableSites();
    }

    initializeElements() {
        // Site selection
        this.siteSelector = document.getElementById('site-selector');
        this.analyzeSiteBtn = document.getElementById('analyze-site-btn');
        
        // Chat interface
        this.chatMessages = document.getElementById('chat-messages');
        this.chatForm = document.getElementById('chat-form');
        this.chatInput = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-btn');
        this.autoExecuteCheckbox = document.getElementById('auto-execute');
        
        // Status elements
        this.systemStatus = document.getElementById('system-status');
        this.activeProvider = document.getElementById('active-provider');
        this.memoryStatus = document.getElementById('memory-status');
        
        // Memory browser
        this.memoryBrowser = document.getElementById('memory-browser');
        this.memoryContent = document.getElementById('memory-content');
        
        // Modals
        this.progressModal = document.getElementById('progress-modal');
        this.progressText = document.getElementById('progress-text');
        this.progressBar = document.getElementById('progress-bar');
        this.configModal = document.getElementById('config-modal');
        
        // Event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Site selection
        this.siteSelector.addEventListener('change', () => this.onSiteSelected());
        this.analyzeSiteBtn.addEventListener('click', () => this.analyzeSite());
        
        // Chat form
        this.chatForm.addEventListener('submit', (e) => this.onChatSubmit(e));
        
        // Config modal
        document.getElementById('ai-config-btn').addEventListener('click', () => this.openConfigModal());
        document.getElementById('close-config-modal').addEventListener('click', () => this.closeConfigModal());
    }

    initializeSocketIO() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        this.socket.on('workflow_update', (data) => {
            this.handleWorkflowUpdate(data);
        });
        
        this.socket.on('ai_progress', (data) => {
            this.updateProgress(data);
        });
    }

    async loadAIStatus() {
        try {
            const response = await fetch('/ai/status');
            const data = await response.json();
            
            this.updateStatusDisplay(data);
        } catch (error) {
            console.error('Error loading AI status:', error);
            this.systemStatus.textContent = 'Error';
            this.systemStatus.className = 'px-2 py-1 text-xs rounded-full bg-red-100 text-red-800';
        }
    }

    updateStatusDisplay(data) {
        // System status
        if (data.status === 'operational') {
            this.systemStatus.textContent = 'Operational';
            this.systemStatus.className = 'px-2 py-1 text-xs rounded-full bg-green-100 text-green-800';
        } else {
            this.systemStatus.textContent = 'Error';
            this.systemStatus.className = 'px-2 py-1 text-xs rounded-full bg-red-100 text-red-800';
        }
        
        // Active provider
        this.activeProvider.textContent = data.active_provider || 'None';
        
        // Check if any providers are available
        const availableProviders = Object.values(data.providers || {}).filter(p => p.valid);
        if (availableProviders.length === 0) {
            this.addChatMessage('system', 'No AI providers are configured. Please configure at least one provider in Settings.');
        }
    }

    async loadAvailableSites() {
        // For now, hardcode the available sites until server restart
        // This will work with the current scraped sites
        const sites = [
            {
                path: 'example-site1.com/timestamp1',
                display_name: 'example-site1.com (timestamp1)'
            },
            {
                path: 'example-site2.com/timestamp2', 
                display_name: 'example-site2.com (timestamp2)'
            },
            {
                path: 'example-site3.com/timestamp3',
                display_name: 'example-site3.com (timestamp3)'
            }
        ];
        
        this.siteSelector.innerHTML = '<option value="">Choose a converted site...</option>';
        
        sites.forEach(site => {
            const option = document.createElement('option');
            option.value = site.path;
            option.textContent = site.display_name;
            this.siteSelector.appendChild(option);
        });
        
        // Add manual entry option
        const manualOption = document.createElement('option');
        manualOption.value = 'manual';
        manualOption.textContent = 'Manual Site Path Entry';
        this.siteSelector.appendChild(manualOption);
    }

    onSiteSelected() {
        const selectedValue = this.siteSelector.value;
        
        if (selectedValue === 'manual') {
            const sitePath = prompt('Enter the site path (e.g., "example.com/20241201_120000"):');
            if (sitePath) {
                this.currentSiteId = sitePath;
                this.analyzeSiteBtn.disabled = false;
                this.chatInput.disabled = false;
                this.sendBtn.disabled = false;
            }
        } else if (selectedValue) {
            this.currentSiteId = selectedValue;
            this.analyzeSiteBtn.disabled = false;
            this.chatInput.disabled = false;
            this.sendBtn.disabled = false;
        } else {
            this.currentSiteId = null;
            this.analyzeSiteBtn.disabled = true;
            this.chatInput.disabled = true;
            this.sendBtn.disabled = true;
        }
    }

    async analyzeSite() {
        if (!this.currentSiteId) return;
        
        this.showProgress('Analyzing site structure...');
        
        try {
            const response = await fetch(`/ai/analyze/${this.currentSiteId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    site_url: '' // Could be extracted from site metadata
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.currentSiteId = data.site_id;
                this.memoryStatus.textContent = `${data.pages_found} pages`;
                this.memoryStatus.className = 'px-2 py-1 text-xs rounded-full bg-green-100 text-green-800';
                
                this.addChatMessage('system', `Site analyzed successfully! Found ${data.pages_found} pages and detected ${data.components_detected} components. Technology stack: ${Object.entries(data.technology_stack).map(([k,v]) => `${k}: ${v}`).join(', ')}`);
                
                // Show memory browser
                this.memoryBrowser.classList.remove('hidden');
                this.loadMemoryContent();
            } else {
                this.addChatMessage('error', `Error analyzing site: ${data.error}`);
            }
        } catch (error) {
            console.error('Error analyzing site:', error);
            this.addChatMessage('error', 'Failed to analyze site. Please try again.');
        } finally {
            this.hideProgress();
        }
    }

    async onChatSubmit(e) {
        e.preventDefault();
        
        if (this.isProcessing) return;
        
        const userRequest = this.chatInput.value.trim();
        if (!userRequest || !this.currentSiteId) return;
        
        this.isProcessing = true;
        this.addChatMessage('user', userRequest);
        this.chatInput.value = '';
        this.chatInput.disabled = true;
        this.sendBtn.disabled = true;
        
        const autoExecute = this.autoExecuteCheckbox.checked;
        
        try {
            this.addChatMessage('system', 'Creating workflow plan...');
            
            const response = await fetch('/ai/workflow/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    site_id: this.currentSiteId,
                    user_request: userRequest
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.currentSessionId = data.session_id;
                
                // Join workflow session for real-time updates
                this.socket.emit('join_workflow_session', { session_id: this.currentSessionId });
                
                this.addChatMessage('assistant', `Created workflow with ${data.tasks_count} tasks.`);
                this.displayTasks(data.tasks);
                
                if (autoExecute) {
                    this.executeWorkflow();
                } else {
                    this.addChatMessage('system', 'Review the tasks and click "Execute Workflow" when ready.');
                }
            } else {
                this.addChatMessage('error', `Error creating workflow: ${data.error}`);
            }
        } catch (error) {
            console.error('Error creating workflow:', error);
            this.addChatMessage('error', 'Failed to create workflow. Please try again.');
        } finally {
            this.isProcessing = false;
            this.chatInput.disabled = false;
            this.sendBtn.disabled = false;
        }
    }

    async executeWorkflow() {
        if (!this.currentSessionId) return;
        
        this.showProgress('Executing workflow...');
        
        try {
            const response = await fetch(`/ai/workflow/${this.currentSessionId}/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    auto_execute: true
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.addChatMessage('assistant', `Workflow execution ${data.status}. ${data.progress.completed} tasks completed, ${data.progress.failed} failed.`);
                
                if (data.results && data.results.length > 0) {
                    data.results.forEach(result => {
                        if (result.success) {
                            this.addChatMessage('success', `✅ ${result.description}`);
                        } else {
                            this.addChatMessage('error', `❌ ${result.description}: ${result.message}`);
                        }
                    });
                }
            } else {
                this.addChatMessage('error', `Error executing workflow: ${data.error}`);
            }
        } catch (error) {
            console.error('Error executing workflow:', error);
            this.addChatMessage('error', 'Failed to execute workflow. Please try again.');
        } finally {
            this.hideProgress();
        }
    }

    displayTasks(tasks) {
        const todoList = document.getElementById('todo-list');
        const todoActions = document.getElementById('todo-actions');
        
        if (tasks.length === 0) {
            todoList.innerHTML = '<div class="text-center text-gray-500 text-sm">No tasks generated</div>';
            todoActions.classList.add('hidden');
            return;
        }
        
        todoList.innerHTML = '';
        tasks.forEach(task => {
            const taskElement = this.createTaskElement(task);
            todoList.appendChild(taskElement);
        });
        
        todoActions.classList.remove('hidden');
        
        // Setup execute workflow button
        const executeBtn = document.getElementById('execute-workflow-btn');
        executeBtn.onclick = () => this.executeWorkflow();
    }

    createTaskElement(task) {
        const element = document.createElement('div');
        element.className = 'border border-gray-200 rounded p-3 mb-2';
        
        const priorityColor = {
            'low': 'text-green-600',
            'medium': 'text-yellow-600', 
            'high': 'text-orange-600',
            'critical': 'text-red-600'
        }[task.priority] || 'text-gray-600';
        
        element.innerHTML = `
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <p class="font-medium text-sm text-gray-900">${task.description}</p>
                    <div class="flex items-center space-x-2 mt-1">
                        <span class="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">${task.task_type}</span>
                        <span class="px-2 py-1 text-xs rounded-full ${priorityColor} bg-gray-50">${task.priority}</span>
                        <span class="text-xs text-gray-500">${task.estimated_complexity} complexity</span>
                    </div>
                    ${task.files_affected.length > 0 ? `
                        <div class="mt-1">
                            <span class="text-xs text-gray-500">Files: ${task.files_affected.join(', ')}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        return element;
    }

    addChatMessage(type, content) {
        const messageElement = document.createElement('div');
        messageElement.className = 'flex space-x-3';
        
        let iconClass, textClass, bgClass;
        switch (type) {
            case 'user':
                iconClass = '👤';
                textClass = 'text-gray-900';
                bgClass = 'bg-blue-50 border-blue-200';
                break;
            case 'assistant':
                iconClass = '🤖';
                textClass = 'text-gray-900';
                bgClass = 'bg-green-50 border-green-200';
                break;
            case 'system':
                iconClass = 'ℹ️';
                textClass = 'text-gray-700';
                bgClass = 'bg-gray-50 border-gray-200';
                break;
            case 'error':
                iconClass = '❌';
                textClass = 'text-red-700';
                bgClass = 'bg-red-50 border-red-200';
                break;
            case 'success':
                iconClass = '✅';
                textClass = 'text-green-700';
                bgClass = 'bg-green-50 border-green-200';
                break;
            default:
                iconClass = '💬';
                textClass = 'text-gray-900';
                bgClass = 'bg-gray-50 border-gray-200';
        }
        
        messageElement.innerHTML = `
            <div class="flex-shrink-0">
                <span class="text-lg">${iconClass}</span>
            </div>
            <div class="flex-1 ${bgClass} border rounded-lg p-3">
                <p class="${textClass} text-sm">${content}</p>
                <span class="text-xs text-gray-500">${new Date().toLocaleTimeString()}</span>
            </div>
        `;
        
        this.chatMessages.appendChild(messageElement);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    async loadMemoryContent() {
        if (!this.currentSiteId) return;
        
        try {
            const response = await fetch(`/ai/memory/${this.currentSiteId}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayMemoryContent(data);
            }
        } catch (error) {
            console.error('Error loading memory content:', error);
        }
    }

    displayMemoryContent(memory) {
        this.memoryContent.innerHTML = `
            <div class="space-y-2 text-xs">
                <div><strong>Pages:</strong> ${Object.keys(memory.pages).length}</div>
                <div><strong>Components:</strong> ${Object.keys(memory.components).join(', ') || 'None'}</div>
                <div><strong>Framework:</strong> ${memory.technology_stack.css_framework || 'Unknown'}</div>
                <div><strong>Created:</strong> ${new Date(memory.created_at).toLocaleDateString()}</div>
            </div>
        `;
    }

    handleWorkflowUpdate(data) {
        // Handle real-time workflow updates
        this.addChatMessage('system', `Workflow update: ${data.message || 'Task progress updated'}`);
    }

    showProgress(message) {
        this.progressText.textContent = message;
        this.progressModal.classList.remove('hidden');
        this.progressModal.classList.add('flex');
    }

    hideProgress() {
        this.progressModal.classList.add('hidden');
        this.progressModal.classList.remove('flex');
    }

    updateProgress(data) {
        if (data.percentage !== undefined) {
            this.progressBar.style.width = `${data.percentage}%`;
        }
        if (data.message) {
            this.progressText.textContent = data.message;
        }
    }

    async openConfigModal() {
        this.configModal.classList.remove('hidden');
        this.configModal.classList.add('flex');
        
        try {
            const response = await fetch('/ai/config');
            const data = await response.json();
            
            this.displayConfigContent(data);
        } catch (error) {
            console.error('Error loading config:', error);
        }
    }

    closeConfigModal() {
        this.configModal.classList.add('hidden');
        this.configModal.classList.remove('flex');
    }

    displayConfigContent(config) {
        const configContent = document.getElementById('config-content');
        
        let providersHtml = '';
        Object.entries(config.providers).forEach(([name, providerConfig]) => {
            providersHtml += `
                <div class="border border-gray-200 rounded p-4 mb-4">
                    <h4 class="font-semibold text-gray-900 mb-2">${name.charAt(0).toUpperCase() + name.slice(1)}</h4>
                    <div class="space-y-2">
                        <div><strong>Models:</strong></div>
                        <ul class="ml-4 text-sm text-gray-600">
                            <li>Planning: ${providerConfig.models?.planning || 'Not configured'}</li>
                            <li>Coding: ${providerConfig.models?.coding || 'Not configured'}</li>
                            <li>Analysis: ${providerConfig.models?.analysis || 'Not configured'}</li>
                        </ul>
                    </div>
                </div>
            `;
        });
        
        configContent.innerHTML = `
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Active Provider</label>
                    <select id="active-provider-select" class="w-full border border-gray-300 rounded p-2">
                        ${Object.keys(config.providers).map(name => 
                            `<option value="${name}" ${name === config.active_provider ? 'selected' : ''}>${name}</option>`
                        ).join('')}
                    </select>
                </div>
                <div>
                    <h4 class="font-semibold text-gray-900 mb-2">Provider Configurations</h4>
                    ${providersHtml}
                </div>
                <div class="flex justify-end">
                    <button id="save-config" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                        Save Configuration
                    </button>
                </div>
            </div>
        `;
        
        // Add save functionality
        document.getElementById('save-config').addEventListener('click', async () => {
            const activeProvider = document.getElementById('active-provider-select').value;
            
            try {
                const response = await fetch('/ai/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        active_provider: activeProvider
                    })
                });
                
                if (response.ok) {
                    this.closeConfigModal();
                    this.loadAIStatus(); // Refresh status
                } else {
                    alert('Failed to save configuration');
                }
            } catch (error) {
                console.error('Error saving config:', error);
                alert('Error saving configuration');
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aiChat = new AIChatInterface();
});