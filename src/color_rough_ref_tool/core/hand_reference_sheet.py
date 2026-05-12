"""Export a simple hand reference sheet image."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import struct
import zlib

from color_rough_ref_tool.integrations.comfyui.hand_inpainting import HandReferenceOutputImage


HAND_REFERENCE_SHEET_FILENAME = "hand_sheet_001.png"
SHEET_BACKGROUND_RGB = (255, 255, 255)
SHEET_COLUMNS = 3
SHEET_THUMBNAIL_MAX_SIZE = 256
SHEET_PADDING = 16
SHEET_GAP = 12

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True, slots=True)
class _RgbImage:
    width: int
    height: int
    pixels: bytes


def export_hand_reference_sheet(
    hand_refs: tuple[HandReferenceOutputImage, ...],
    sheets_dir: Path | str,
    *,
    file_name: str = HAND_REFERENCE_SHEET_FILENAME,
    columns: int = SHEET_COLUMNS,
    thumbnail_max_size: int = SHEET_THUMBNAIL_MAX_SIZE,
) -> Path:
    """Create a simple PNG sheet from saved hand reference PNG images."""

    if not hand_refs:
        raise ValueError("At least one hand reference image is required.")
    if columns <= 0:
        raise ValueError("Sheet column count must be positive.")
    if thumbnail_max_size <= 0:
        raise ValueError("Sheet thumbnail size must be positive.")

    source_images = tuple(_resize_to_fit(_read_png_rgb(output.path), thumbnail_max_size) for output in hand_refs)
    used_columns = min(columns, len(source_images))
    rows = math.ceil(len(source_images) / used_columns)
    sheet_width = (SHEET_PADDING * 2) + (used_columns * thumbnail_max_size) + ((used_columns - 1) * SHEET_GAP)
    sheet_height = (SHEET_PADDING * 2) + (rows * thumbnail_max_size) + ((rows - 1) * SHEET_GAP)

    background = bytes(SHEET_BACKGROUND_RGB)
    sheet_pixels = bytearray(background * (sheet_width * sheet_height))
    for index, image in enumerate(source_images):
        column = index % used_columns
        row = index // used_columns
        cell_x = SHEET_PADDING + column * (thumbnail_max_size + SHEET_GAP)
        cell_y = SHEET_PADDING + row * (thumbnail_max_size + SHEET_GAP)
        paste_x = cell_x + (thumbnail_max_size - image.width) // 2
        paste_y = cell_y + (thumbnail_max_size - image.height) // 2
        _paste_rgb(sheet_pixels, sheet_width, image, paste_x, paste_y)

    output_dir = Path(sheets_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / file_name
    output_path.write_bytes(_encode_rgb_png(sheet_width, sheet_height, bytes(sheet_pixels)))
    return output_path


def _read_png_rgb(path: Path | str) -> _RgbImage:
    image_path = Path(path)
    if image_path.suffix.lower() != ".png":
        raise ValueError(f"Hand reference sheet currently supports PNG source images only: {image_path}")

    data = image_path.read_bytes()
    if not data.startswith(_PNG_SIGNATURE):
        raise ValueError(f"Hand reference image is not a PNG file: {image_path}")

    offset = len(_PNG_SIGNATURE)
    width = 0
    height = 0
    bit_depth = -1
    color_type = -1
    idat_parts: list[bytes] = []
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError(f"PNG file is truncated: {image_path}")
        chunk_length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_start = offset + 8
        chunk_end = chunk_start + chunk_length
        if chunk_end + 4 > len(data):
            raise ValueError(f"PNG chunk is truncated: {image_path}")
        chunk_data = data[chunk_start:chunk_end]
        offset = chunk_end + 4

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, png_filter, interlace = struct.unpack(
                ">IIBBBBB",
                chunk_data,
            )
            if bit_depth != 8 or color_type not in (0, 2, 6):
                raise ValueError(f"Unsupported PNG color format for hand reference sheet: {image_path}")
            if compression != 0 or png_filter != 0 or interlace != 0:
                raise ValueError(f"Unsupported PNG encoding for hand reference sheet: {image_path}")
        elif chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    if width <= 0 or height <= 0 or not idat_parts:
        raise ValueError(f"PNG file is missing image data: {image_path}")

    return _decode_png_rows(
        width=width,
        height=height,
        color_type=color_type,
        raw_data=zlib.decompress(b"".join(idat_parts)),
    )


def _decode_png_rows(
    *,
    width: int,
    height: int,
    color_type: int,
    raw_data: bytes,
) -> _RgbImage:
    bytes_per_pixel = {0: 1, 2: 3, 6: 4}[color_type]
    row_size = width * bytes_per_pixel
    expected_size = height * (row_size + 1)
    if len(raw_data) < expected_size:
        raise ValueError("PNG image data is shorter than expected.")

    previous_row = bytearray(row_size)
    rows: list[bytes] = []
    offset = 0
    for _ in range(height):
        filter_type = raw_data[offset]
        offset += 1
        current_row = bytearray(raw_data[offset : offset + row_size])
        offset += row_size
        _unfilter_png_row(current_row, previous_row, filter_type, bytes_per_pixel)
        rows.append(_row_to_rgb(current_row, width, color_type))
        previous_row = current_row

    return _RgbImage(width=width, height=height, pixels=b"".join(rows))


def _unfilter_png_row(
    current_row: bytearray,
    previous_row: bytearray,
    filter_type: int,
    bytes_per_pixel: int,
) -> None:
    for index, value in enumerate(current_row):
        left = current_row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
        up = previous_row[index]
        upper_left = previous_row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
        if filter_type == 0:
            addend = 0
        elif filter_type == 1:
            addend = left
        elif filter_type == 2:
            addend = up
        elif filter_type == 3:
            addend = (left + up) // 2
        elif filter_type == 4:
            addend = _paeth_predictor(left, up, upper_left)
        else:
            raise ValueError(f"Unsupported PNG row filter: {filter_type}")
        current_row[index] = (value + addend) & 0xFF


def _row_to_rgb(row: bytearray, width: int, color_type: int) -> bytes:
    if color_type == 0:
        rgb = bytearray(width * 3)
        for x in range(width):
            value = row[x]
            rgb[x * 3 : x * 3 + 3] = bytes((value, value, value))
        return bytes(rgb)
    if color_type == 2:
        return bytes(row)

    rgb = bytearray(width * 3)
    for x in range(width):
        source = x * 4
        target = x * 3
        red, green, blue, alpha = row[source : source + 4]
        rgb[target] = _composite_over_white(red, alpha)
        rgb[target + 1] = _composite_over_white(green, alpha)
        rgb[target + 2] = _composite_over_white(blue, alpha)
    return bytes(rgb)


def _composite_over_white(value: int, alpha: int) -> int:
    return (value * alpha + 255 * (255 - alpha)) // 255


def _paeth_predictor(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def _resize_to_fit(image: _RgbImage, max_size: int) -> _RgbImage:
    scale = min(max_size / image.width, max_size / image.height, 1.0)
    target_width = max(1, int(image.width * scale))
    target_height = max(1, int(image.height * scale))
    if target_width == image.width and target_height == image.height:
        return image

    resized = bytearray(target_width * target_height * 3)
    for y in range(target_height):
        source_y = min(image.height - 1, int(y / scale))
        for x in range(target_width):
            source_x = min(image.width - 1, int(x / scale))
            source_index = (source_y * image.width + source_x) * 3
            target_index = (y * target_width + x) * 3
            resized[target_index : target_index + 3] = image.pixels[source_index : source_index + 3]
    return _RgbImage(width=target_width, height=target_height, pixels=bytes(resized))


def _paste_rgb(
    sheet_pixels: bytearray,
    sheet_width: int,
    image: _RgbImage,
    paste_x: int,
    paste_y: int,
) -> None:
    for y in range(image.height):
        source_start = y * image.width * 3
        source_end = source_start + image.width * 3
        target_start = ((paste_y + y) * sheet_width + paste_x) * 3
        sheet_pixels[target_start : target_start + image.width * 3] = image.pixels[source_start:source_end]


def _encode_rgb_png(width: int, height: int, pixels: bytes) -> bytes:
    rows = [
        b"\x00" + pixels[y * width * 3 : (y + 1) * width * 3]
        for y in range(height)
    ]
    raw_image = b"".join(rows)
    return b"".join(
        (
            _PNG_SIGNATURE,
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(raw_image)),
            _png_chunk(b"IEND", b""),
        )
    )


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", checksum)
