# Allow `python -m src` to offer quick commands
import sys
from src.runner import run_workflow

if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'run':
        import json
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            inv = json.load(f)
        run_workflow(inv)
    else:
        print('Usage: python -m src run <invoice.json>')
