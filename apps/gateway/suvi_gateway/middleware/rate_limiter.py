import time

class SimpleRateLimiter:
    """
    Prevents the desktop client from spamming the AI and running up your Vertex API bill.
    """
    def __init__(self, requests_per_second: int = 5):
        self.rate = requests_per_second
        self.last_requests = {}

    def is_allowed(self, client_id: str) -> bool:
        current_time = time.time()
        
        # Keep track of when this client last made a request
        if client_id in self.last_requests:
            time_passed = current_time - self.last_requests[client_id]
            if time_passed < (1.0 / self.rate):
                return False # Blocking: Too fast!
                
        self.last_requests[client_id] = current_time
        return True