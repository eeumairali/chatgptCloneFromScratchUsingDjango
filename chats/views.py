from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from openai import OpenAI

from .mongo import new_chat, list_chats, get_chat, push_message

client = OpenAI(api_key=settings.OPEN_API_KEY)

def _render(request, cid):
    chats = list_chats(request.user.id)
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

    # POST: send -> save user -> call OpenAI -> save assistant
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

    # 3) call OpenAI
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = resp.choices[0].message.content
    except Exception as e:
        reply = f"(Error: {e})"

    # 4) push assistant reply
    push_message(request.user.id, cid, user="assistant", message=reply)
    return redirect("chat_open", cid=cid)

