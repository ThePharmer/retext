#!/usr/bin/env python3
"""Flask web application for Retext SMS Search."""

import html
import logging
import os
import re
import signal
import sys
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.security import check_password_hash
from werkzeug.wrappers import Response

import db

# T049a: Configure authentication logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('retext')

# T022: Flask application with config loading
app = Flask(__name__)

# T022a: APPLICATION_ROOT for URL prefix support (e.g., /absproxy/8888 for code-server)
# Uses Werkzeug's DispatcherMiddleware - the official approach for mounting Flask at a subpath
# See: https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/
APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '')
if APPLICATION_ROOT:
    def not_found_app(environ, start_response):
        """Simple 404 handler for requests outside the prefix."""
        response = Response('Not Found', status=404)
        return response(environ, start_response)

    # Mount the Flask app at the specified prefix
    # DispatcherMiddleware properly handles PATH_INFO stripping and SCRIPT_NAME setting
    app.wsgi_app = DispatcherMiddleware(not_found_app, {APPLICATION_ROOT: app.wsgi_app})

# T023: Session configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-me')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

# Password hash from environment
PASSWORD_HASH = os.environ.get('PASSWORD_HASH', '')


# T046: Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'"
    return response


# T024: login_required decorator
def login_required(f):
    """Decorator to protect routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# T025: GET /login route
@app.route('/login', methods=['GET'])
def login():
    """Serve login form."""
    error = request.args.get('error')
    return render_template('login.html', error=error)


# T026: POST /login route with password verification
@app.route('/login', methods=['POST'])
def login_post():
    """Handle login form submission."""
    password = request.form.get('password', '')
    client_ip = request.remote_addr

    if PASSWORD_HASH and check_password_hash(PASSWORD_HASH, password):
        session['authenticated'] = True
        # T049a: Log successful authentication
        logger.info(f'AUTH_SUCCESS ip={client_ip}')
        return redirect(url_for('index'))

    # T049a: Log failed authentication
    logger.warning(f'AUTH_FAILURE ip={client_ip}')
    return redirect(url_for('login', error='1'))


# T027: POST /logout route
@app.route('/logout', methods=['POST'])
def logout():
    """Clear session and log out."""
    session.clear()
    return redirect(url_for('login'))


# T032: GET / route serving index.html
@app.route('/')
@login_required
def index():
    """Serve main search interface."""
    return render_template('index.html')


# T041: GET /api/stats route
@app.route('/api/stats')
@login_required
def api_stats():
    """Return database statistics."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as count FROM messages')
    count = cursor.fetchone()['count']
    conn.close()

    return jsonify({
        'message_count': count,
        'has_messages': count > 0
    })


# T028, T029, T030, T031: GET /api/search route
@app.route('/api/search')
@login_required
def api_search():
    """Search messages with FTS5 MATCH query."""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', '1')

    # Validate query
    if not query:
        return jsonify({'error': 'Missing search query'}), 400

    # Validate page number
    try:
        page = max(1, int(page))
    except ValueError:
        page = 1

    # T029: Pagination (50 per page)
    per_page = 50
    offset = (page - 1) * per_page

    conn = db.get_connection()
    cursor = conn.cursor()

    # Sanitize query for FTS5 (escape special characters)
    safe_query = sanitize_fts_query(query)

    try:
        # Get total count
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM messages m
            JOIN messages_fts fts ON m.id = fts.rowid
            WHERE messages_fts MATCH ?
        ''', (safe_query,))
        total = cursor.fetchone()['count']

        # Get paginated results
        cursor.execute('''
            SELECT m.id, m.phone_number, m.contact_name, m.body,
                   m.timestamp, m.message_type
            FROM messages m
            JOIN messages_fts fts ON m.id = fts.rowid
            WHERE messages_fts MATCH ?
            ORDER BY m.timestamp DESC
            LIMIT ? OFFSET ?
        ''', (safe_query, per_page, offset))

        rows = cursor.fetchall()
        conn.close()

        # Build results with highlighting and formatting
        results = []
        for row in rows:
            # T30: Highlight search terms
            highlighted_body = highlight_terms(row['body'], query)

            # T31: Format timestamp
            formatted_date = format_timestamp(row['timestamp'])

            results.append({
                'id': row['id'],
                'phone_number': row['phone_number'],
                'contact_name': row['contact_name'],
                'body': highlighted_body,
                'timestamp': row['timestamp'],
                'message_type': row['message_type'],
                'formatted_date': formatted_date
            })

        has_more = (page * per_page) < total

        return jsonify({
            'results': results,
            'total': total,
            'page': page,
            'per_page': per_page,
            'has_more': has_more
        })

    except Exception:
        conn.close()
        return jsonify({'error': 'Search failed'}), 500


def sanitize_fts_query(query):
    """Sanitize search query for FTS5."""
    # Escape FTS5 special characters
    # Quote the entire query for phrase search
    escaped = query.replace('"', '""')
    return f'"{escaped}"'


def highlight_terms(body, query):
    """T030: Highlight search terms with <mark> tags."""
    # HTML escape the body first
    safe_body = html.escape(body)

    # Split query into words and highlight each
    words = query.split()
    for word in words:
        # Case-insensitive highlight
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        safe_body = pattern.sub(
            lambda m: f'<mark>{html.escape(m.group())}</mark>',
            safe_body
        )

    return safe_body


def format_timestamp(timestamp_ms):
    """T031: Convert millisecond timestamp to human-readable date."""
    try:
        # SMS Backup uses milliseconds
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime('%Y-%m-%d %I:%M %p')
    except (ValueError, OSError):
        return 'Unknown date'


# T045: Health endpoint (public, no auth required)
@app.route('/health')
def health():
    """Health check endpoint for reverse proxy."""
    return jsonify({'status': 'ok'})


# T049: Error handlers returning JSON (no message content)
@app.errorhandler(400)
def bad_request(e):
    """Handle 400 Bad Request errors."""
    return jsonify({'error': 'Bad request'}), 400


@app.errorhandler(401)
def unauthorized(e):
    """Handle 401 Unauthorized errors."""
    return jsonify({'error': 'Unauthorized'}), 401


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 Internal Server errors (T049b: no message content)."""
    logger.error('Internal server error occurred')
    return jsonify({'error': 'Internal server error'}), 500


# T048a: SIGTERM handler for graceful shutdown
def handle_sigterm(signum, frame):
    """Handle SIGTERM for graceful container shutdown."""
    logger.info('Received SIGTERM, shutting down gracefully')
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_sigterm)


if __name__ == '__main__':
    # Initialize database
    db.init_db()

    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))

    app.run(host=host, port=port, debug=False)
