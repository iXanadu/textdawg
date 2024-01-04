from django.db import models
from models import FubMessageHistory  # Replace 'your_app' with your actual app name

def create_complete_io_records():
    # Retrieve all messages ordered by timestamp
    messages = FubMessageHistory.objects.all().order_by('timestamp')

    records = []
    pending_human_input = None
    pending_ai_output = None

    for message in messages:
        if message.role == "Human":
            if pending_ai_output is not None:
                records.append((None, pending_ai_output.message))
                pending_ai_output = None

            if pending_human_input is not None:
                records.append((pending_human_input.message, None))

            pending_human_input = message

        elif message.role == "AI":
            if pending_human_input is not None:
                records.append((pending_human_input.message, message.message))
                pending_human_input = None
            else:
                pending_ai_output = message

    # Handling any remaining messages without responses
    if pending_human_input is not None:
        records.append((pending_human_input.message, None))
    if pending_ai_output is not None:
        records.append((None, pending_ai_output.message))

    return records

# Call the function to create records
io_records = create_complete_io_records()

# Outputting the first few records for demonstration (you can handle this as needed)
for record in io_records[:5]:  # Adjust the range as necessary
    print(record)
