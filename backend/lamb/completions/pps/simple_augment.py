from typing import Dict, Any, List, Optional
from lamb.lamb_classes import Assistant
import json
from utils.timelog import Timelog
def prompt_processor(
    request: Dict[str, Any],
    assistant: Optional[Assistant] = None,
    rag_context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    Simple augment prompt processor that:
    1. Uses system prompt from assistant if available
    2. Replaces last message with prompt template, substituting:
       - {user_input} with the original message
       - {context} with RAG context if available
    """
    messages = request.get('messages', [])
    if not messages:
        return messages

    # Get the last user message
    last_message = messages[-1]['content']

    # Create new messages list
    processed_messages = []

    if assistant:
        # Add system message from assistant if available
        if assistant.system_prompt:
            processed_messages.append({
                "role": "system",
                "content": assistant.system_prompt
            })
        
        # Add previous messages except the last one
        processed_messages.extend(messages[:-1])
        
        # Process the last message using the prompt template
        if assistant.prompt_template:
            # Replace placeholders in template
            Timelog(f"User message: {last_message}",2)
            prompt = assistant.prompt_template.replace("{user_input}", "\n\n" + last_message + "\n\n")
            
            # Add RAG context if available
            if rag_context:
                context = json.dumps(rag_context)
                prompt = prompt.replace("{context}", "\n\n" + context + "\n\n")
            else:
                prompt = prompt.replace("{context}", "")
                
            # Add processed message
            processed_messages.append({
                "role": messages[-1]['role'],
                "content": prompt
            })
        else:
            # If no template, use original message
            processed_messages.append(messages[-1])
            
        return processed_messages
    
    # If no assistant provided, return original messages
    return messages 