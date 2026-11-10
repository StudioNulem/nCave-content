"""Verify staged or downloaded public nCave-content release DATs (stdlib only)."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("assets", type=Path)
args = parser.parse_args()
catalog = json.loads((root / "catalog/thesauri.json").read_text(encoding="utf-8"))
tag = catalog["releaseTag"]
packets = catalog["packages"]
assert len({p["id"] for p in packets}) == len(packets)
assert {p.name for p in args.assets.glob("*.dat")} == {m["file"] for m in packets}
digest = lambda data: hashlib.sha256(data).hexdigest()
checksums = ""
for m in packets:
    locale = m["locale"]
    data = (args.assets / m["file"]).read_bytes()
    assert len(data) == m["bytes"] and digest(data) == m["sha256"], locale
    assert m["url"] == (
        "https://github.com/StudioNulem/nCave-content/releases/download/"
        f"{tag}/{m['file']}"
    )
    assert json.loads((root / f"thesauri/{locale}/metadata.json").read_text(encoding="utf-8")) == m
    for ref in ("licenseNotice", "correspondingSource"):
        assert (root / m[ref]).is_file(), m[ref]
    if m["provenance"] == "original":
        assert digest(data) == m["upstream"]["datSha256"]
    elif m["provenance"] == "derived":
        path = root / f"corresponding-source/{locale}/source-original.dat.gz"
        original = gzip.decompress(path.read_bytes())
        assert digest(original) == m["upstream"]["datSha256"], locale
        with tempfile.TemporaryDirectory() as work:
            source = Path(work) / "source.dat"
            out = Path(work) / "out.dat"
            source.write_bytes(original)
            subprocess.run(
                [sys.executable, root / "corresponding-source/derive_mythes.py", source, out],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            assert out.read_bytes() == data, locale
    else:
        raise ValueError(m["provenance"])
    checksums += f"{m['sha256']}  {m['file']}\n"
    print(f"OK {locale}: {len(data):,} bytes; SHA-256 {digest(data)}; {m['provenance']}")
checksums_path = args.assets / "SHA256SUMS.txt"
if checksums_path.is_file():
    assert checksums_path.read_text(encoding="ascii") == checksums
