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
        # For URL-encoded POST (from your AJAX)
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



#!/usr/bin/env python
# import os
# import cgi
# import cgitb
# import http.cookies as Cookie
# import uuid
# import urllib.parse
# from auth import create_user, authenticate_user
# from crud import get_items, add_item, delete_item, update_item
# import json
# from db import get_db

# cgitb.enable()

# SESSION_DIR = os.path.join(os.path.dirname(__file__), "sessions")
# os.makedirs(SESSION_DIR, exist_ok=True)

# # --- SESSION FUNCTIONS ---
# def load_session():
#     cookie = Cookie.SimpleCookie(os.environ.get("HTTP_COOKIE"))
#     sid_cookie = cookie.get("sid")
#     if sid_cookie:
#         sid = sid_cookie.value
#         try:
#             with open(os.path.join(SESSION_DIR, sid + ".json")) as f:
#                 session = json.load(f)
#                 session["sid"] = sid
#                 return session
#         except FileNotFoundError:
#             pass
#     # Create new session
#     session = {"sid": str(uuid.uuid4())}
#     save_session(session)
#     return session

# def save_session(session):
#     sid = session.get("sid") or str(uuid.uuid4())
#     session["sid"] = sid
#     with open(os.path.join(SESSION_DIR, sid + ".json"), "w") as f:
#         json.dump(session, f)
#     print(f"Set-Cookie: sid={sid}; Path=/; HttpOnly")

# # --- TEMPLATE ---
# def render_template(template_name, context=None):
#     """Render an HTML template from templates/ folder."""
#     context = context or {}
#     template_path = os.path.join(os.path.dirname(__file__), "..", "templates", template_name)
    
#     with open(template_path, "r", encoding="utf-8") as f:
#         html = f.read()

#     # Replace {{ key }} in template with context values
#     for key, value in context.items():
#         html = html.replace(f"{{{{ {key} }}}}", str(value))

#     print("Content-Type: text/html\n")
#     print(html)

# # --- HANDLERS ---
# def handle_signup(form):
#     username = form.getvalue("username")
#     password = form.getvalue("password")
#     if username and password:
#         if create_user(username, password):
#             render_template("Signup", "User created! <a href='?action=login'>Login</a>")
#         else:
#             render_template("Signup", "User already exists.")
#     else:
#         render_template("Signup", """<form method="POST" action="?action=signup">
#         Username: <input name="username"><br>
#         Password: <input type="password" name="password"><br>
#         <input type="submit" value="Sign Up">
#         </form>""")

# def handle_login(form, session):
#     username = form.getvalue("username")
#     password = form.getvalue("password")
#     if username and password:
#         user = authenticate_user(username, password)
#         if user:
#             session["user_id"] = user[0]
#             save_session(session)
#             render_template("login.html", {"message": "Login successful! <a href='?action=list'>Go to items</a>"})
#             # render_template("Login", "Login successful! <a href='?action=list'>Go to items</a>")
#         else:
#             render_template("login.html", "Invalid credentials.")
#     else:
#         render_template("login.html", """<form method="POST" action="?action=login">
#         Username: <input name="username"><br>
#         Password: <input type="password" name="password"><br>
#         <input type="submit" value="Login">
#         </form>""")

# def handle_list(session):
#     if "user_id" not in session:
#         render_template("Unauthorized", "Please <a href='?action=login'>login</a>.")
#         return
#     items = get_items(session["user_id"])
#     rows = "".join(
#         f"<li>{item['name']} - {item['description']} - ${item['price']} "
#         f"<a href='?action=edit&id={item['id']}'>Edit</a> "
#         f"<a href='?action=delete&id={item['id']}'>Delete</a></li>"
#         for item in items
#     )
#     form_html = """<form method="POST" action="?action=add">
#         Name: <input name="name"><br>
#         Description: <input name="description"><br>
#         Price: <input name="price"><br>
#         <input type="submit" value="Add Item">
#         </form>"""
#     render_template("Items", f"<ul>{rows}</ul>{form_html}")

# def handle_add(form, session):
#     if "user_id" not in session:
#         render_template("Unauthorized", "Please <a href='?action=login'>login</a>.")
#         return
#     name = form.getvalue("name")
#     description = form.getvalue("description")
#     price = form.getvalue("price")
#     if name and price:
#         add_item(session["user_id"], name, description, float(price))
#     handle_list(session)

# def handle_edit(form, session, params=None):
#     if "user_id" not in session:
#         render_template("Unauthorized", "Please <a href='?action=login'>login</a>.")
#         return

#     item_id = form.getvalue("id") or (params.get("id", [None])[0] if params else None)
#     if not item_id:
#         render_template("Error", "Item ID missing.")
#         return

#     # Show current item
#     conn = get_db()
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM items WHERE id=? AND user_id=?", (item_id, session["user_id"]))
#     item = cursor.fetchone()
#     conn.close()
#     if not item:
#         render_template("Error", "Item not found.")
#         return

#     if os.environ.get("REQUEST_METHOD") == "POST":
#         name = form.getvalue("name", "").strip()
#         description = form.getvalue("description", "").strip()
#         price = form.getvalue("price", "").strip()

#         if not name or not price:
#             render_template("Edit Item", "Name and Price are required.")
#             return

#         try:
#             price = float(price)
#         except ValueError:
#             render_template("Edit Item", "Invalid price. Please enter a valid number.")
#             return

#         update_item(item_id, session["user_id"], name, description, price)
#         handle_list(session)
#         return

#     render_template("Edit Item", f"""
#         <form method="POST" action="?action=edit&id={item_id}">
#             Name: <input name="name" value="{item['name']}"><br>
#             Description: <input name="description" value="{item['description']}"><br>
#             Price: <input name="price" value="{item['price']}"><br>
#             <input type="submit" value="Update">
#         </form>
#     """)

# def handle_delete(session, params):
#     if "user_id" not in session:
#         render_template("Unauthorized", "Please <a href='?action=login'>login</a>.")
#         return
#     item_id = params.get("id", [None])[0]
#     if item_id:
#         delete_item(session["user_id"], item_id)
#     handle_list(session)

# # --- MAIN CGI ---
# if __name__ == "__main__":
#     form = cgi.FieldStorage()
#     query = os.environ.get("QUERY_STRING", "")
#     params = urllib.parse.parse_qs(query)
#     action = params.get("action", [""])[0]

#     session = load_session()

#     if os.environ.get("REQUEST_METHOD") == "POST":
#         if action == "signup":
#             handle_signup(form)
#         elif action == "login":
#             handle_login(form, session)
#         elif action == "add":
#             handle_add(form, session)
#         elif action == "edit":
#             handle_edit(form, session)
#         else:
#             render_template("Error", "Invalid action.")
#     else:  # GET requests
#         if action == "delete":
#             handle_delete(session, params)
#         elif action == "signup":
#             handle_signup(form)
#         elif action == "login":
#             handle_login(form, session)
#         elif action == "list":
#             handle_list(session)
#         elif action == "edit":
#             handle_edit(form, session, params)
#         else:
#             render_template("Home", "<a href='?action=signup'>Sign Up</a> | <a href='?action=login'>Login</a>")

