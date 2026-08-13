from __future__ import annotations

import logging

from consumers.trigger_detected_consumer import run_forever

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
