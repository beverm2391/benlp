from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fastapi import File, UploadFile
from sse_starlette.sse import EventSourceResponse

from pydantic import BaseModel

from benlp.document import JupyterSimpleServer
from benlp.llms import Chat


router = APIRouter()

# routes -------------------------------------

@router.post("/jupyter")
async def endpoint_post_jupyterdocs(file : UploadFile = File(...)):
    doc = JupyterSimpleServer(file.file.read())
    prompt = doc.create_prompt()
    chat = Chat(model="gpt-3.5-turbo-16k", stream=True)
    response = chat(prompt)

    async def event_stream():
        full_message = ""
        for item in response:
            yield str(item)

            content = item['choices'][0]['delta'].get('content') # use get method to avoid key error on empty delts
            # use this to avoid adding None to the string (which would cause an error)
            if content:
                full_message += content
    
    return EventSourceResponse(event_stream(), media_type="text/event-stream")