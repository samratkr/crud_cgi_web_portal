# CRUD CGI Web Portal

A simple Python CGI-based web application with user authentication, product management (CRUD), and SQLite database. Includes login/signup, session handling, and AJAX support using jQuery.

## Features

- User signup and login
- Dashboard with item listing
- Add, edit, delete items
- AJAX support for CRUD operations
- Session handling using JSON files
- SQLite database

## Prerequisites

- Python 3.x
- SQLite
- A web server that supports CGI (e.g., Apache, Nginx with CGI)
- `pip` for Python dependencies

## Setup and Run Locally

1. Clone the repository:

   ```bash
   git clone https://github.com/samratkr/crud_cgi_web_portal.git
   cd crud_cgi_web_portal

   ```

2. Create a virtual environment (optional but recommended):
   python -m venv venv
   source venv/bin/activate # Linux / macOS
   venv\Scripts\activate # Windows

3. Initialize the database:
   cd cgi-bin
   python db.py

4. Set up a CGI-compatible server and ensure cgi-bin/app.py is executable:
   chmod +x cgi-bin/app.py

5. Run locally (using Python’s built-in server for testing CGI):
   python -m http.server 8000 --cgi

   Then visit: http://localhost:8000/cgi-bin/app.py

# if writable problem persist use

chmod 775 /var/www/crud_cgi_web_portal/cgi-bin
chmod 664 /var/www/crud_cgi_web_portal/cgi-bin/app.db
