# SHADE

**S**teganographic **H**iding with **A**ES-**D**riven **E**ncryption

SHADE is a command-line tool that hides any file (text, images, binaries) inside a PNG image by encoding it into the least significant bits of the image's pixels. The payload and its original filename are encrypted with a symmetric key before embedding, so a stego image gives up nothing without the key. The output looks the same as the cover image to the eye.

## How it works

**Encoding (`-E`)**
1. The input file is read as raw bytes and encrypted with [Fernet](https://cryptography.io/en/latest/fernet/) (AES-128-CBC + HMAC-SHA256), which gives both confidentiality and tamper detection.
2. The original filename is encrypted separately so it can be restored on extraction.
3. A bitstream is built with a fixed-size header followed by the data:

   | Field | Size |
   |---|---|
   | Encrypted payload length | 32 bits |
   | Encrypted filename length | 32 bits |
   | Encrypted filename | variable |
   | Encrypted payload | variable |

4. Each bit is written into the least significant bit of a pixel's **blue channel**, scanning row by row. Changing a channel value by at most 1 (out of 255) can't be seen.
5. The stego image is saved to `output/` under the cover image's name.

**Decoding (`-D`)**
1. LSBs are read back from the blue channel in the same order.
2. The two 32-bit headers tell the decoder where the filename ends and how much payload to read.
3. The filename and payload are decrypted with the shared key, and the original file is written to `output/`. A wrong key or a modified image fails Fernet's HMAC check instead of producing garbage.

**Capacity:** 1 bit per pixel, so a 1920×1080 cover holds about 259 KB of encrypted data. Fernet's base64 encoding adds about 33% overhead, which leaves roughly 190 KB of plaintext.

## Project structure

```
source/
  app.py            # Encoder/decoder CLI
  requirements.txt
  images/           # Sample cover images (solid black/white/yellow, complex photo)
  input/            # Sample payloads (small/medium text, binary PNG)
  output/           # Stego images and recovered files are written here
  comparison*.txt   # Byte-level diffs of original vs. recovered files (PowerShell Compare-Object)
```

## Usage

Requires Python 3.11+.

```bash
cd source
pip install -r requirements.txt

# Generate a key (share it with the recipient out-of-band)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Hide a file inside an image
python app.py -E <cover_image.png> <fernet_key> <file_to_hide>

# Extract a hidden file
python app.py -D <stego_image.png> <fernet_key>
```

Example:

```bash
python app.py -E images/complex.png "$KEY" input/binary.png   # -> output/complex.png
python app.py -D output/complex.png "$KEY"                     # -> output/binary.png
```

> Use lossless formats (PNG/BMP) for the cover and output. JPEG compression destroys LSB data.

## Testing

Tested with plain-text and binary payloads across uniform-color covers (black, white, yellow) and a high-detail photograph. Byte-for-byte comparison of the original and recovered files showed no differences. Invalid input was also covered: bad flags, missing files, malformed keys, and payloads too large for the cover.
