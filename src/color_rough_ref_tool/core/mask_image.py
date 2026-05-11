"""Save simple hand mask images."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
import zlib


MASK_FILE_SUFFIX = "_hand_mask.png"


@dataclass(frozen=True, slots=True)
class BrushMaskStroke:
    """A brush stroke segment on the displayed mask canvas."""

    start: tuple[int, int]
    end: tuple[int, int]
    size: int


@dataclass(frozen=True, slots=True)
class RectangleMask:
    """A rectangular mask area on the displayed mask canvas."""

    start: tuple[int, int]
    end: tuple[int, int]


MaskOperation = BrushMaskStroke | RectangleMask


def mask_file_name_for_candidate(candidate_file_name: str) -> str:
    """Return the default mask file name for a selected candidate."""

    return f"{Path(candidate_file_name).stem}{MASK_FILE_SUFFIX}"


def save_mask_png(
    *,
    width: int,
    height: int,
    operations: tuple[MaskOperation, ...],
    masks_dir: Path | str,
    candidate_file_name: str,
) -> Path:
    """Save a black background / white mask PNG and return its path."""

    if width <= 0 or height <= 0:
        raise ValueError("Mask image size must be positive.")
    if not operations:
        raise ValueError("Mask must include at least one stroke or rectangle.")

    pixels = bytearray(width * height)
    for operation in operations:
        if isinstance(operation, BrushMaskStroke):
            _draw_brush_stroke(pixels, width, height, operation)
        else:
            _draw_rectangle(pixels, width, height, operation)

    output_dir = Path(masks_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / mask_file_name_for_candidate(candidate_file_name)
    output_path.write_bytes(_encode_grayscale_png(width, height, bytes(pixels)))
    return output_path


def _draw_brush_stroke(
    pixels: bytearray,
    width: int,
    height: int,
    stroke: BrushMaskStroke,
) -> None:
    x1, y1 = stroke.start
    x2, y2 = stroke.end
    steps = max(abs(x2 - x1), abs(y2 - y1), 1)
    radius = max(1, stroke.size // 2)
    for step in range(steps + 1):
        x = round(x1 + (x2 - x1) * step / steps)
        y = round(y1 + (y2 - y1) * step / steps)
        _fill_circle(pixels, width, height, x, y, radius)


def _draw_rectangle(
    pixels: bytearray,
    width: int,
    height: int,
    rectangle: RectangleMask,
) -> None:
    x1, y1 = rectangle.start
    x2, y2 = rectangle.end
    left = max(0, min(x1, x2))
    right = min(width - 1, max(x1, x2))
    top = max(0, min(y1, y2))
    bottom = min(height - 1, max(y1, y2))
    for y in range(top, bottom + 1):
        row = y * width
        for x in range(left, right + 1):
            pixels[row + x] = 255


def _fill_circle(
    pixels: bytearray,
    width: int,
    height: int,
    center_x: int,
    center_y: int,
    radius: int,
) -> None:
    radius_squared = radius * radius
    for y in range(center_y - radius, center_y + radius + 1):
        if y < 0 or y >= height:
            continue
        row = y * width
        for x in range(center_x - radius, center_x + radius + 1):
            if x < 0 or x >= width:
                continue
            if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius_squared:
                pixels[row + x] = 255


def _encode_grayscale_png(width: int, height: int, pixels: bytes) -> bytes:
    rows = [
        b"\x00" + pixels[y * width : (y + 1) * width]
        for y in range(height)
    ]
    raw_image = b"".join(rows)
    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(raw_image)),
            _png_chunk(b"IEND", b""),
        )
    )


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", checksum)
