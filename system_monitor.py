from gpiozero import CPUTemperature
import os
import time
import psutil

class SystemMonitor:
	def __init__(self):
		self.CPUload = 0
		self.CPUtemp = 0
		self.storageFree = 0
		self.storageTotal = 0

	def getCPUload(self):
		return(int(psutil.cpu_percent()))

	def getCPUtemp(self):
		return(str(round(CPUTemperature().temperature)))

	def getStorageFree(self):
		statvfs = os.statvfs("/")
		return(round((statvfs.f_frsize * statvfs.f_bavail)/1000000000),1)

	def getStorageTotal(self):
		statvfs = os.statvfs("/")
		return(round((statvfs.f_frsize * statvfs.f_blocks)/1000000000),1)


def sysmonitor():
	mon = SystemMonitor()
	while True:
		print(mon.getCPUload())
		print(mon.getCPUtemp())
		print(mon.getStorageFree())
		print(mon.getStorageTotal())
		time.sleep(0.5)
