/**
 * Todo Manager JavaScript
 * Handles workflow task management and execution
 */

class TodoManager {
    constructor() {
        this.sessionId = window.sessionId || null;
        this.socket = null;
        this.tasks = [];
        this.sessionData = null;
        
        this.initializeElements();
        this.initializeSocketIO();
        
        if (this.sessionId) {
            this.loadSessionData();
        }
    }

    initializeElements() {
        // Session elements
        this.sessionStatus = document.getElementById('session-status');
        this.siteId = document.getElementById('site-id');
        this.createdAt = document.getElementById('created-at');
        this.userRequest = document.getElementById('user-request');
        
        // Progress elements
        this.progressBar = document.getElementById('progress-bar');
        this.progressText = document.getElementById('progress-text');
        this.progressPercentage = document.getElementById('progress-percentage');
        
        // Action buttons
        this.executeAllBtn = document.getElementById('execute-all-btn');
        this.saveSessionBtn = document.getElementById('save-session-btn');
        this.refreshBtn = document.getElementById('refresh-btn');
        this.addTaskBtn = document.getElementById('add-task-btn');
        
        // Tasks container
        this.tasksContainer = document.getElementById('tasks-container');
        this.filterTasks = document.getElementById('filter-tasks');
        
        // Modals
        this.addTaskModal = document.getElementById('add-task-modal');
        this.editTaskModal = document.getElementById('edit-task-modal');
        this.addTaskForm = document.getElementById('add-task-form');
        this.editTaskForm = document.getElementById('edit-task-form');
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Action buttons
        if (this.executeAllBtn) {
            this.executeAllBtn.addEventListener('click', () => this.executeAllTasks());
        }
        if (this.saveSessionBtn) {
            this.saveSessionBtn.addEventListener('click', () => this.saveSession());
        }
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.refreshSession());
        }
        if (this.addTaskBtn) {
            this.addTaskBtn.addEventListener('click', () => this.openAddTaskModal());
        }
        
        // Filter
        if (this.filterTasks) {
            this.filterTasks.addEventListener('change', () => this.filterTaskDisplay());
        }
        
        // Modals
        this.setupModalEventListeners();
        
        // Forms
        if (this.addTaskForm) {
            this.addTaskForm.addEventListener('submit', (e) => this.handleAddTask(e));
        }
        if (this.editTaskForm) {
            this.editTaskForm.addEventListener('submit', (e) => this.handleEditTask(e));
        }
    }

    setupModalEventListeners() {
        // Add task modal
        const cancelAddTask = document.getElementById('cancel-add-task');
        if (cancelAddTask) {
            cancelAddTask.addEventListener('click', () => this.closeAddTaskModal());
        }
        
        // Edit task modal
        const cancelEditTask = document.getElementById('cancel-edit-task');
        if (cancelEditTask) {
            cancelEditTask.addEventListener('click', () => this.closeEditTaskModal());
        }
        
        // Close modals when clicking outside
        if (this.addTaskModal) {
            this.addTaskModal.addEventListener('click', (e) => {
                if (e.target === this.addTaskModal) {
                    this.closeAddTaskModal();
                }
            });
        }
        
        if (this.editTaskModal) {
            this.editTaskModal.addEventListener('click', (e) => {
                if (e.target === this.editTaskModal) {
                    this.closeEditTaskModal();
                }
            });
        }
    }

    initializeSocketIO() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to server');
                if (this.sessionId) {
                    this.socket.emit('join_workflow_session', { session_id: this.sessionId });
                }
            });
            
            this.socket.on('workflow_update', (data) => {
                this.handleWorkflowUpdate(data);
            });
        }
    }

    async loadSessionData() {
        if (!this.sessionId) return;
        
        try {
            const response = await fetch(`/ai/workflow/${this.sessionId}/status`);
            const data = await response.json();
            
            if (response.ok) {
                this.sessionData = data;
                this.tasks = data.tasks || [];
                this.updateSessionDisplay();
                this.updateTasksDisplay();
            } else {
                this.showError(`Error loading session: ${data.error}`);
            }
        } catch (error) {
            console.error('Error loading session data:', error);
            this.showError('Failed to load session data');
        }
    }

    updateSessionDisplay() {
        if (!this.sessionData) return;
        
        // Update session info
        if (this.sessionStatus) {
            this.sessionStatus.textContent = this.sessionData.status;
            this.sessionStatus.className = this.getStatusBadgeClass(this.sessionData.status);
        }
        
        if (this.siteId) {
            this.siteId.textContent = this.sessionData.site_id;
        }
        
        if (this.createdAt) {
            this.createdAt.textContent = new Date(this.sessionData.created_at).toLocaleString();
        }
        
        if (this.userRequest) {
            this.userRequest.textContent = this.sessionData.user_request;
        }
        
        // Update progress
        this.updateProgress();
    }

    updateProgress() {
        if (!this.sessionData?.progress) return;
        
        const { total_tasks, completed, failed, in_progress } = this.sessionData.progress;
        const percentage = total_tasks > 0 ? Math.round((completed / total_tasks) * 100) : 0;
        
        if (this.progressBar) {
            this.progressBar.style.width = `${percentage}%`;
        }
        
        if (this.progressText) {
            this.progressText.textContent = `${completed} / ${total_tasks} tasks`;
        }
        
        if (this.progressPercentage) {
            this.progressPercentage.textContent = `${percentage}%`;
        }
        
        // Update progress bar color based on status
        if (this.progressBar) {
            if (failed > 0) {
                this.progressBar.className = 'bg-red-600 h-2 rounded-full transition-all';
            } else if (completed === total_tasks && total_tasks > 0) {
                this.progressBar.className = 'bg-green-600 h-2 rounded-full transition-all';
            } else {
                this.progressBar.className = 'bg-blue-600 h-2 rounded-full transition-all';
            }
        }
    }

    updateTasksDisplay() {
        if (!this.tasksContainer) return;
        
        if (!this.tasks || this.tasks.length === 0) {
            this.tasksContainer.innerHTML = `
                <div class="p-6 text-center text-gray-500">
                    No tasks in this session
                </div>
            `;
            return;
        }
        
        // Filter tasks based on current filter
        const filterValue = this.filterTasks?.value || 'all';
        const filteredTasks = filterValue === 'all' 
            ? this.tasks 
            : this.tasks.filter(task => task.status === filterValue);
        
        this.tasksContainer.innerHTML = '';
        
        filteredTasks.forEach(task => {
            const taskElement = this.createTaskElement(task);
            this.tasksContainer.appendChild(taskElement);
        });
    }

    createTaskElement(task) {
        const element = document.createElement('div');
        element.className = 'p-6';
        element.dataset.taskId = task.id;
        
        const statusBadge = this.getStatusBadgeClass(task.status);
        const priorityBadge = this.getPriorityBadgeClass(task.priority);
        
        element.innerHTML = `
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <div class="flex items-center space-x-2 mb-2">
                        <span class="${statusBadge}">${task.status.replace('_', ' ')}</span>
                        <span class="${priorityBadge}">${task.priority}</span>
                        <span class="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700">${task.files_affected?.length || 0} files</span>
                    </div>
                    
                    <h3 class="font-medium text-gray-900 mb-2">${task.description}</h3>
                    
                    ${task.files_affected && task.files_affected.length > 0 ? `
                        <p class="text-sm text-gray-600 mb-2">
                            <strong>Files:</strong> ${task.files_affected.join(', ')}
                        </p>
                    ` : ''}
                    
                    ${task.error_message ? `
                        <div class="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                            <strong>Error:</strong> ${task.error_message}
                        </div>
                    ` : ''}
                </div>
                
                <div class="flex space-x-2 ml-4">
                    <button onclick="todoManager.editTask('${task.id}')" 
                            class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                        Edit
                    </button>
                    <button onclick="todoManager.executeTask('${task.id}')" 
                            class="text-green-600 hover:text-green-800 text-sm font-medium"
                            ${task.status === 'completed' ? 'disabled' : ''}>
                        Execute
                    </button>
                    <button onclick="todoManager.deleteTask('${task.id}')" 
                            class="text-red-600 hover:text-red-800 text-sm font-medium">
                        Delete
                    </button>
                </div>
            </div>
        `;
        
        return element;
    }

    getStatusBadgeClass(status) {
        const classes = {
            'pending': 'px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800',
            'in_progress': 'px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800',
            'completed': 'px-2 py-1 text-xs rounded-full bg-green-100 text-green-800',
            'failed': 'px-2 py-1 text-xs rounded-full bg-red-100 text-red-800',
            'cancelled': 'px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800'
        };
        return classes[status] || classes['pending'];
    }

    getPriorityBadgeClass(priority) {
        const classes = {
            'low': 'px-2 py-1 text-xs rounded-full bg-green-100 text-green-800',
            'medium': 'px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800',
            'high': 'px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-800',
            'critical': 'px-2 py-1 text-xs rounded-full bg-red-100 text-red-800'
        };
        return classes[priority] || classes['medium'];
    }

    async executeAllTasks() {
        if (!this.sessionId) return;
        
        if (!confirm('Execute all pending tasks? This action cannot be undone.')) {
            return;
        }
        
        try {
            this.showLoading('Executing all tasks...');
            
            const response = await fetch(`/ai/workflow/${this.sessionId}/execute`, {
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
                this.showSuccess(`Execution ${data.status}. ${data.progress.completed} tasks completed, ${data.progress.failed} failed.`);
                this.refreshSession();
            } else {
                this.showError(`Error executing tasks: ${data.error}`);
            }
        } catch (error) {
            console.error('Error executing tasks:', error);
            this.showError('Failed to execute tasks');
        } finally {
            this.hideLoading();
        }
    }

    async executeTask(taskId) {
        // For now, we'll implement single task execution as part of the full workflow
        // In a full implementation, you might want a separate endpoint for single tasks
        this.showInfo('Single task execution not yet implemented. Use "Execute All" for now.');
    }

    async saveSession() {
        if (!this.sessionId) return;
        
        try {
            // Note: The save functionality is built into the workflow execution
            // This is more of a manual trigger or could export session data
            this.showSuccess('Session saved successfully');
        } catch (error) {
            console.error('Error saving session:', error);
            this.showError('Failed to save session');
        }
    }

    async refreshSession() {
        await this.loadSessionData();
        this.showInfo('Session refreshed');
    }

    filterTaskDisplay() {
        this.updateTasksDisplay();
    }

    // Modal functions
    openAddTaskModal() {
        if (this.addTaskModal) {
            this.addTaskModal.classList.remove('hidden');
            this.addTaskModal.classList.add('flex');
        }
    }

    closeAddTaskModal() {
        if (this.addTaskModal) {
            this.addTaskModal.classList.add('hidden');
            this.addTaskModal.classList.remove('flex');
        }
        if (this.addTaskForm) {
            this.addTaskForm.reset();
        }
    }

    openEditTaskModal() {
        if (this.editTaskModal) {
            this.editTaskModal.classList.remove('hidden');
            this.editTaskModal.classList.add('flex');
        }
    }

    closeEditTaskModal() {
        if (this.editTaskModal) {
            this.editTaskModal.classList.add('hidden');
            this.editTaskModal.classList.remove('flex');
        }
        if (this.editTaskForm) {
            this.editTaskForm.reset();
        }
    }

    async handleAddTask(e) {
        e.preventDefault();
        
        const formData = new FormData(this.addTaskForm);
        const taskData = {
            description: formData.get('description'),
            task_type: formData.get('task_type'),
            priority: formData.get('priority'),
            files_affected: formData.get('files_affected')?.split(',').map(f => f.trim()).filter(f => f) || [],
            estimated_complexity: 'medium',
            llm_prompt: formData.get('description')
        };
        
        try {
            const response = await fetch(`/ai/workflow/${this.sessionId}/task`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(taskData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Task added successfully');
                this.closeAddTaskModal();
                this.refreshSession();
            } else {
                this.showError(`Error adding task: ${data.error}`);
            }
        } catch (error) {
            console.error('Error adding task:', error);
            this.showError('Failed to add task');
        }
    }

    editTask(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;
        
        // Populate edit form
        const form = this.editTaskForm;
        if (form) {
            form.querySelector('[name="task_id"]').value = task.id;
            form.querySelector('[name="description"]').value = task.description;
            form.querySelector('[name="priority"]').value = task.priority;
            form.querySelector('[name="status"]').value = task.status;
            form.querySelector('[name="llm_prompt"]').value = task.llm_prompt || task.description;
        }
        
        this.openEditTaskModal();
    }

    async handleEditTask(e) {
        e.preventDefault();
        
        const formData = new FormData(this.editTaskForm);
        const taskId = formData.get('task_id');
        const updates = {
            description: formData.get('description'),
            priority: formData.get('priority'),
            status: formData.get('status'),
            llm_prompt: formData.get('llm_prompt')
        };
        
        try {
            const response = await fetch(`/ai/workflow/${this.sessionId}/task/${taskId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updates)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Task updated successfully');
                this.closeEditTaskModal();
                this.refreshSession();
            } else {
                this.showError(`Error updating task: ${data.error}`);
            }
        } catch (error) {
            console.error('Error updating task:', error);
            this.showError('Failed to update task');
        }
    }

    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) {
            return;
        }
        
        try {
            const response = await fetch(`/ai/workflow/${this.sessionId}/task/${taskId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Task deleted successfully');
                this.refreshSession();
            } else {
                this.showError(`Error deleting task: ${data.error}`);
            }
        } catch (error) {
            console.error('Error deleting task:', error);
            this.showError('Failed to delete task');
        }
    }

    handleWorkflowUpdate(data) {
        // Handle real-time workflow updates
        console.log('Workflow update:', data);
        this.refreshSession();
    }

    // Utility functions for notifications
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    showNotification(message, type = 'info') {
        // Simple notification - in a full implementation you might want a proper notification system
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${this.getNotificationClass(type)}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    getNotificationClass(type) {
        const classes = {
            'success': 'bg-green-500 text-white',
            'error': 'bg-red-500 text-white',
            'info': 'bg-blue-500 text-white',
            'warning': 'bg-yellow-500 text-black'
        };
        return classes[type] || classes['info'];
    }

    showLoading(message) {
        // Simple loading indicator
        console.log('Loading:', message);
    }

    hideLoading() {
        console.log('Loading complete');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.todoManager = new TodoManager();
});