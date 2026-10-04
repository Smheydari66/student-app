import os
import sys

if __name__ == '__main__':
    port = os.environ.get('PORT', '8501')
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base_dir, 'student_management_app.py')
    
    cmd = [
        sys.executable,
        '-m', 'streamlit', 'run',
        app_path,
        f'--server.port={port}',
        '--server.address=0.0.0.0',
        '--server.headless=true',
        '--server.enableCORS=false',
        '--server.enableXsrfProtection=false'
    ]
    
    print(f'Starting Streamlit on port {port}...')
    os.execv(sys.executable, cmd)

