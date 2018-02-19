import RPi.GPIO as GPIO
import time

TIMEOUT = 2

ERROR_TIMEOUT = -1
ERROR_DATA_LOW = -2
ERROR_DATA_READ = -3
ERROR_DATA_EOF = -4
ERROR_DATA_LENGTH = -5
ERROR_DATA_PARITY = -6
ERROR_DATA_VALUE = -7

class DHT22:

	def usleep(self, t):
		tt = time.time() + (t / 1000000)
		while time.time() < tt:
			pass

	def confirm(self, us, level):
		cnt = int(us / 10)
		if us % 10 > 0:
			cnt = cnt + 1

		for i in range(0, cnt):
			self.usleep(10)

			l = GPIO.input(self.pin)
			if l != level:
				return True

		return False

	def bits2byte(self, data, offset):
		result = 0
		b = 128

		for i in range(0, 8):
			result += data[offset + i] * b
			b >>= 1

		return result

	def acquire(self):

		t_start = time.time()

		while True:
			# init transmission
			GPIO.setup(self.pin, GPIO.OUT)
			GPIO.output(self.pin, GPIO.LOW)
			self.usleep(1000)
			GPIO.output(self.pin, GPIO.HIGH)
			GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

			if self.confirm(85, GPIO.LOW):
				if self.confirm(85, GPIO.HIGH):
					break

			if time.time() - t_start > TIMEOUT:
				return ERROR_TIMEOUT

		# read transmission
		data = []

		for i in range(0, 40):

			if not self.confirm(90, GPIO.LOW):
				return ERROR_DATA_LOW

			ok = False

			for j in range(0, 8):

				if GPIO.input(self.pin) != GPIO.HIGH:
					ok = True
					break

				self.usleep(6)

			if not ok:
				return ERROR_DATA_READ

			if j > 3:
				data.append(1)
			else:
				data.append(0)

		if not self.confirm(75, GPIO.LOW):
			return ERROR_DATA_EOF

		# decode
		if len(data) != 40:
			return ERROR_DATA_LENGTH

		hh = self.bits2byte(data, 0)
		hl = self.bits2byte(data, 8)
		th = self.bits2byte(data, 16)
		tl = self.bits2byte(data, 24)

		p = self.bits2byte(data, 32)

		s = (hh + hl + th + tl) & 255
		if p != s:
			return ERROR_DATA_PARITY

		h = (hh << 8) | hl
		t = (th << 8) | tl

		if h == 0 and t == 0:
			return ERROR_DATA_VALUE

		return [h / 10, t / 10]

	def begin(self, pin):

		self.pin = pin

		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
