import onnxruntime as ort
from openvino.inference_engine import IECore
import openvino.inference_engine as ovie
'''
print(ort.get_device()) # Returns the current device
print(ort.get_all_providers())
print(ort.get_available_providers())
#sess = ort.InferenceSession(f'{self.model}onnx/model.onnx', self.opts, providers=['DmlExecutionProvider'])
'''
ie = IECore()
ovie.list_devices
#print(ie.get_devices())
#net = ie.read_network(model=f'{self.model}openvino/model.xml', weights=f'{self.model}openvino/model.bin')
#self.sess = ie.load_network(network=net, device_name='CPU')