from PIL import Image
import struct
import os

def embed_data(carrier_path: str, payload_path: str, output_path: str):
    """Embed the contents of payload_path into the LSBs of the carrier image."""
    with open(payload_path, 'rb') as f:
        payload = f.read()
    
    # Prefix with 8-byte length
    length_bytes = struct.pack(">Q", len(payload))
    data = length_bytes + payload
    
    img = Image.open(carrier_path)
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA')
        
    pixels = list(img.getdata())
    num_channels = len(pixels[0])
    
    required_bits = len(data) * 8
    if required_bits > len(pixels) * num_channels:
        raise ValueError(f"Carrier image is too small. Needs {required_bits} bits, but image has {len(pixels) * num_channels} bits.")
    
    # Flatten pixels
    flat_pixels = [channel for pixel in pixels for channel in pixel]
    
    # Embed data
    for i in range(len(data)):
        byte = data[i]
        for j in range(8):
            bit = (byte >> (7 - j)) & 1
            idx = i * 8 + j
            flat_pixels[idx] = (flat_pixels[idx] & 0xFE) | bit
            
    # Reconstruct pixels
    new_pixels = [tuple(flat_pixels[i:i+num_channels]) for i in range(0, len(flat_pixels), num_channels)]
    img.putdata(new_pixels)
    img.save(output_path, "PNG")

def extract_data(carrier_path: str, output_path: str):
    """Extract data from the LSBs of a carrier image and write it to output_path."""
    img = Image.open(carrier_path)
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA')
        
    pixels = list(img.getdata())
    flat_pixels = [channel for pixel in pixels for channel in pixel]
    
    # Extract first 8 bytes for length
    if len(flat_pixels) < 64:
        raise ValueError("Image too small to contain a HexCrypt stego header.")
        
    length_bytes = bytearray(8)
    for i in range(8):
        byte = 0
        for j in range(8):
            idx = i * 8 + j
            byte = (byte << 1) | (flat_pixels[idx] & 1)
        length_bytes[i] = byte
        
    payload_len = struct.unpack(">Q", length_bytes)[0]
    required_bits = 64 + payload_len * 8
    
    if len(flat_pixels) < required_bits:
        raise ValueError("Corrupted or invalid stego image: declared payload length exceeds image capacity.")
        
    payload = bytearray(payload_len)
    for i in range(payload_len):
        byte = 0
        for j in range(8):
            idx = 64 + i * 8 + j
            byte = (byte << 1) | (flat_pixels[idx] & 1)
        payload[i] = byte
        
    with open(output_path, 'wb') as f:
        f.write(payload)
