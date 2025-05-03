from .app import lambda_handler
import json
import os
event_file = os.path.join(os.path.dirname(__file__), "test_event.json")

if __name__ == "__main__":
    with open(event_file) as f:
        event = json.load(f)

    response = lambda_handler(event, context={})
    print(json.dumps(response, indent=2))
