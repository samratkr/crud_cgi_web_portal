import os
import cgi
import cgitb
import sys
import uuid
import urllib.parse
import http.cookies
import json
from auth import create_user, authenticate_user
from crud import get_items, add_item, delete_item, update_item
from db import get_db

cgitb.enable()

SESSION_DIR = "/tmp/cgi_sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

def load_session():
    cookie = http.cookies.SimpleCookie(os.environ.get("HTTP_COOKIE"))
    sid_cookie = cookie.get("sid")
    if sid_cookie:
        sid = sid_cookie.value
        session_file = os.path.join(SESSION_DIR, f"{sid}.json")
        if os.path.exists(session_file):
            with open(session_file) as f:
                return json.load(f)
    return {}

def save_session(session, sid=None):
    if not sid:
        sid = str(uuid.uuid4())
    with open(os.path.join(SESSION_DIR, f"{sid}.json"), "w") as f:
        json.dump(session, f)
    return sid

def render_template(template_name, context=None):
    context = context or {}
    template_path = os.path.join(os.path.dirname(__file__), "templates", template_name)
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    for key, value in context.items():
        html = html.replace(f"{{{{ {key} }}}}", str(value))
    print("Content-Type: text/html\n")
    print(html)

def render_json(data):
    print("Content-Type: application/json\n")
    print(json.dumps(data))

def redirect(url):
    print("Status: 303 See Other")
    print(f"Location: {url}\n")
    print(f"<html><body>Redirecting to <a href='{url}'>{url}</a></body></html>")

def handle_signup(form, session):
    username = form.getvalue("username")
    password = form.getvalue("password")

    if not username or not password:
        response = {"success": False, "message": "Username and password are required."}
        render_json(response)
        return

    if create_user(username, password):
        response = {"success": True, "message": "User created successfully."}
    else:
        response = {"success": False, "message": "User already exists."}

    render_json(response)

def handle_login(form, session):
    username = form.getvalue("username")
    password = form.getvalue("password")

    if username and password:
        user = authenticate_user(username, password)
        if user:
            session["user_id"] = user[0]
            sid = save_session(session)
            print(f"Set-Cookie: sid={sid}; Path=/; HttpOnly")
            print("Content-Type: application/json")
            print()
            print(json.dumps({"success": True, "message": "Login successful"}))
            return
        else:
            response = {"success": False, "message": "Invalid credentials"}
    else:
        response = {"success": False, "message": "Missing username or password"}

    print("Content-Type: application/json")
    print()
    print(json.dumps(response))

def handle_dashboard(session):
    if "user_id" not in session:
        render_template("login.html", {"message": "Please login first"})
        return
    render_template("dashboard.html")

def handle_list(session):
    session = load_session()
    if "user_id" not in session:
        render_json({"error": "Unauthorized"})
        return
    items = get_items(session["user_id"])
    items_list = [{"id": i[0], "name": i[1], "description": i[2], "price": float(i[3])} for i in items]
    render_json(items_list)

def handle_add(form, session):
    if "user_id" not in session:
        render_json({"error": "Unauthorized"})
        return
    name = form.getvalue("name")
    description = form.getvalue("description")
    price = form.getvalue("price")
    if name and price:
        add_item(session["user_id"], name, description, float(price))
        render_json({"success": True})
    else:
        render_json({"error": "Missing fields"})

def handle_edit(form, session, params=None):
    if "user_id" not in session:
        render_json({"error": "Unauthorized"})
        return

    item_id = form.getvalue("id") or (params.get("id", [None])[0] if params else None)
    if not item_id:
        render_json({"error": "Item ID missing"})
        return

    name = form.getvalue("name")
    description = form.getvalue("description")
    price = form.getvalue("price")

    if name and price:
        update_item(item_id, session["user_id"], name, description, float(price))
        render_json({"success": True})
    else:
        render_json({"error": "Missing fields"})


def handle_delete(session, params=None):
    if "user_id" not in session:
        render_json({"error": "Unauthorized"})
        return

    try:
        length = int(os.environ.get("CONTENT_LENGTH", 0))
        data = json.loads(sys.stdin.read(length)) if length > 0 else {}
    except Exception as e:
        render_json({"error": f"Invalid JSON: {str(e)}"})
        return

    item_id = data.get("id")
    if not item_id:
        render_json({"error": "Item ID missing"})
        return

    delete_item(item_id, session["user_id"])
    render_json({"success": True})


if __name__ == "__main__":
    form = cgi.FieldStorage()
    query = os.environ.get("QUERY_STRING", "")
    params = urllib.parse.parse_qs(query)
    action = params.get("action", [""])[0]

    session = load_session()

    if os.environ.get("REQUEST_METHOD") == "POST":
        if action == "signup":
            handle_signup(form, session)
        elif action == "login":
            handle_login(form, session)
        elif action == "add":
            handle_add(form, session)
        elif action == "edit":
            handle_edit(form, session)
        elif action == "delete":
            item_id = form.getvalue("id")
            if not item_id:
                render_json({"error": "Item ID missing"})
            else:
                delete_item(item_id, session.get("user_id"))
                render_json({"success": True})
        else:
            render_template("login.html", {"message": "Invalid action."})
    else:
        if action == "delete":
            handle_delete(session, params)
        elif action == "signup":
            handle_signup(form, session)
        elif action == "login":
            handle_login(form, session)
        elif action == "list":
            handle_list(session)
        elif action == "edit":
            handle_edit(form, session, params)
        elif action == "dashboard":
            handle_dashboard(session)
        else:
            render_template("login.html")