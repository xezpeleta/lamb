<script>
	import { onMount } from 'svelte';
	import { getConfig } from '$lib/config';
	import { user } from '$lib/stores/userStore';
	import axios from 'axios';

	let config = {};
	/** @type {any} */
	let mcpStatus = null;
	/** @type {any[]} */
	let mcpPrompts = [];
	/** @type {any[]} */
	let mcpTools = [];
	/** @type {any[]} */
	let mcpResources = [];
	let loading = false;
	/** @type {string | null} */
	let error = null;
	/** @type {any} */
	let selectedPrompt = null;
	/** @type {any} */
	let promptArguments = {};
	/** @type {any} */
	let promptResult = null;
	/** @type {any} */
	let selectedTool = null;
	/** @type {any} */
	let toolArguments = {};
	/** @type {any} */
	let toolResult = null;
	let activeTab = 'prompts';

	onMount(() => {
		config = getConfig();
		loadMcpStatus();
	});

	// Get the MCP base URL
	/**
	 * @param {string} endpoint
	 */
	function getMcpUrl(endpoint) {
		const lambServer = config?.api?.lambServer || 'http://localhost:9099';
		return `${lambServer.replace(/\/$/, '')}/lamb/v1/mcp${endpoint}`;
	}

	// Get API headers with authentication
	function getHeaders() {
		const ltiSecret = config?.api?.ltiSecret || 'pepino-secret-key';
		const userEmail = $user.email || 'test@example.com'; // Get from user store
		
		return {
			'Authorization': `Bearer ${ltiSecret}`,
			'X-User-Email': userEmail,
			'Content-Type': 'application/json'
		};
	}

	async function loadMcpStatus() {
		loading = true;
		error = null;
		try {
			const response = await axios.get(getMcpUrl('/status'), {
				headers: getHeaders()
			});
			mcpStatus = response.data;
		} catch (err) {
			console.error('Error loading MCP status:', err);
			error = err.response?.data?.detail || err.message || 'Failed to load MCP status';
		} finally {
			loading = false;
		}
	}

	async function loadMcpPrompts() {
		activeTab = 'prompts';
		loading = true;
		error = null;
		try {
			const response = await axios.get(getMcpUrl('/prompts'), {
				headers: getHeaders()
			});
			mcpPrompts = response.data.prompts || [];
		} catch (err) {
			console.error('Error loading MCP prompts:', err);
			error = err.response?.data?.detail || err.message || 'Failed to load MCP prompts';
		} finally {
			loading = false;
		}
	}

	async function loadMcpTools() {
		activeTab = 'tools';
		loading = true;
		error = null;
		try {
			const response = await axios.get(getMcpUrl('/tools'), {
				headers: getHeaders()
			});
			mcpTools = response.data.tools || [];
		} catch (err) {
			console.error('Error loading MCP tools:', err);
			error = err.response?.data?.detail || err.message || 'Failed to load MCP tools';
		} finally {
			loading = false;
		}
	}

	async function loadMcpResources() {
		activeTab = 'resources';
		loading = true;
		error = null;
		try {
			const response = await axios.get(getMcpUrl('/resources'), {
				headers: getHeaders()
			});
			mcpResources = response.data.resources || [];
		} catch (err) {
			console.error('Error loading MCP resources:', err);
			error = err.response?.data?.detail || err.message || 'Failed to load MCP resources';
		} finally {
			loading = false;
		}
	}

	async function testPrompt() {
		if (!selectedPrompt) return;
		
		loading = true;
		error = null;
		try {
			const response = await axios.post(getMcpUrl('/prompts/get'), {
				name: selectedPrompt.name,
				arguments: promptArguments
			}, {
				headers: getHeaders()
			});
			promptResult = response.data;
		} catch (err) {
			console.error('Error testing prompt:', err);
			error = err.response?.data?.detail || err.message || 'Failed to test prompt';
		} finally {
			loading = false;
		}
	}

	async function testTool() {
		if (!selectedTool) return;
		
		loading = true;
		error = null;
		try {
			const response = await axios.post(getMcpUrl('/tools/call'), {
				name: selectedTool.name,
				arguments: toolArguments
			}, {
				headers: getHeaders()
			});
			toolResult = response.data;
		} catch (err) {
			console.error('Error testing tool:', err);
			error = err.response?.data?.detail || err.message || 'Failed to test tool';
		} finally {
			loading = false;
		}
	}

	/**
	 * @param {any} prompt
	 */
	function selectPrompt(prompt) {
		selectedPrompt = prompt;
		promptArguments = {};
		promptResult = null;
		// Initialize arguments based on prompt schema
		if (prompt.arguments) {
			prompt.arguments.forEach((arg) => {
				promptArguments[arg.name] = '';
			});
		}
	}

	/**
	 * @param {any} tool
	 */
	function selectTool(tool) {
		selectedTool = tool;
		toolArguments = {};
		toolResult = null;
		// Initialize arguments based on tool schema
		if (tool.inputSchema && tool.inputSchema.properties) {
			Object.keys(tool.inputSchema.properties).forEach(key => {
				toolArguments[key] = '';
			});
		}
	}
</script>

<div class="space-y-6">
	<!-- User Authentication Check -->
	{#if !$user.isLoggedIn}
		<div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
			<strong>Authentication Required:</strong> Please log in to access the MCP testing interface.
		</div>
	{:else}

	<!-- Error Display -->
	{#if error}
		<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
			<strong>Error:</strong> {error}
		</div>
	{/if}

	<!-- Loading Indicator -->
	{#if loading}
		<div class="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded">
			Loading...
		</div>
	{/if}

	<!-- MCP Status Section -->
	<div class="bg-white rounded-lg shadow-md p-6">
		<h3 class="text-lg font-semibold text-gray-800 mb-4">MCP Server Status</h3>
		{#if mcpStatus}
			<div class="space-y-3">
				<div class="flex items-center">
					<span class="font-medium text-gray-700 w-24">Status:</span>
					<span class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm">Connected</span>
				</div>
				<div class="flex items-center">
					<span class="font-medium text-gray-700 w-24">Version:</span>
					<span class="text-gray-600">{mcpStatus.version || 'Unknown'}</span>
				</div>
				<div class="flex items-center">
					<span class="font-medium text-gray-700 w-24">Capabilities:</span>
					<div class="flex flex-wrap gap-2">
						{#each (mcpStatus.capabilities || []) as capability}
							<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">{capability}</span>
						{/each}
					</div>
				</div>
			</div>
		{:else}
			<p class="text-gray-500">Loading status...</p>
		{/if}
	</div>

	<!-- Navigation Tabs -->
	<div class="bg-white rounded-lg shadow-md">
		<div class="border-b border-gray-200">
			<nav class="-mb-px flex space-x-8 px-6">
				<button 
					on:click={loadMcpPrompts}
					class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'prompts' ? 'border-[#2271b3] text-[#2271b3]' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				>
					Prompts
				</button>
				<button 
					on:click={loadMcpTools}
					class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'tools' ? 'border-[#2271b3] text-[#2271b3]' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				>
					Tools
				</button>
				<button 
					on:click={loadMcpResources}
					class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'resources' ? 'border-[#2271b3] text-[#2271b3]' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				>
					Resources
				</button>
				<button 
					on:click={() => activeTab = 'setup'}
					class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'setup' ? 'border-[#2271b3] text-[#2271b3]' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				>
					Client Setup
				</button>
			</nav>
		</div>

		<!-- Prompts Section -->
		{#if activeTab === 'prompts'}
			{#if mcpPrompts.length > 0}
				<div class="p-6">
					<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
						<!-- Prompts List -->
						<div>
							<h4 class="font-medium text-gray-700 mb-3">Available Prompts</h4>
							<div class="space-y-2">
								{#each mcpPrompts as prompt}
									<button
										on:click={() => selectPrompt(prompt)}
										class="w-full text-left p-3 border rounded hover:bg-gray-50 {selectedPrompt?.name === prompt.name ? 'border-[#2271b3] bg-blue-50' : 'border-gray-200'}"
									>
										<div class="font-medium">{prompt.name}</div>
										<div class="text-sm text-gray-600">{prompt.description}</div>
									</button>
								{/each}
							</div>
						</div>

						<!-- Prompt Testing -->
						{#if selectedPrompt}
							<div>
								<h4 class="font-medium text-gray-700 mb-2">Test Prompt: {selectedPrompt.name}</h4>
								<div class="space-y-3">
									{#if selectedPrompt.arguments}
										{#each selectedPrompt.arguments as arg}
											<div>
												<label for="prompt-arg-{arg.name}" class="block text-sm font-medium text-gray-700 mb-1">
													{arg.name} {arg.required ? '*' : ''}
												</label>
												<input
													id="prompt-arg-{arg.name}"
													type="text"
													bind:value={promptArguments[arg.name]}
													placeholder={arg.description}
													class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#2271b3] focus:border-transparent"
												/>
											</div>
										{/each}
									{/if}
									<button
										on:click={testPrompt}
										class="bg-[#2271b3] text-white px-4 py-2 rounded hover:bg-[#1e5a8a]"
										disabled={loading}
									>
										Test Prompt
									</button>
								</div>

								{#if promptResult}
									<div class="mt-4">
										<h5 class="font-medium text-gray-700 mb-2">Result:</h5>
										<pre class="bg-gray-100 p-3 rounded text-sm overflow-auto">{JSON.stringify(promptResult, null, 2)}</pre>
									</div>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			{:else}
				<div class="p-6 text-center text-gray-500">
					<p>No prompts available. You need to create assistants first.</p>
				</div>
			{/if}
		{/if}

		<!-- Tools Section -->
		{#if activeTab === 'tools'}
			{#if mcpTools.length > 0}
				<div class="p-6">
					<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
						<!-- Tools List -->
						<div>
							<h4 class="font-medium text-gray-700 mb-3">Available Tools</h4>
							<div class="space-y-2">
								{#each mcpTools as tool}
									<button
										on:click={() => selectTool(tool)}
										class="w-full text-left p-3 border rounded hover:bg-gray-50 {selectedTool?.name === tool.name ? 'border-[#2271b3] bg-blue-50' : 'border-gray-200'}"
									>
										<div class="font-medium">{tool.name}</div>
										<div class="text-sm text-gray-600">{tool.description}</div>
									</button>
								{/each}
							</div>
						</div>

						<!-- Tool Testing -->
						{#if selectedTool}
							<div>
								<h4 class="font-medium text-gray-700 mb-2">Test Tool: {selectedTool.name}</h4>
								<div class="space-y-3">
									{#if selectedTool.inputSchema?.properties}
										{#each Object.entries(selectedTool.inputSchema.properties) as [key, prop]}
											<div>
												<label for="tool-arg-{key}" class="block text-sm font-medium text-gray-700 mb-1">
													{key} {selectedTool.inputSchema.required?.includes(key) ? '*' : ''}
												</label>
												<input
													id="tool-arg-{key}"
													type="text"
													bind:value={toolArguments[key]}
													placeholder={prop.description || ''}
													class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#2271b3] focus:border-transparent"
												/>
											</div>
										{/each}
									{/if}
									<button
										on:click={testTool}
										class="bg-[#2271b3] text-white px-4 py-2 rounded hover:bg-[#1e5a8a]"
										disabled={loading}
									>
										Test Tool
									</button>
								</div>

								{#if toolResult}
									<div class="mt-4">
										<h5 class="font-medium text-gray-700 mb-2">Result:</h5>
										<pre class="bg-gray-100 p-3 rounded text-sm overflow-auto">{JSON.stringify(toolResult, null, 2)}</pre>
									</div>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			{:else}
				<div class="p-6 text-center text-gray-500">
					<p>No tools available yet.</p>
				</div>
			{/if}
		{/if}

		<!-- Resources Section -->
		{#if activeTab === 'resources'}
			{#if mcpResources.length > 0}
				<div class="p-6">
					<h4 class="font-medium text-gray-700 mb-3">Available Resources</h4>
					<div class="space-y-3">
						{#each mcpResources as resource}
							<div class="border rounded p-3">
								<div class="font-medium">{resource.name}</div>
								<div class="text-sm text-gray-600">{resource.description}</div>
								<div class="text-xs text-gray-500 mt-1">URI: {resource.uri}</div>
							</div>
						{/each}
					</div>
				</div>
			{:else}
				<div class="p-6 text-center text-gray-500">
					<p>No resources available yet.</p>
				</div>
			{/if}
		{/if}

		<!-- Setup Section -->
		{#if activeTab === 'setup'}
			<div class="p-6">
				<h4 class="font-medium text-gray-700 mb-3">MCP Client Setup</h4>
				<div class="space-y-4">
					<div class="bg-gray-50 p-4 rounded">
						<h5 class="font-medium mb-2">Server Configuration</h5>
						<pre class="text-sm text-gray-700">{JSON.stringify({
							command: "python",
							args: ["-m", "lamb.mcp_server"],
							env: {
								LAMB_SERVER_URL: config?.api?.lambServer || 'http://localhost:9099',
								LAMB_API_KEY: '***REDACTED***'
							}
						}, null, 2)}</pre>
					</div>
					<div class="text-sm text-gray-600">
						<p>Add this configuration to your MCP client to connect to the LAMB server.</p>
						<p class="mt-2"><strong>Note:</strong> Replace the API key with your actual LAMB API key.</p>
					</div>
				</div>
			</div>
		{/if}
	</div>

	{/if}
</div>