#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "config/capacity.json").read_text(encoding="utf-8"))


def main() -> None:
    assert DATA["target"] == "GREEN"
    assert DATA["runtime"] == "original-game-boy-rom"
    assert DATA["policy_target_generation"] >= 10

    source = DATA["source"]
    assert source["mapper"] == "MBC1+RAM+BATTERY"
    assert source["rom_bytes"] == 0x80000
    assert source["sram_bytes"] == 0x8000

    expanded = DATA["expanded"]
    assert expanded["mapper"] == "MBC5+RAM+BATTERY"
    assert expanded["rom_bytes"] == 0x800000
    assert expanded["rom_banks"] == 512
    assert expanded["rom_bank_bits"] == 9
    assert expanded["sram_bytes"] == 0x20000
    assert expanded["sram_banks"] == 16

    for width in DATA["id_width_bits"].values():
        assert width >= 16

    far = DATA["far_reference"]
    assert far["bank_bits"] >= 9
    assert far["address_bits"] == 16
    assert far["storage_bytes"] >= 4

    invariants = set(DATA["invariants"])
    assert "original-rom-is-the-runtime-baseline" in invariants
    assert "no-gba-engine-dependency" in invariants

    print("GREEN original-ROM expansion policy: OK")


if __name__ == "__main__":
    main()
