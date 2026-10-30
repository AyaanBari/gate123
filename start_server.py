import http.server
import socketserver
import webbrowser
import os
import sys
import json
import urllib.parse
import ipaddress
import base64
import hashlib
import hmac
import secrets
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts import db_manager

db_manager.init_db()

# Admin tokens are issued after a successful login. Set this environment variable
# to a stable random secret when running more than one server worker.
ADMIN_TOKEN_SECRET = os.environ.get('ADMIN_API_TOKEN_SECRET') or secrets.token_bytes(32)


def _trusted_proxy_networks():
    values = os.environ.get('TRUSTED_PROXY_CIDRS', '127.0.0.1/32,::1/128')
    networks = []
    for value in values.split(','):
        value = value.strip()
        if not value:
            continue
        try:
            networks.append(ipaddress.ip_network(value, strict=False))
        except ValueError:
            print(f'Ignoring invalid TRUSTED_PROXY_CIDRS entry: {value}')
    return networks


TRUSTED_PROXY_NETWORKS = _trusted_proxy_networks()


def _normalize_ip(value):
    try:
        address = ipaddress.ip_address(value.strip())
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        return address
    except (ValueError, AttributeError):
        return None


def _is_trusted_proxy(address):
    return any(address.version == network.version and address in network for network in TRUSTED_PROXY_NETWORKS)


def create_admin_token(email):
    payload = json.dumps({'sub': email.lower().strip(), 'exp': int(time.time()) + 12 * 60 * 60}, separators=(',', ':')).encode('utf-8')
    encoded = base64.urlsafe_b64encode(payload).rstrip(b'=').decode('ascii')
    signature = hmac.new(ADMIN_TOKEN_SECRET if isinstance(ADMIN_TOKEN_SECRET, bytes) else ADMIN_TOKEN_SECRET.encode('utf-8'), encoded.encode('ascii'), hashlib.sha256).digest()
    return encoded + '.' + base64.urlsafe_b64encode(signature).rstrip(b'=').decode('ascii')


def verify_admin_token(header_value):
    if not header_value or not header_value.startswith('Bearer '):
        return None
    try:
        encoded, signature_text = header_value[7:].split('.', 1)
        secret = ADMIN_TOKEN_SECRET if isinstance(ADMIN_TOKEN_SECRET, bytes) else ADMIN_TOKEN_SECRET.encode('utf-8')
        expected = hmac.new(secret, encoded.encode('ascii'), hashlib.sha256).digest()
        provided = base64.urlsafe_b64decode(signature_text + '=' * (-len(signature_text) % 4))
        if not hmac.compare_digest(expected, provided):
            return None
        payload = json.loads(base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4)))
        if payload.get('sub') != db_manager.ADMIN_EMAIL or int(payload.get('exp', 0)) < int(time.time()):
            return None
        return payload['sub']
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def find_available_port(start_port=8080, max_attempts=50):
    import socket
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return start_port


class ExamServerHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Session-Id')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def get_client_ip(self):
        peer = _normalize_ip(self.client_address[0]) if self.client_address else None
        if peer is None:
            return ''
        if not _is_trusted_proxy(peer):
            return str(peer)

        forwarded = self.headers.get('X-Forwarded-For', '')
        chain = [_normalize_ip(item) for item in forwarded.split(',') if item.strip()]
        chain = [item for item in chain if item is not None]
        current = peer
        for address in reversed(chain):
            if not _is_trusted_proxy(current):
                break
            current = address
        return str(current)

    def require_admin(self):
        email = verify_admin_token(self.headers.get('Authorization', ''))
        if not email:
            self.send_json(401, {'error': 'Administrator sign-in required'})
            return None
        return email

    def log_site_page_access(self, path):
        is_page = path in ('/', '/index.html') or path.lower().endswith('.html')
        is_exam_data = path == '/data/exam_manifest.json' or (path.startswith('/data/tests/') and path.lower().endswith('.json'))
        if not (is_page or is_exam_data):
            return
        try:
            db_manager.log_site_access(self.get_client_ip(), path, self.headers.get('User-Agent', ''))
        except Exception as exc:
            print('Site-access telemetry error:', exc)

    # ── GET routes ───────────────────────────────────────────────────────────

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path
        query  = urllib.parse.parse_qs(parsed.query)

        if path == '/api/user/analytics':
            email = query.get('email', [''])[0]
            if not email:
                return self.send_json(400, {"error": "Email required"})
            return self.send_json(200, db_manager.get_user_analytics(email))

        if path in ('/api/admin/data', '/api/admin/telemetry', '/api/admin/student-detail'):
            admin = self.require_admin()
            if not admin:
                return

        if path == '/api/admin/data':
            return self.send_json(200, db_manager.get_admin_data())

        # ── Telemetry dashboard ───────────────────────────────────────────
        if path == '/api/admin/telemetry':
            data = db_manager.get_telemetry_dashboard(admin)
            return self.send_json(200, data)

        # ── Single-student drill-down ─────────────────────────────────────
        if path == '/api/admin/student-detail':
            student = query.get('studentEmail', [''])[0]
            data = db_manager.get_student_telemetry_detail(admin, student)
            return self.send_json(200, data)

        self.log_site_page_access(path)
        return super().do_GET()

    # ── POST routes ──────────────────────────────────────────────────────────

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path

        content_len = int(self.headers.get('Content-Length', 0))
        body_bytes  = self.rfile.read(content_len) if content_len > 0 else b'{}'
        try:
            body = json.loads(body_bytes.decode('utf-8'))
            if not isinstance(body, dict):
                raise ValueError('JSON body must be an object')
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return self.send_json(400, {"error": "Invalid JSON request body"})

        ip = self.get_client_ip()

        # Auth
        if path == '/api/auth/register':
            email = body.get('email', '')
            name  = body.get('name', '')
            pw    = body.get('password', '')
            if not email or not pw:
                return self.send_json(400, {"error": "Email and password required"})
            ok, result = db_manager.register_user(email, name or email.split('@')[0], pw)
            if not ok:
                return self.send_json(400, {"error": result})
            # Log telemetry
            try:
                db_manager.log_login_event(
                    email, 'register', ip=ip,
                    user_agent=body.get('userAgent', ''),
                    screen_res=body.get('screenRes', ''),
                    platform=body.get('platform', ''),
                    language=body.get('language', ''),
                    timezone=body.get('timezone', ''))
            except Exception:
                pass
            return self.send_json(200, {"success": True, "user": result})

        if path == '/api/auth/login':
            email = body.get('email', '')
            pw    = body.get('password', '')
            if not email or not pw:
                return self.send_json(400, {"error": "Email and password required"})
            ok, result = db_manager.login_user(email, pw)
            if not ok:
                return self.send_json(401, {"error": result})
            # Log telemetry
            try:
                db_manager.log_login_event(
                    email, 'login', ip=ip,
                    user_agent=body.get('userAgent', ''),
                    screen_res=body.get('screenRes', ''),
                    platform=body.get('platform', ''),
                    language=body.get('language', ''),
                    timezone=body.get('timezone', ''))
            except Exception:
                pass
            response = {"success": True, "user": result}
            if result.get('email') == db_manager.ADMIN_EMAIL:
                response['adminToken'] = create_admin_token(result['email'])
            return self.send_json(200, response)

        if path == '/api/auth/unlock':
            email = body.get('email', '')
            code  = body.get('code', '')
            if not email or not code:
                return self.send_json(400, {"error": "Email and code required"})
            ok, msg = db_manager.verify_and_unlock_code(email, code)
            if not ok:
                return self.send_json(400, {"error": msg})
            try:
                db_manager.log_login_event(email, 'code_unlock', ip=ip)
            except Exception:
                pass
            return self.send_json(200, {"success": True, "message": msg})

        # Attempt save
        if path == '/api/attempts/save':
            email   = body.get('email', '')
            attempt = body.get('attempt', {})
            if not email:
                return self.send_json(400, {"error": "User email required"})
            ok, msg = db_manager.save_attempt(email, attempt)
            return self.send_json(200, {"success": ok, "message": msg})

        # Admin toggle
        if path == '/api/admin/toggle-access':
            admin = self.require_admin()
            if not admin:
                return
            target = body.get('targetEmail', '')
            grant  = bool(body.get('grant', True))
            db_manager.toggle_user_access(target, grant)
            return self.send_json(200, {"success": True, "message": f"Access {'granted' if grant else 'revoked'} for {target}"})

        # ── Telemetry endpoints ───────────────────────────────────────────

        if path == '/api/telemetry/session':
            # Start or end of a portal session
            try:
                db_manager.log_session_event(
                    email=body.get('email', ''),
                    session_id=body.get('sessionId', ''),
                    event_type=body.get('eventType', 'start'),
                    duration=body.get('durationSeconds'),
                    pages=body.get('pagesVisited'),
                    series=body.get('seriesBrowsed'),
                    ip=ip)
            except Exception as exc:
                print('Session telemetry error:', exc)
                return self.send_json(500, {"error": "Could not save session telemetry"})
            return self.send_json(200, {"ok": True})

        if path == '/api/telemetry/questions':
            # Per-question telemetry after exam submit
            email = body.get('email', 'guest')
            rows  = body.get('rows', [])
            try:
                db_manager.save_question_telemetry(email, rows, ip=ip)
            except Exception as e:
                print("Q-telemetry error:", e)
                return self.send_json(500, {"error": "Could not save question telemetry"})
            return self.send_json(200, {"ok": True})

        if path == '/api/telemetry/event':
            # Single behavioral event (calculator, bookmark, search, abandon…)
            try:
                db_manager.log_behavior_event(
                    email=body.get('email', ''),
                    session_id=body.get('sessionId', ''),
                    event_type=body.get('eventType', ''),
                    event_data=body.get('data'),
                    ip=ip)
            except Exception as exc:
                print('Behavior telemetry error:', exc)
                return self.send_json(500, {"error": "Could not save behavior telemetry"})
            return self.send_json(200, {"ok": True})

        return self.send_json(404, {"error": "Not Found"})

    def log_message(self, format, *args):
        # Suppress noisy per-request logs; only show errors
        if '404' in str(args) or '500' in str(args):
            super().log_message(format, *args)


def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = int(os.environ.get('PORT', find_available_port(8080)))
    handler = ExamServerHandler

    handler.extensions_map.update({
        '.js':   'application/javascript',
        '.json': 'application/json',
        '.css':  'text/css',
        '.html': 'text/html',
    })

    socketserver.TCPServer.allow_reuse_address = True

    host = '0.0.0.0'
    with socketserver.TCPServer((host, port), handler) as httpd:
        url = f"http://localhost:{port}/index.html"
        print("=" * 65)
        print("  GATE CS CBT EXAM SYSTEM — WITH TELEMETRY")
        print("=" * 65)
        print(f"  URL    : {url}")
        print(f"  Admin  : musicfusion123456@gmail.com / admin123")
        print(f"  Code   : 12G3A4T8WE")
        print(f"  DB     : data/exam_system.db")
        print("  Press Ctrl+C to stop.")
        print("=" * 65)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == '__main__':
    run_server()
