import os
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit for requests
ALLOWED_EXTENSIONS = {'mp4', 'mkv', 'webm', 'mp3'}

# Ensure download folder exists
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/download', methods=['POST'])
def download_channel():
    data = request.get_json()
    channel_url = data.get('channel_url')
    format = data.get('format', 'best')
    
    if not channel_url:
        return jsonify({'success': False, 'message': 'Channel URL is required'}), 400
    
    try:
        # Use yt-dlp to download all videos from the channel
        cmd = [
            'yt-dlp',
            '-f', format,
            '-o', os.path.join(app.config['DOWNLOAD_FOLDER'], '%(title)s.%(ext)s'),
            '--yes-playlist',
            channel_url
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            return jsonify({
                'success': False,
                'message': stderr.decode('utf-8')
            }), 500
            
        return jsonify({
            'success': True,
            'message': 'Download started successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/downloads', methods=['GET'])
def list_downloads():
    files = []
    for filename in os.listdir(app.config['DOWNLOAD_FOLDER']):
        path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
        if os.path.isfile(path) and allowed_file(filename):
            files.append({
                'name': filename,
                'size': os.path.getsize(path),
                'url': f"/api/downloads/{filename}"
            })
    return jsonify(files)

@app.route('/api/downloads/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(
        app.config['DOWNLOAD_FOLDER'],
        filename,
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)