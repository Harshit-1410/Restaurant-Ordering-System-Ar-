#!/usr/bin/env python3
import http.server
import socketserver
import mimetypes
import os

# Add USDZ MIME type for AR Quick Look
mimetypes.add_type('model/vnd.usdz+zip', '.usdz')
mimetypes.add_type('model/usd+zip', '.usdz')

class ARHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for AR files
        if self.path.endswith('.usdz'):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-Type', 'model/vnd.usdz+zip')
        super().end_headers()

    def guess_type(self, path):
        """Override to ensure USDZ files get correct MIME type"""
        if path.endswith('.usdz'):
            return 'model/vnd.usdz+zip'
        return super().guess_type(path)

if __name__ == "__main__":
    PORT = 8080
    
    print(f"Starting AR-enabled server on port {PORT}")
    print(f"Server will serve USDZ files with proper MIME type for iOS AR Quick Look")
    print(f"Access your website at: http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ARHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
