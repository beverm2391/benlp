from benlp import llms

# Load model
chat = llms.ChatAsync()

prompts = [
    "What is the meaning of life?",
    "What is the best life advice you can give?",
    "What is the best way to live?",
]

responses = []

# Generate responses
chat(prompts, responses)

print(responses)