from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from models import ChatRequest

from benlp.llms import ChatServer

router = APIRouter()

# routes -------------------------------------
@router.get("/stream")
async def endpoint_get_chat():
    # return a message that shows the approrpiate params
    message = """
    PARAMS:
    messages: 
    max_tokens: int (optional), defaults to 2048
    temperature: float (optional), defaults to 0
    model: str (optional), defaults to "gpt-3.5-turbo-16k"
    """
    return {"message": message}

@router.post("/stream")
def endpoint_post_chat(req : ChatRequest):
    # parse the request
    messages = [message.dict(exclude_none=True) for message in req.messages] # convert to dict instead of pydantic model, and remove None values
    print(messages)
    max_tokens = req.max_tokens
    temperature = req.temperature
    model = req.model

    # run the chat
    chat = ChatServer()
    response = chat(messages, max_tokens=max_tokens, temperature=temperature, model=model, stream=True)

    # return the response
    async def event_stream():
        full_message = ""
        for item in response:
            yield str(item)

            content = item['choices'][0]['delta'].get('content') # use get method to avoid key error on empty delts
            # use this to avoid adding None to the string (which would cause an error)
            if content:
                full_message += content
    
    return EventSourceResponse(event_stream(), media_type="text/event-stream")