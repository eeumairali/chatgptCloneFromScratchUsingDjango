from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings


from .mongo import new_chat, list_chats, get_chat, push_message


import ollama
OLLAMA_MODEL = "deepseek-r1:1.5b"

# Maintain conversation history per chat in memory (for demonstration; for production, persist in DB)
chat_histories = {}

def _render(request, cid):
    chats = list_chats(request.user.id)
    # Rename _id to id for template compatibility
    for c in chats:
        if "_id" in c:
            c["id"] = c.pop("_id")
    doc = get_chat(request.user.id, cid)
    messages = doc["messages"] if doc else []
    return render(request, "chats/index.html", {
        "cid": cid, "chats": chats, "messages": messages
    })

@login_required
def new_chat_view(request):
    cid = new_chat(request.user.id, "New chat")
    return redirect("chat_open", cid=cid)

@login_required
def open_chat_view(request, cid):
    return _render(request, cid)

@login_required
def chat_home(request):
    # GET: open last or create
    if request.method == "GET":
        recent = list_chats(request.user.id, 1)
        cid = recent[0]["_id"] if recent else new_chat(request.user.id)
        return redirect("chat_open", cid=cid)

    # POST: send -> save user -> call Ollama -> save assistant
    cid = request.POST.get("cid") or new_chat(request.user.id)
    user_text = (request.POST.get("message") or "").strip()
    if not user_text:
        return redirect("chat_open", cid=cid)

    # 1) push user message
    push_message(request.user.id, cid, user=request.user.username, message=user_text)

    # 2) build model messages from stored history
    doc = get_chat(request.user.id, cid) or {"messages": []}
    hist = [{"role": ("assistant" if m["user"] == "assistant" else "user"),
             "content": m["message"]} for m in doc["messages"]]
    messages = [{"role": "system", "content": "You are a helpful assistant."}] + hist

    # Maintain conversation history per chat in memory (for demo; for prod, persist in DB)
    if cid not in chat_histories:
        chat_histories[cid] = messages.copy()
    else:
        chat_histories[cid] = messages.copy()

    # 3) call Ollama Python package
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=chat_histories[cid]
        )
        reply = response['message']['content']
        # Add assistant reply to conversation history
        chat_histories[cid].append({
            'role': 'assistant',
            'content': reply
        })
    except Exception as e:
        reply = f"(Ollama error: {e})"

    # 4) push assistant reply
    push_message(request.user.id, cid, user="assistant", message=reply)
    return redirect("chat_open", cid=cid)



