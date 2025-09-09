from schemas import OpenAIChatCompletionForm
from fastapi import Request


def print_api_key(request: Request):
    print("API Key:", request.headers.get("Authorization"))

def print_request(request: Request):
    print("Request:")
    print(f"  Method: {request.method}")
    print(f"  URL: {request.url}")
    print(f"  Headers: {request.headers}")
    print(f"  Body: {request.body}")

def print_form_data(form_data: OpenAIChatCompletionForm):
    print("Form Data:")
    for field, value in form_data.model_dump().items():
        if value is not None:
            if field == "messages":
                print("  Messages:")
                for idx, message in enumerate(value):
                    print(f"    Message {idx + 1}:")
                    for msg_field, msg_value in message.items():
                        print(f"      {msg_field}: {msg_value}")
            elif field == "functions":
                print("  Functions:")
                for idx, function in enumerate(value):
                    print(f"    Function {idx + 1}:")
                    for func_field, func_value in function.items():
                        print(f"      {func_field}: {func_value}")
            else:
                print(f"  {field}: {value}")