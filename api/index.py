import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
backend_dir = os.path.join(project_root, 'backend')

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ['PYTHONPATH'] = backend_dir + os.pathsep + os.environ.get('PYTHONPATH', '')

from app.main import app
