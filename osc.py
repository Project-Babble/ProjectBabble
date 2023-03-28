from pythonosc import udp_client

class OSC:
    global client #todo, make this more proper
    client = udp_client.SimpleUDPClient("127.0.0.1", 9000) 

    def set_osc(OSCip, OSCport):
        global client
        client = udp_client.SimpleUDPClient(str(OSCip), int(OSCport))

    def send_osc(array, multi, location):
                global client
                client.send_message(location + "/cheekPuff", array[0] * multi)
                client.send_message(location + "/cheekSquintLeft", array[1] * multi)
                client.send_message(location + "/cheekSquintRight", array[2] * multi)
                client.send_message(location + "/noseSneerLeft", array[3] * multi)
                client.send_message(location + "/noseSneerRight", array[4] * multi)
                client.send_message(location + "/jawOpen", array[5] * multi)
                client.send_message(location + "/jawForward", array[6] * multi)
                client.send_message(location + "/jawLeft", array[7] * multi)
                client.send_message(location + "/jawRight", array[8] * multi)
                client.send_message(location + "/mouthFunnel", array[9] * multi)
                client.send_message(location + "/mouthPucker", array[10] * multi)
                client.send_message(location + "/mouthLeft", array[11] * multi)
                client.send_message(location + "/mouthRight", array[12] * multi)
                client.send_message(location + "/mouthRollUpper", array[13] * multi)
                client.send_message(location + "/mouthRollLower", array[14] * multi)
                client.send_message(location + "/mouthShrugUpper", array[15] * multi)
                client.send_message(location + "/mouthShrugLower", array[16] * multi)
                client.send_message(location + "/mouthClose", array[17] * multi)
                client.send_message(location + "/mouthSmileLeft", array[18] * multi)
                client.send_message(location + "/mouthSmileRight", array[19] * multi)
                client.send_message(location + "/mouthFrownLeft", array[20] * multi)
                client.send_message(location + "/mouthFrownRight", array[21] * multi)
                client.send_message(location + "/mouthDimpleLeft", array[22] * multi)
                client.send_message(location + "/mouthDimpleRight", array[23] * multi)
                client.send_message(location + "/mouthUpperUpLeft", array[24] * multi)
                client.send_message(location + "/mouthUpperUpRight", array[25] * multi)
                client.send_message(location + "/mouthLowerDownLeft", array[26] * multi)
                client.send_message(location + "/mouthLowerDownRight", array[27] * multi)
                client.send_message(location + "/mouthPressLeft", array[28] * multi)
                client.send_message(location + "/mouthPressRight", array[29] * multi)
                client.send_message(location + "/mouthStretchLeft", array[30] * multi)
                client.send_message(location + "/mouthStretchRight", array[31] * multi)
                client.send_message(location + "/tongueOut", array[32] * multi)