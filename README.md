## benlp (Ben's Natural Language Processing Library)

This repo includes a library of reusable abstractions for building application layers on top of LLM APIs. There are some other great solutions, like [langchain](https://www.langchain.com/) but I wanted more flexibility and control over the abstractions.

### Notable Things I've Built With This Library
1. Complex Summarization with AI: [post](https:www.beneverman/com/blog/llm-timeline)/[repo](https://github.com/beverm2391/ai-summarizer)
2. A proof-of-concept Clinical Decision Support Tool (CDST) for adolescent depression screening: [post]()/[repo](https://github.com/beverm2391/NLP-CDST)
3. A linear optimization word problem solver to do my econ homework: [post]()/[repo]()
4. A chatGPT-like clone, extended with embedded search: (the server is here in this repo): [frontend repo]()

### Server

The server is a simple FastAPI server that exposes the library's functionality as a REST API. I use this server to run my custom chat-like UI for GPT-4.