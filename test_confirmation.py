from agent import get_agent_for_user

agent = get_agent_for_user(user_id=1)
messages = []

def send(user_message):
    messages.append({"role": "user", "content": user_message})
    result = agent.invoke({"messages": messages})
    reply = result["messages"][-1].content
    messages.append({"role": "assistant", "content": reply})
    print(f"USER: {user_message}")
    print(f"AGENT: {reply}\n")
    return reply

# Turn 1: find a product
send("do you have the Sony WH-1000XM5?")

# Turn 2: add to cart (no user_id needed anymore — it's baked in)
send("add it to my cart")

# Turn 3: ask to order — should trigger preview_order, NOT confirm_order
send("okay place the order, ship to Kathmandu, pay with esewa")

# Turn 4: explicit confirmation — should NOW trigger confirm_order
send("yes, confirm it")

# add this temporarily to the end of test_confirmation.py
import json
print("\n--- Raw last tool result check ---")
for m in messages:
    pass  # messages only has text; let's inspect the full result object instead