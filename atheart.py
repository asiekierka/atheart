import bluetooth
from enum import IntEnum
import time

class MicrophoneMode(IntEnum):
	OFF = 0
	HEARTHROUGH = 1
	NOISE_REDUCTION = 2

class MicrophoneLevel(IntEnum):
	OFF = 0
	LOW = 1
	MEDIUM = 2
	HIGH = 3

class Headphones:
	def __init__(self, mac, uuid="00001101-0000-1000-8000-00805f9b34fb"):
		self.uuid = uuid
		self.mac = mac
		self.service = bluetooth.find_service(uuid=uuid, address=mac)
		if len(self.service) < 1:
			raise Exception("Could not find Bluetooth service!")
		self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

	def connect(self):
		self.sock.connect((self.service[0]['host'], self.service[0]['port']))

	def close(self):
		self.sock.close()

	def __build_header(self, flags, subchannel_id):
		# TODO: These are all guesses!
		return [0xFF, 0x01, 0x00, flags, 0x00, 0x0A, subchannel_id]

	def __build_header_0x08(self, flags, command):
		return self.__build_header(flags, 0x08) + [0x00, 0x00, command]

	def get_microphone_mode(self):
		packet = self.__build_header_0x08(0x04, 0x1C)
		self.sock.send(bytes(packet))
		result = list(self.sock.recv(1024))
		if len(result) != 13:
			raise Exception('Could not receive microphone mode!')
		return {
			'mode': MicrophoneMode(result[11]),
			'level': MicrophoneLevel(result[12])
		}

	def set_microphone_mode(self, mode, level=None):
		if mode == MicrophoneMode.OFF:
			level = MicrophoneLevel.OFF
		elif mode == MicrophoneMode.HEARTHROUGH:
			if level is None:
				level = MicrophoneLevel.MEDIUM
		elif mode == MicrophoneMode.NOISE_REDUCTION:
			if (level != MicrophoneLevel.OFF) and (level != MicrophoneLevel.LOW):
				level = MicrophoneLevel.LOW
		packet = self.__build_header_0x08(0x04, 0x1D) + [int(mode), int(level)]
		self.sock.send(bytes(packet))


	def get_battery_level(self):
		packet = self.__build_header(0x00, 0x03) + [0x02]
		self.sock.send(bytes(packet))
		result = list(self.sock.recv(1024))
		if len(result) != 11:
			raise Exception('Could not receive microphone mode!')
		raw_level = (result[9] * 256) + result[10]
		return {
			'adjusted': raw_level / 8192.0, # TODO - probably inaccurate
			'raw': raw_level
		}

	def set_voice_prompt(self, enabled):
		packet = self.__build_header(0x01, 0x02) + [0x0A, 1 if enabled else 0]
		self.sock.send(bytes(packet))

# TODO
headphones = Headphones(mac)
try:
	headphones.connect()
	print(headphones.get_battery_level()['adjusted'])
finally:
	headphones.close()
