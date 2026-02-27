#!/usr/bin/env python3
"""Generate tests/sample.wav — a 1-second 440 Hz sine wave (16-bit mono 16 kHz).

Run once before executing the integration tests:
    python tests/make_sample_wav.py
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

OUTPUT = Path(__file__).parent / "sample.wav"

SAMPLE_RATE = 16_000
DURATION_S = 1
FREQUENCY = 440.0


def main() -> None:
    n = SAMPLE_RATE * DURATION_S
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUTPUT), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        for i in range(n):
            value = int(32_767 * math.sin(2 * math.pi * FREQUENCY * i / SAMPLE_RATE))
            wf.writeframes(struct.pack("<h", value))
    print(f"Written: {OUTPUT}  ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
