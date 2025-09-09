import json
import os
import logging
import time
import asyncio
import subprocess
from typing import Dict, Any, AsyncGenerator, List

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_available_llms() -> List[str]:
    """
    Return list of available LLMs from llm CLI
    """
    if os.getenv("LLM_ENABLED", "false").lower() != "true":
        logger.info("LLM_ENABLED is false, skipping model list fetch")
        return []
    
    try:
        # Run 'llm models' to get available models
        result = subprocess.run(['llm', 'models'], capture_output=True, text=True)
        if result.returncode == 0:
            # Parse output and extract model names
            models = [
                line.strip() 
                for line in result.stdout.split('\n') 
                if line.strip() and not line.startswith('#')
            ]
            return models
        else:
            logger.error(f"Failed to get models from llm CLI: {result.stderr}")
            return [os.getenv("LLM_DEFAULT_MODEL", "gpt-3.5-turbo")]
    except Exception as e:
        logger.error(f"Error fetching llm models: {str(e)}")
        return [os.getenv("LLM_DEFAULT_MODEL", "gpt-3.5-turbo")]

def format_messages_for_llm(messages: list, is_o_model: bool = False) -> tuple[str, str]:
    """
    Convert OpenAI message format to llm CLI format
    Returns (system_prompt, user_message)
    """
    system_prompt = None
    context = None
    last_user_msg = None
    
    # Get the last user message and any system prompt
    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        elif msg["role"] == "user":
            last_user_msg = msg["content"]
            if "context" in msg:
                context = msg["context"]
    
    # Format user message with context if present
    user_message = last_user_msg if last_user_msg else ""
    if context:
        user_message = f"{user_message}\n\nThis is the context:\n{json.dumps(context)}"
    
    # For o-models, prepend system prompt to user message and clear system_prompt
    if is_o_model and system_prompt:
        user_message = f"{system_prompt}\n{user_message}"
        system_prompt = None  # Clear system prompt for o-models
    # For non-o-models, escape quotes in system prompt
    elif system_prompt:
        system_prompt = system_prompt.replace('"', '\\"')
    
    # Escape quotes in the final message
    user_message = user_message.replace('"', '\\"')
    
    return system_prompt, user_message

def clean_model_name(model: str) -> str:
    """Clean up model name to be compatible with llm CLI"""
    # Strip any provider prefix (e.g., 'openai:', 'ollama:')
    if "/" in model:
        model = model.split("/")[-1]
    if ":" in model:
        model = model.split(":")[-1]
    
    # Clean up any whitespace
    model = model.strip()
    
    # Map common model names
    model_map = {
        "gpt-4o-mini": "o1-mini",
        "o1-mini": "o1-mini",
    }
    
    model = model_map.get(model, model)
    logger.debug(f"Cleaned model name: '{model}'")  # Added quotes to see whitespace
    return model

def llm_connect(messages: list, stream: bool = False, body: Dict[str, Any] = None, llm: str = None):
    """
    LLM CLI connector that returns OpenAI-compatible responses
    """
    raw_model = llm or os.getenv("LLM_DEFAULT_MODEL", "o1-mini")
    model = clean_model_name(raw_model)
    is_o_model = model.startswith('o')
    
    logger.debug(f"Using model: {model} (raw: {raw_model}, is_o_model: {is_o_model})")
    
    # Prepare the llm CLI command
    cmd = ["llm"]
    
    # Add model specification
    cmd.extend(["-m", model])
    
    # Get system prompt and user message
    system_prompt, user_message = format_messages_for_llm(messages, is_o_model)
    
    # Add system prompt ONLY if not an o-model
    if not is_o_model and system_prompt:
        cmd.extend(["-s", f'"{system_prompt}"'])
    
    # Add no-stream flag for non-streaming requests
    if not stream:
        cmd.append("--no-stream")
    
    # Append the user message as the final argument, properly quoted
    cmd.append(f'"{user_message}"')
    
    # Log the complete command for debugging
    logger.info("=" * 40)
    logger.info("LLM Command:")
    logger.info(f"Command: {' '.join(cmd)}")
    logger.info("=" * 40)
    
    try:
        if stream:
            async def generate_stream():
                # Send initial "thinking" message
                thinking_chunk = {
                    "id": f"llm-{int(time.time())}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": "Thinking... "},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(thinking_chunk)}\n\n"

                # Run llm CLI command
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    logger.error(f"Error from llm CLI: {stderr}")
                    content = f"[LLM Error] Failed to get response from model {model}: {stderr}"
                else:
                    content = stdout.strip()

                # Stream the response word by word
                words = content.split()
                for word in words:
                    chunk = {
                        "id": f"llm-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": word + " "},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.05)

                # Send final chunk
                final_chunk = {
                    "id": f"llm-{int(time.time())}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"

            return generate_stream()
        else:
            # For non-streaming, run llm CLI command directly
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                logger.error(f"Error from llm CLI: {process.stderr}")
                content = f"[LLM Error] Failed to get response from model {model}: {process.stderr}"
            else:
                content = process.stdout.strip()

            # Create OpenAI-compatible response
            return {
                "id": f"llm-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": -1,
                    "completion_tokens": -1,
                    "total_tokens": -1
                }
            }

    except Exception as e:
        logger.error(f"Unexpected error in LLM connector: {str(e)}")
        raise 