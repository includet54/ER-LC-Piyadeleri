import urllib.request
import urllib.parse
import mimetypes
import os
import uuid

filepath = r"C:\Users\pcigd\.gemini\antigravity\brain\f59e0b90-f9b5-44f4-b6e9-21e75323521e\.user_uploaded\media_1790437868610.png"

boundary = uuid.uuid4().hex

def encode_multipart(fields, files):
    lines = []
    for key, value in fields.items():
        lines.append(f'--{boundary}')
        lines.append(f'Content-Disposition: form-data; name="{key}"')
        lines.append('')
        lines.append(value)
    
    for key, (filename, data, content_type) in files.items():
        lines.append(f'--{boundary}')
        lines.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"')
        lines.append(f'Content-Type: {content_type}')
        lines.append('')
        lines.append(None)  # placeholder for binary data
    
    # Build body
    body = b''
    for line in lines:
        if line is None:
            continue
        body += (line + '\r\n').encode('utf-8')
        if line == '' and lines[lines.index(line) + 1] is None:
            # Next is binary data
            break
    
    # Simpler approach
    body = b''
    # Add fields
    for key, value in fields.items():
        body += f'--{boundary}\r\n'.encode()
        body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
        body += f'{value}\r\n'.encode()
    
    # Add file
    for key, (filename, data, content_type) in files.items():
        body += f'--{boundary}\r\n'.encode()
        body += f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode()
        body += f'Content-Type: {content_type}\r\n\r\n'.encode()
        body += data
        body += b'\r\n'
    
    body += f'--{boundary}--\r\n'.encode()
    
    return body, f'multipart/form-data; boundary={boundary}'

with open(filepath, 'rb') as f:
    file_data = f.read()

body, content_type = encode_multipart(
    fields={'reqtype': 'fileupload'},
    files={'fileToUpload': ('logo.png', file_data, 'image/png')}
)

req = urllib.request.Request(
    'https://catbox.moe/user/api.php',
    data=body,
    headers={'Content-Type': content_type}
)

response = urllib.request.urlopen(req)
print(response.read().decode())
