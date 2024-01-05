import numpy as np

def normalize(numpy_array):
    """
    Normalize the values of a numpy array to a specified range.

    Args:
    - numpy_array (numpy.ndarray): Input numpy array.
    
    Returns:
    - numpy.ndarray: Normalized numpy array.
    """
    normalized_array = numpy_array / 255

    return normalized_array


def to_tensor(numpy_array, dtype=np.float32):
    """
    Convert a numpy array to a PyTorch tensor.

    Args:
    - numpy_array (numpy.ndarray): Input numpy array.
    - dtype (numpy.dtype): Data type of the resulting PyTorch tensor.

    Returns:
    - torch.Tensor: Converted PyTorch tensor.
    """
    if not isinstance(numpy_array, np.ndarray):
        raise ValueError("Input must be a numpy array")

    # Ensure the input array has the correct data type
    numpy_array = numpy_array.astype(dtype)

    # Add a batch dimension if the input array is 2D
    if len(numpy_array.shape) == 2:
        numpy_array = numpy_array[:, :, np.newaxis]

    # Transpose the array to match PyTorch tensor format (C x H x W)
    tensor = normalize(np.transpose(numpy_array, (2, 0, 1)))

    return tensor

def unsqueeze(numpy_array, axis: int):
    """
    Add a dimension of size 1 to a numpy array at the specified position.

    Args:
    - numpy_array (numpy.ndarray): Input numpy array.
    - axis (int): Position along which to add the new dimension.

    Returns:
    - numpy.ndarray: Numpy array with an additional dimension.
    """
    if not isinstance(numpy_array, np.ndarray):
        raise ValueError("Input must be a numpy array")

    result_array = np.expand_dims(numpy_array, axis=axis)

    return result_array