from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from pydantic import BaseModel

from benlp.document import JupyterSimple
from benlp.llms import Chat


router = APIRouter()

# routes -------------------------------------


@router.get("/")
async def endpoint_get_chain():
    message = """
    This is the chain endpoint. It allows you to run prebuilt chains of functions.
    """
    return {"message": "Hello World!"}

@router.post("/jupyterdocs")
async def endpoint_post_jupyterdocs(request):
    fpath = "/Users/beneverman/Documents/Coding/benlp_v1/data/test/lp_solver.ipynb"
    doc = JupyterSimple(fpath)
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