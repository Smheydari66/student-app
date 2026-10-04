import os
import sys

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base_dir, 'student_management_app.py')
    cmd = f'{sys.executable} -m streamlit run "{app_path}" --server.port 8501 --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false'
    print(f"Starting Streamlit via main.py: {cmd}")
    os.system(cmd)

