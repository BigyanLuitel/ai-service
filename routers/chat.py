from fastapi import APIRouter, HTTPException
import json

from schemas import ChatRequest, ChatResponse
from agent import get_agent_for_user

router = APIRouter(prefix="/chat", tags=["chat"])
@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest):
    agent = get_agent_for_user(payload.user_id)
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    result = None
    last_error = None
    for attempt in range(3):
        try:
            result = agent.invoke({"messages": messages})
            break
        except Exception as e:
            last_error = e

    if result is None:
        raise HTTPException(status_code=502, detail=f"Agent error after 3 attempts: {str(last_error)}")

    final_message = result["messages"][-1]
    reply_text = final_message.content

    payment_qr = None
    payment_url = None
    for m in result["messages"]:
        if hasattr(m, "name") and m.name == "confirm_order":
            try:
                tool_data = json.loads(m.content)
                if tool_data.get("success"):
                    payment_qr = tool_data.get("payment_qr_base64")
                    payment_url = tool_data.get("payment_url")
            except (json.JSONDecodeError, AttributeError):
                pass

    return ChatResponse(reply=reply_text, payment_qr_base64=payment_qr, payment_url=payment_url)