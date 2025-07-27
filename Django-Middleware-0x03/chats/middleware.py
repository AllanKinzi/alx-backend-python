# chats/middleware.py
from datetime import datetime, time
from django.http import HttpResponseForbidden
import logging
from datetime import datetime
from collections import defaultdict, deque
from threading import Lock

# Configure the logger
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('requests.log')
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user if request.user.is_authenticated else 'Anonymous'
        log_entry = f"{datetime.now()} - User: {user} - Path: {request.path}"
        logger.info(log_entry)
        response = self.get_response(request)
        return response
    
class RestrictAccessByTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Define the access window: 6 PM to 9 PM
        start_time = time(18, 0)  # 6:00 PM
        end_time = time(21, 0)    # 9:00 PM
        now = datetime.now().time()

        # Allow only if current time is between 6 PM and 9 PM
        if not (start_time <= now <= end_time):
            return HttpResponseForbidden("Access to chat is allowed only between 6 PM and 9 PM.")

        return self.get_response(request)


class RateLimitByIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Store message timestamps per IP
        self.message_logs = defaultdict(deque)
        self.limit = 5  # Max messages
        self.window_seconds = 60  # 1 minute

    def __call__(self, request):
        # Apply rate-limiting only to POST requests to /api/messages/ or similar
        if request.method == "POST" and "/messages" in request.path:
            ip = self.get_client_ip(request)
            now = time.time()

            logs = self.message_logs[ip]

            # Remove timestamps older than the window
            while logs and now - logs[0] > self.window_seconds:
                logs.popleft()

            if len(logs) >= self.limit:
                return HttpResponseForbidden("Rate limit exceeded: Max 5 messages per minute.")

            logs.append(now)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
    
class RolePermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only check role-based access for unsafe methods
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            user = getattr(request, "user", None)

            if user and user.is_authenticated:
                if user.role not in ["admin"]:  # You can add "moderator" if needed
                    return HttpResponseForbidden("403 Forbidden: Insufficient role permissions.")
            else:
                return HttpResponseForbidden("403 Forbidden: Authentication required.")

        return self.get_response(request)
    
class OffensiveLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_log = defaultdict(list)  # {ip: [timestamps]}
        self.lock = Lock()
        self.limit = 5  # messages
        self.window = 60  # seconds

    def __call__(self, request):
        if request.method == 'POST' and request.path.startswith("/chats/"):
            ip = self.get_client_ip(request)
            now = time.time()

            with self.lock:
                # Remove timestamps older than the window
                self.request_log[ip] = [
                    t for t in self.request_log[ip] if now - t < self.window
                ]

                if len(self.request_log[ip]) >= self.limit:
                    return HttpResponseForbidden("403 Forbidden: Message rate limit exceeded (5 messages/minute).")

                self.request_log[ip].append(now)

        return self.get_response(request)

    def get_client_ip(self, request):
        """ Get the client's IP address, considering reverse proxy headers if needed """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")