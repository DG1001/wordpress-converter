/**
 * Memory Viewer JavaScript
 * Handles website memory browsing and visualization
 */

class MemoryViewer {
    constructor() {
        this.memories = [];
        this.currentMemory = null;
        
        this.initializeElements();
        this.loadMemories();
    }

    initializeElements() {
        // Main elements
        this.memoriesList = document.getElementById('memories-list');
        this.memoryDetails = document.getElementById('memory-details');
        this.welcomeState = document.getElementById('welcome-state');
        this.memoryContent = document.getElementById('memory-content');
        
        // Refresh button
        this.refreshBtn = document.getElementById('refresh-memories');
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.loadMemories());
        }
        
        // Delete modal
        this.deleteModal = document.getElementById('delete-modal');
        this.deleteMemoryBtn = document.getElementById('delete-memory-btn');
        this.confirmDeleteBtn = document.getElementById('confirm-delete');
        this.cancelDeleteBtn = document.getElementById('cancel-delete');
        
        this.setupDeleteModal();
    }

    setupDeleteModal() {
        if (this.deleteMemoryBtn) {
            this.deleteMemoryBtn.addEventListener('click', () => this.openDeleteModal());
        }
        
        if (this.confirmDeleteBtn) {
            this.confirmDeleteBtn.addEventListener('click', () => this.confirmDelete());
        }
        
        if (this.cancelDeleteBtn) {
            this.cancelDeleteBtn.addEventListener('click', () => this.closeDeleteModal());
        }
        
        // Close modal when clicking outside
        if (this.deleteModal) {
            this.deleteModal.addEventListener('click', (e) => {
                if (e.target === this.deleteModal) {
                    this.closeDeleteModal();
                }
            });
        }
    }

    async loadMemories() {
        try {
            const response = await fetch('/ai/memory');
            const data = await response.json();
            
            if (response.ok) {
                this.memories = data;
                this.displayMemoriesList();
            } else {
                this.showError(`Error loading memories: ${data.error}`);
            }
        } catch (error) {
            console.error('Error loading memories:', error);
            this.showError('Failed to load memories');
        }
    }

    displayMemoriesList() {
        if (!this.memoriesList) return;
        
        if (this.memories.length === 0) {
            this.memoriesList.innerHTML = `
                <div class="p-4 text-center text-gray-500">
                    No website memories found
                </div>
            `;
            return;
        }
        
        this.memoriesList.innerHTML = '';
        
        this.memories.forEach(memory => {
            const memoryElement = this.createMemoryListItem(memory);
            this.memoriesList.appendChild(memoryElement);
        });
    }

    createMemoryListItem(memory) {
        const element = document.createElement('div');
        element.className = 'p-4 hover:bg-gray-50 cursor-pointer';
        element.dataset.siteId = memory.site_id;
        
        element.innerHTML = `
            <div class="space-y-2">
                <div class="font-medium text-sm text-gray-900 truncate">
                    ${memory.site_url || 'Unknown Site'}
                </div>
                <div class="text-xs text-gray-500">
                    ${memory.page_count} pages
                </div>
                <div class="text-xs text-gray-400">
                    Created: ${new Date(memory.created_at).toLocaleDateString()}
                </div>
            </div>
        `;
        
        element.addEventListener('click', () => this.selectMemory(memory.site_id));
        
        return element;
    }

    async selectMemory(siteId) {
        try {
            const response = await fetch(`/ai/memory/${siteId}`);
            const data = await response.json();
            
            if (response.ok) {
                this.currentMemory = data;
                this.displayMemoryDetails(data);
                this.highlightSelectedMemory(siteId);
            } else {
                this.showError(`Error loading memory: ${data.error}`);
            }
        } catch (error) {
            console.error('Error loading memory details:', error);
            this.showError('Failed to load memory details');
        }
    }

    highlightSelectedMemory(siteId) {
        // Remove previous selection
        const previousSelected = this.memoriesList.querySelector('.bg-blue-50');
        if (previousSelected) {
            previousSelected.classList.remove('bg-blue-50', 'border-blue-200');
        }
        
        // Highlight new selection
        const selected = this.memoriesList.querySelector(`[data-site-id="${siteId}"]`);
        if (selected) {
            selected.classList.add('bg-blue-50', 'border-blue-200');
        }
    }

    displayMemoryDetails(memory) {
        if (!this.memoryContent || !this.welcomeState) return;
        
        // Hide welcome state, show memory content
        this.welcomeState.classList.add('hidden');
        this.memoryContent.classList.remove('hidden');
        
        // Update overview
        this.updateOverview(memory);
        
        // Update technology stack
        this.updateTechnologyStack(memory.technology_stack);
        
        // Update pages analysis
        this.updatePagesAnalysis(memory.pages);
        
        // Update components
        this.updateComponents(memory.components);
        
        // Update navigation structure
        this.updateNavigationStructure(memory.navigation_structure);
        
        // Update content patterns
        this.updateContentPatterns(memory.content_patterns);
        
        // Update file structure
        this.updateFileStructure(memory.file_structure);
    }

    updateOverview(memory) {
        // Site URL
        const siteUrlElement = document.getElementById('memory-site-url');
        if (siteUrlElement) {
            siteUrlElement.textContent = memory.site_url || 'Unknown Site';
        }
        
        // Created date
        const createdElement = document.getElementById('memory-created');
        if (createdElement) {
            createdElement.textContent = new Date(memory.created_at).toLocaleDateString();
        }
        
        // Counts
        const pagesCount = document.getElementById('pages-count');
        if (pagesCount) {
            pagesCount.textContent = Object.keys(memory.pages).length;
        }
        
        const componentsCount = document.getElementById('components-count');
        if (componentsCount) {
            componentsCount.textContent = Object.keys(memory.components).length;
        }
        
        const totalFiles = document.getElementById('total-files');
        if (totalFiles) {
            totalFiles.textContent = memory.file_structure?.total_files || 0;
        }
        
        const cssFramework = document.getElementById('css-framework');
        if (cssFramework) {
            cssFramework.textContent = memory.technology_stack?.css_framework || 'Unknown';
        }
    }

    updateTechnologyStack(techStack) {
        const techStackElement = document.getElementById('tech-stack');
        if (!techStackElement) return;
        
        techStackElement.innerHTML = '';
        
        Object.entries(techStack).forEach(([key, value]) => {
            const item = document.createElement('div');
            item.className = 'bg-gray-50 p-3 rounded';
            item.innerHTML = `
                <div class="font-medium text-sm text-gray-900 capitalize">${key.replace('_', ' ')}</div>
                <div class="text-sm text-gray-600">${Array.isArray(value) ? value.join(', ') : value}</div>
            `;
            techStackElement.appendChild(item);
        });
    }

    updatePagesAnalysis(pages) {
        const pagesTable = document.getElementById('pages-table');
        if (!pagesTable) return;
        
        pagesTable.innerHTML = '';
        
        Object.entries(pages).forEach(([path, pageInfo]) => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50';
            
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${path}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${pageInfo.title || 'No title'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${pageInfo.word_count || 0}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${pageInfo.internal_links || 0}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${pageInfo.images || 0}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    ${pageInfo.has_forms ? '✅' : '❌'}
                </td>
            `;
            
            pagesTable.appendChild(row);
        });
    }

    updateComponents(components) {
        const componentsList = document.getElementById('components-list');
        if (!componentsList) return;
        
        if (Object.keys(components).length === 0) {
            componentsList.innerHTML = `
                <div class="text-center text-gray-500 text-sm">
                    No components detected
                </div>
            `;
            return;
        }
        
        componentsList.innerHTML = '';
        
        Object.entries(components).forEach(([name, component]) => {
            const item = document.createElement('div');
            item.className = 'bg-gray-50 p-3 rounded';
            
            item.innerHTML = `
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="font-medium text-sm text-gray-900 capitalize">${name}</div>
                        <div class="text-sm text-gray-600">Type: ${component.type}</div>
                        <div class="text-sm text-gray-600">Found on ${component.pages_found} pages</div>
                    </div>
                </div>
            `;
            
            componentsList.appendChild(item);
        });
    }

    updateNavigationStructure(navStructure) {
        const navElement = document.getElementById('navigation-structure');
        if (!navElement) return;
        
        navElement.innerHTML = '';
        
        // Main pages
        if (navStructure.main_pages && navStructure.main_pages.length > 0) {
            const mainPagesDiv = document.createElement('div');
            mainPagesDiv.className = 'mb-4';
            mainPagesDiv.innerHTML = `
                <h4 class="font-medium text-gray-900 mb-2">Main Navigation Pages</h4>
                <div class="bg-gray-50 p-3 rounded">
                    <ul class="list-disc list-inside text-sm text-gray-600">
                        ${navStructure.main_pages.map(page => `<li>${page}</li>`).join('')}
                    </ul>
                </div>
            `;
            navElement.appendChild(mainPagesDiv);
        }
        
        // Orphaned pages
        if (navStructure.orphaned_pages && navStructure.orphaned_pages.length > 0) {
            const orphanedDiv = document.createElement('div');
            orphanedDiv.innerHTML = `
                <h4 class="font-medium text-gray-900 mb-2">Orphaned Pages</h4>
                <div class="bg-yellow-50 p-3 rounded border border-yellow-200">
                    <ul class="list-disc list-inside text-sm text-gray-600">
                        ${navStructure.orphaned_pages.map(page => `<li>${page}</li>`).join('')}
                    </ul>
                </div>
            `;
            navElement.appendChild(orphanedDiv);
        }
    }

    updateContentPatterns(contentPatterns) {
        const patternsElement = document.getElementById('content-patterns');
        if (!patternsElement) return;
        
        patternsElement.innerHTML = '';
        
        // Common headings
        if (contentPatterns.common_headings) {
            const headingsDiv = document.createElement('div');
            headingsDiv.className = 'bg-gray-50 p-3 rounded';
            headingsDiv.innerHTML = `
                <h4 class="font-medium text-gray-900 mb-2">Common Headings</h4>
                <div class="text-sm text-gray-600">
                    ${Object.entries(contentPatterns.common_headings)
                        .map(([heading, count]) => `<div>${heading} (${count} times)</div>`)
                        .join('')}
                </div>
            `;
            patternsElement.appendChild(headingsDiv);
        }
        
        // Page types
        if (contentPatterns.page_types) {
            const typesDiv = document.createElement('div');
            typesDiv.className = 'bg-gray-50 p-3 rounded';
            typesDiv.innerHTML = `
                <h4 class="font-medium text-gray-900 mb-2">Page Types by Content Length</h4>
                <div class="text-sm text-gray-600">
                    ${Object.entries(contentPatterns.page_types)
                        .map(([type, pages]) => `<div>${type}: ${pages.length} pages</div>`)
                        .join('')}
                </div>
            `;
            patternsElement.appendChild(typesDiv);
        }
        
        // Form pages
        if (contentPatterns.form_pages && contentPatterns.form_pages.length > 0) {
            const formsDiv = document.createElement('div');
            formsDiv.className = 'bg-blue-50 p-3 rounded border border-blue-200';
            formsDiv.innerHTML = `
                <h4 class="font-medium text-gray-900 mb-2">Pages with Forms</h4>
                <div class="text-sm text-gray-600">
                    ${contentPatterns.form_pages.map(page => `<div>${page}</div>`).join('')}
                </div>
            `;
            patternsElement.appendChild(formsDiv);
        }
    }

    updateFileStructure(fileStructure) {
        const structureElement = document.getElementById('file-structure');
        if (!structureElement) return;
        
        structureElement.innerHTML = '';
        
        // File statistics
        const statsDiv = document.createElement('div');
        statsDiv.className = 'bg-gray-50 p-4 rounded';
        statsDiv.innerHTML = `
            <h4 class="font-medium text-gray-900 mb-2">File Statistics</h4>
            <div class="grid grid-cols-2 gap-2 text-sm">
                <div>Total Files: ${fileStructure.total_files || 0}</div>
                <div>Directories: ${fileStructure.directories?.length || 0}</div>
            </div>
        `;
        
        if (fileStructure.file_types) {
            const typesHtml = Object.entries(fileStructure.file_types)
                .map(([ext, count]) => `<div>${ext || 'no extension'}: ${count}</div>`)
                .join('');
            statsDiv.innerHTML += `
                <div class="mt-2">
                    <strong>File Types:</strong>
                    <div class="mt-1">${typesHtml}</div>
                </div>
            `;
        }
        
        structureElement.appendChild(statsDiv);
        
        // Assets breakdown
        if (fileStructure.assets) {
            const assetsDiv = document.createElement('div');
            assetsDiv.className = 'bg-gray-50 p-4 rounded';
            assetsDiv.innerHTML = `
                <h4 class="font-medium text-gray-900 mb-2">Assets Breakdown</h4>
                <div class="space-y-1 text-sm">
                    <div>Images: ${fileStructure.assets.images?.length || 0}</div>
                    <div>Scripts: ${fileStructure.assets.scripts?.length || 0}</div>
                    <div>Stylesheets: ${fileStructure.assets.styles?.length || 0}</div>
                    <div>Other: ${fileStructure.assets.other?.length || 0}</div>
                </div>
            `;
            structureElement.appendChild(assetsDiv);
        }
    }

    openDeleteModal() {
        if (this.deleteModal) {
            this.deleteModal.classList.remove('hidden');
            this.deleteModal.classList.add('flex');
        }
    }

    closeDeleteModal() {
        if (this.deleteModal) {
            this.deleteModal.classList.add('hidden');
            this.deleteModal.classList.remove('flex');
        }
    }

    async confirmDelete() {
        if (!this.currentMemory) return;
        
        try {
            const response = await fetch(`/ai/memory/${this.currentMemory.site_id}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Memory deleted successfully');
                this.closeDeleteModal();
                
                // Reset view
                this.currentMemory = null;
                this.welcomeState.classList.remove('hidden');
                this.memoryContent.classList.add('hidden');
                
                // Reload memories list
                this.loadMemories();
            } else {
                this.showError(`Error deleting memory: ${data.error}`);
            }
        } catch (error) {
            console.error('Error deleting memory:', error);
            this.showError('Failed to delete memory');
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
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
            'info': 'bg-blue-500 text-white'
        };
        return classes[type] || classes['info'];
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.memoryViewer = new MemoryViewer();
});