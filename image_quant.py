import cv2
import numpy as np
import struct
import zstd

def quantize_grayscale(image: np.ndarray, num_bits: int) -> np.ndarray:
    """
    Quantizes a grayscale image to a specified number of bits.
    
    Args:
        image (np.ndarray): Grayscale image (values between 0 and 255).
        num_bits (int): Number of bits for quantization (1-8).
    
    Returns:
        np.ndarray: Quantized grayscale image.
    """
    if not (1 <= num_bits <= 8):
        raise ValueError("num_bits must be between 1 and 8.")
    
    # Calculate the number of levels
    num_levels = 2 ** num_bits
    
    # Normalize the image to the range [0, num_levels - 1]
    quantized = (image / 255.0) * (num_levels - 1)
    
    # Round to nearest integer and convert back to integers
    quantized = np.round(quantized).astype(np.uint8)
    
    # Scale back to the full grayscale range [0, 255]
    quantized = (quantized * (255 // (num_levels - 1))).astype(np.uint8)
    
    return quantized


image = cv2.imread("0001.png")
image = cv2.resize(image, (194, 194))
image = cv2.GaussianBlur(image, 2)
image = quantize_grayscale(image, 4)
data = image.tobytes()
frame_size = len(data)
compressed_size = len(zstd.compress(data, 5))
est_fps = 225/(compressed_size / 1000)
print(frame_size)
print(compressed_size)
print(est_fps)

cv2.imshow("yeah", image)
cv2.waitKey(0)