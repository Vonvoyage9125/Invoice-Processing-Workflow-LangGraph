import yaml
import os
from typing import List

TOOLS_YAML = os.path.join(os.path.dirname(__file__), '..', 'tools.yaml')


def _load_pools():
    try:
        with open(TOOLS_YAML, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('bigtool_pools', {}) if data else {}
    except FileNotFoundError:
        return {}


class BigtoolPicker:
    def __init__(self, pools=None):
        self.pools = pools or _load_pools()

    def select(self, capability: str, context: dict = None) -> str:
        # Simple deterministic pick: return first in pool or a fallback
        pool: List[str] = self.pools.get(capability, [])
        if pool:
            return pool[0]
        # fallback mapping
        fallbacks = {
            'ocr': 'tesseract',
            'enrichment': 'vendor_db',
            'erp_connector': 'mock_erp',
            'db': 'sqlite',
            'email': 'sendgrid'
        }
        return fallbacks.get(capability, 'mock_tool')


if __name__ == '__main__':
    p = BigtoolPicker()
    print('OCR pick ->', p.select('ocr'))
