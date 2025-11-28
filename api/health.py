"""
Health check endpoint for Vercel
"""

from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    """Health check handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        response_data = {
            "status": "healthy",
            "service": "bill-extraction",
            "version": "2.0.0"
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())
