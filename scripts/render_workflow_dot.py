import json
import argparse
from pathlib import Path

def build_dot(wf):
    lines = [
        'digraph workflow {',
        '  rankdir=LR;',
        '  node [shape=box, style=rounded, fontsize=10];',
    ]
    stages = wf.get('stages', [])
    for i, s in enumerate(stages):
        nid = s.get('id', f's{i}')
        agent = s.get('agent', '')
        label = f"{nid}\\n{agent}"
        style = 'filled' if 'Checkpoint' in agent or 'Checkpoint' in nid else ''
        color = 'lightgoldenrod' if 'Checkpoint' in agent or 'Checkpoint' in nid else 'lightgrey'
        lines.append(f'  "{nid}" [label="{label}" style="{style}" fillcolor="{color}"];')
    for a, b in zip(stages, stages[1:]):
        lines.append(f'  "{a.get("id")}" -> "{b.get("id")}";')
    lines.append('}')
    return '\\n'.join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workflow', default='workflow.json')
    ap.add_argument('--out', default='workflow.dot')
    args = ap.parse_args()
    wf = json.loads(Path(args.workflow).read_text(encoding='utf-8'))
    dot = build_dot(wf)
    Path(args.out).write_text(dot, encoding='utf-8')
    print(f"Wrote {args.out}")

if __name__ == '__main__':
    main()