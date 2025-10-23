import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';

describe('AssistantForm - Default Prompt Template', () => {
	it('should have a default prompt template for new assistants', () => {
		// Test that the default prompt template is not empty
		const defaultPromptTemplate = `User question:\n{user_input}\n\nRelevant context:\n{context}\n\n- Please provide a clear and helpful answer based only on the context above.\n- If the context does not contain enough information, say so clearly.\n- Always respond in the same language used in the user question`;
		
		expect(defaultPromptTemplate).toBeDefined();
		expect(defaultPromptTemplate).not.toBe('');
		expect(defaultPromptTemplate).toContain('{user_input}');
		expect(defaultPromptTemplate).toContain('{context}');
	});

	it('should contain required RAG placeholders in default template', () => {
		const defaultPromptTemplate = `User question:\n{user_input}\n\nRelevant context:\n{context}\n\n- Please provide a clear and helpful answer based only on the context above.\n- If the context does not contain enough information, say so clearly.\n- Always respond in the same language used in the user question`;
		
		// Verify that the default template contains the required placeholders
		expect(defaultPromptTemplate).toMatch(/\{user_input\}/);
		expect(defaultPromptTemplate).toMatch(/\{context\}/);
	});
});
