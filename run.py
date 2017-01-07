#! /usr/bin/python3
import http.server
import urllib.request, urllib.error, urllib.parse
from os import sep, path, environ
import ssl

import i2pcontrol
import json

listen_port = 8082
i2pcontrol_url = "https://127.0.0.1:7650/"
i2pd_dir = path.join(environ["HOME"], ".i2pd")
cert = path.join(i2pd_dir, "i2pcontrol.pem")

def resp_html(s):
    """Response to GET requests with actual documents"""
    legal_files = ["/js/lib/underscore-min.js", "/js/app.js", "/favicon.ico",
            "/js/functions.js",
            "/css/main.css"]

    if s.path == "/":
        s.send_response(200)
        s.send_header("Content-Type", "text/html")
        s.end_headers()
        with open("index.html", 'rb') as f:
            s.wfile.write(f.read())
    elif s.path in legal_files:
        s.send_response(200)
        s.end_headers()
        file_path = s.path[1:].replace("/", sep)
        with open(file_path, 'rb') as f:
            s.wfile.write(f.read())
    else:
        s.send_error(404, "Not Found")

def proxy_request(data, s):
    """Send data to i2pcontrol port and return response"""
    try:
        ctl = i2pcontrol.I2PController(ssl_cert=cert)
        j = json.loads(data.decode("utf-8"))
        if 'method' not in j:
            raise Exception("no method specified")
        if 'params' not in j:
            raise Exception("no params specified")
        r = ctl.call(j["method"], j['params'])
        s.send_response(200)
        s.send_header("Content-Type", "application/json")
        s.end_headers()
        s.wfile.write(json.dumps({'result': r, 'method': j['method'], 'jsonrpc': '2.0'}).encode("utf-8"))
    except Exception as e:
        s.send_error(500, "Cannot connect to I2PControl port: {}".format(e))
        raise e

class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(s):
        resp_html(s)

    def do_POST(s):
        content_length = int(s.headers['Content-Length'])
        post_data = s.rfile.read(content_length)
        proxy_request(post_data, s)

if __name__ == "__main__":
    httpd = http.server.HTTPServer(("127.0.0.1", listen_port), MyHandler)
    try:
        print(("WebUI is listening at http://127.0.0.1:" + str(listen_port)))
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()
