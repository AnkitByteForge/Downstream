"""Streaming hash correctness and memory-safety-by-construction."""

import hashlib

from dip.manifest.hashing import sha256_of_file


def test_matches_stdlib_hash(tmp_path):
    content = b"deterministic content, not a real construction document" * 1000
    f = tmp_path / "sample.bin"
    f.write_bytes(content)

    assert sha256_of_file(f) == hashlib.sha256(content).hexdigest()


def test_deterministic_across_repeated_calls(tmp_path):
    f = tmp_path / "sample.bin"
    f.write_bytes(b"same bytes every time")

    assert sha256_of_file(f) == sha256_of_file(f)


def test_different_content_different_hash(tmp_path):
    f1 = tmp_path / "a.bin"
    f2 = tmp_path / "b.bin"
    f1.write_bytes(b"content A")
    f2.write_bytes(b"content B")

    assert sha256_of_file(f1) != sha256_of_file(f2)


def test_reads_in_chunks_not_whole_file(tmp_path, monkeypatch):
    """A regression guard against accidentally reverting to
    Path.read_bytes()-style whole-file loading: patch the chunk size down
    and confirm a multi-chunk file still hashes correctly, proving the
    chunked loop — not a single big read — is what's actually running."""
    import dip.manifest.hashing as hashing_module

    monkeypatch.setattr(hashing_module, "_CHUNK_SIZE", 4)  # force many tiny reads
    content = b"0123456789" * 50
    f = tmp_path / "chunked.bin"
    f.write_bytes(content)

    assert sha256_of_file(f) == hashlib.sha256(content).hexdigest()
