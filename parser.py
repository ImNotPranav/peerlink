"""
Bencode encoder and decoder.

Implements the bencoding format used by .torrent files and tracker responses.
Supports integers, byte strings, lists, and dictionaries.
"""

from exceptions import BencodeError


def bdecode(data, position=0):
    """Decode a bencoded value starting at *position* in *data*.

    Returns a (value, next_position) tuple so the caller can continue
    decoding the remaining bytes.
    """
    try:
        byte = data[position]
    except IndexError:
        raise BencodeError("Unexpected end of data while decoding")

    # Integer: i<digits>e
    if byte == ord('i'):
        try:
            end = data.index(ord('e'), position)
        except ValueError:
            raise BencodeError("Unterminated integer — missing 'e'")
        return int(data[position + 1:end]), end + 1

    # Byte string: <length>:<content>
    if ord('0') <= byte <= ord('9'):
        try:
            colon = data.index(ord(':'), position)
        except ValueError:
            raise BencodeError("Malformed byte string — missing ':'")
        length = int(data[position:colon])
        start = colon + 1
        end = start + length
        return data[start:end], end

    # List: l<items>e
    if byte == ord('l'):
        position += 1
        items = []
        while data[position] != ord('e'):
            value, position = bdecode(data, position)
            items.append(value)
        return items, position + 1

    # Dictionary: d<key-value pairs>e
    if byte == ord('d'):
        position += 1
        entries = {}
        while data[position] != ord('e'):
            key, position = bdecode(data, position)
            value, position = bdecode(data, position)
            entries[key] = value
        return entries, position + 1

    raise BencodeError(f"Unexpected byte 0x{byte:02x} at position {position}")


def bencode(obj):
    """Encode a Python object into its bencoded byte-string representation."""

    # Integer
    if isinstance(obj, int):
        return b"i" + str(obj).encode() + b"e"

    # Bytes
    if isinstance(obj, bytes):
        return str(len(obj)).encode() + b":" + obj

    # String → encode to bytes first
    if isinstance(obj, str):
        encoded = obj.encode()
        return str(len(encoded)).encode() + b":" + encoded

    # List
    if isinstance(obj, list):
        return b"l" + b"".join(bencode(item) for item in obj) + b"e"

    # Dictionary
    if isinstance(obj, dict):
        items = b"".join(bencode(k) + bencode(v) for k, v in obj.items())
        return b"d" + items + b"e"

    raise BencodeError(f"Cannot bencode type: {type(obj)}")
