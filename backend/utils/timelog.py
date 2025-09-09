# time_logger.py
import os
import datetime
import inspect
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()

# Get log level from environment variable, default to 1 if not set or invalid
try:
    # Attempt to get and convert the log level
    CONFIG_TIMELOG_LEVEL = int(os.getenv('TIMELOG_LEVEL', '1'))
except ValueError:
    # Handle cases where TIMELOG_LEVEL is not a valid integer
    print("Warning: Invalid TIMELOG_LEVEL in .env file. Using default level 1.")
    CONFIG_TIMELOG_LEVEL = 1

# Get log file path from environment variable, default to 'timelog.log'
CONFIG_TIMELOG_FILE = os.getenv('TIMELOG_FILE', 'timelog.log')
VERBOSE_TIMELOG = os.getenv('VERBOSE_TIMELOG', 'false')
# Ensure the directory for the log file exists (optional, but good practice)
log_dir = os.path.dirname(CONFIG_TIMELOG_FILE)
if log_dir and not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)
        print(f"Created log directory: {log_dir}")
    except OSError as e:
        print(f"Error creating log directory {log_dir}: {e}")
        # Fallback to current directory if dir creation fails
        CONFIG_TIMELOG_FILE = os.path.basename(CONFIG_TIMELOG_FILE)


# --- Logging Function ---
def Timelog(message: str, level: int = 1):
    """
    Logs a message to the configured file if the provided level is less
    than or equal to the configured TIMELOG_LEVEL.

    Includes timestamp, calling function name, level, and message.
    Creates the log file if it doesn't exist.

    Args:
        message (str): The message string to log.
        level (int): The logging level for this message. Defaults to 1.
                     Only messages with level <= CONFIG_TIMELOG_LEVEL are logged.
    """
    if level <= CONFIG_TIMELOG_LEVEL:
        try:
            # --- Get caller information ---
            caller_frame = inspect.stack()[1]  # Get the frame of the caller
            caller_function_name = caller_frame.function # Get the function name

            # --- Get current timestamp ---
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # --- Format the log entry based on VERBOSE_TIMELOG setting ---
            if VERBOSE_TIMELOG.lower() == 'true':
                log_entry = f"* **{timestamp}** - `Function: {caller_function_name}` - `LEVEL {level}` - {message}\n"
            else:
                # Concise format: timestamp - function - message (max 100 chars)
                base_entry = f"* {timestamp} - {caller_function_name}: "
                max_message_length = 100 - len(base_entry)
                truncated_message = message[:max_message_length] + "..." if len(message) > max_message_length else message
                log_entry = f"{base_entry}{truncated_message}\n"

            # --- Write to log file ---
            with open(CONFIG_TIMELOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_entry)

        except IndexError:
            print(f"Error: Could not determine caller function for message: {message}")
        except IOError as e:
            print(f"Error writing to log file {CONFIG_TIMELOG_FILE}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during logging: {e}")

# --- Example Usage (Optional - runs only if script is executed directly) ---
if __name__ == "__main__":
    print(f"Logger initialized.")
    print(f"Logging Level configured to: {CONFIG_TIMELOG_LEVEL}")
    print(f"Logging to file: {CONFIG_TIMELOG_FILE}")

    def example_function_one():
        Timelog("This is a standard message.", 1)
        Timelog("This is a more detailed message.", 2)

    def example_function_two():
        Timelog("This message has a higher level.", 3) # Won't log if level is 2
        Timelog("Another standard message from function two.", 1)

    print("\nRunning example functions...")
    example_function_one()
    example_function_two()
    Timelog("This message is logged from the main script block.", 1)

    print(f"\nCheck the '{CONFIG_TIMELOG_FILE}' file for log entries.")