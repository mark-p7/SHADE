import base64
import os
from pathlib import Path
from PIL import Image
import numpy as np
import sys
from cryptography.fernet import Fernet

def main():
    args = parse_arguments()
    is_encode = args[0]
    image = args[1]
    cipher = args[2]
    input_data = args[3]
    img_file_name = args[4]
        
    if is_encode:
        bits = file_to_bits_string(input_data, cipher)
        encode(image, bits, str(input_data), cipher, str(img_file_name))
    else:
        decode(image, cipher)

def file_to_bits_string(filename, cipher):
    with open(filename, 'rb') as f:
        byte_data = f.read()
    byte_data = cipher.encrypt(byte_data)
    bit_string = "".join(f"{byte:08b}" for byte in byte_data)
    return bit_string

def encode(image, bits, input_data_file_name, cipher, img_file_name):
    print(input_data_file_name)
    print(img_file_name)
    # Handle File name encryption and encoding first
    image_file_name_split = img_file_name.split('\\')
    image_file_name_sliced = image_file_name_split[len(image_file_name_split) - 1]
    file_name_arr = input_data_file_name.split('\\')
    file_name = file_name_arr[len(file_name_arr) - 1]
    encoded_file_name = file_name.encode('utf-8')
    encoded_file_name = cipher.encrypt(encoded_file_name)
    file_name_in_bits = ''.join(f"{byte:08b}" for byte in encoded_file_name)
    
    # Other variables
    pixels = np.array(image)
    size_of_bits_in_bits = f'{len(bits):08b}'
    size_of_filename_in_bits = f'{len(file_name_in_bits):08b}'
    bit_counter = 0
    length, width, _ = pixels.shape
    
    # Quick size check and padding
    if len(size_of_bits_in_bits) > 32:
        print("Size of the input data too large. Please try again.")
    
    while len(size_of_bits_in_bits) < 32:
        size_of_bits_in_bits = "0" + size_of_bits_in_bits

    while len(size_of_filename_in_bits) < 32:
        size_of_filename_in_bits = "0" + size_of_filename_in_bits

    # First 64 bits are allocated to the size of filename and size of file data at an even 32-bit split
    bits = size_of_bits_in_bits + size_of_filename_in_bits + file_name_in_bits + bits
    
    for y in range(length):
        for x in range(width):
            pixel = pixels[y][x]
            
            if bit_counter >= len(bits):
                encoded_image = Image.fromarray(pixels)
                encoded_image.show()
                encoded_image.save(f"./output/{image_file_name_sliced}")
                return
            
            if bits[bit_counter] == "0":
                pixels[y][x][2] = pixel[2] & ~1
            else:
                pixels[y][x][2] = pixel[2] | 1

            bit_counter += 1
            
    print("Input bits exceeded. Please try again with a smaller input.")
    
def decode(image, cipher):
    pixels = np.array(image)
    bit_counter = 0
    message_size = float("inf")
    filename_size = float("inf")
    file_name = ""
    bits = ""
    
    length, width, _ = pixels.shape
    
    for y in range(length):
        for x in range(width):
            bit = pixels[y][x][2] % 2
            bits += str(bit)
            bit_counter += 1
            
            if bit_counter == 32:
                message_size = int(bits, 2)
                bits = ""
            
            if bit_counter == 32 + 32:
                filename_size = int(bits, 2)
                bits = ""
            
            if bit_counter == 32 + 32 + filename_size:
                file_name = convert_bits_to_characters(bits, cipher)
                bits = ""
                
            if bit_counter >= 32 + 256 + filename_size + message_size:
                write_bits_to_file(file_name, bits, cipher)
                return
            

def convert_bits_to_characters(bits, cipher):
    n = int(bits, 2)
    byte_length = (n.bit_length() + 7) // 8
    bytes_data = n.to_bytes(byte_length, 'big')
    bytes_data = cipher.decrypt(bytes_data)
    result = bytes_data.decode('utf-8')
    return result

def write_bits_to_file(filename, bits, cipher):
    byte_list = []
    for i in range(0, len(bits), 8):
        byte_str = bits[i:i+8]
        byte_val = int(byte_str, 2)
        byte_list.append(byte_val)

    binary_data = bytes(byte_list)
    binary_data = cipher.decrypt(binary_data)
    
    with open(f"./output/{filename}", 'wb') as f:
        f.write(binary_data)
    
    print(f"Successfully wrote {len(binary_data)} bytes to {filename}")

def parse_arguments():
    img = None
    img_file_name = None
    path = None
    cipher = None
    try:
        if sys.argv[1] != "-E" and sys.argv[1] != "-D":
            print("Please specify encoding or decoding using either -E for encoding or -D for decoding")
            exit()
        try:
            img = Image.open(sys.argv[2])
            img_file_name = Path(sys.argv[2])
        except FileNotFoundError:
            print("Image does not exist. Check path.")
            exit()
        
        key = str(sys.argv[3])
        try:
            cipher = Fernet(key)
        except ValueError:
            print("Fernet key must be 32 url-safe base64-encoded bytes. Please Try Again")
            exit()
        
        if sys.argv[1] == "-E":
            path = Path(sys.argv[4])
            if not path.exists():
                print("Input data file does NOT exist. Please try again.")
                exit()
    
    except Exception:
        print("Something went wrong. Check arguments and please try again.")
        exit()
        
    return (sys.argv[1] == "-E", img, cipher, path, img_file_name)
    
if __name__ == "__main__":
    main()