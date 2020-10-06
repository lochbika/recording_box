class LCDmenu:
	def __init__(self,AllItems):
		self.AllItems = AllItems
		self.CurrentItem = "0"
		self.CurrentLevel = len(self.CurrentItem.replace(".","")) - 1
		self.CurrentLevelItemList = []
		self.MaxDepth = 0

	def levelCurrent(self):
		self.CurrentLevel = len(self.CurrentItem.split(".")) - 1

	def getLevelItemList(self):
		keys = list(self.AllItems)
		self.CurrentLevelItemList = []
		levelBase = ".".join(self.CurrentItem.split(".")[:-1])
		for i in keys:
			i_list = i.split(".")
			if len(i_list) is self.CurrentLevel + 1:
				if ".".join(i_list[:-1]) == levelBase:
					self.CurrentLevelItemList.append(self.AllItems[i])
		return(self.CurrentLevelItemList)

	def levelDescent(self):
		if self.AllItems.get(self.CurrentItem + ".0") != None:
			self.CurrentItem = self.CurrentItem + ".0"
			self.CurrentLevel = self.CurrentLevel + 1

	def levelAscent(self):
		if len(self.CurrentItem.split(".")) > 1:
			self.CurrentItem = ".".join(self.CurrentItem.split(".")[:-1])
			self.CurrentLevel = self.CurrentLevel - 1

	def getNextItem(self):
		levelBase = ".".join(self.CurrentItem.split(".")[:-1])
		curitem = self.CurrentItem.split(".")[-1]
		if self.CurrentLevel > 0:
			newitem = levelBase + "." + str(int(curitem) + 1)
		else:
			newitem = str(int(curitem) + 1)
		if self.AllItems.get(newitem) != None:
			return(newitem)
		else:
			if self.CurrentLevel > 0:
				return(levelBase + ".0")
			else:
				return("0")

	def getPrevItem(self):
		levelBase = ".".join(self.CurrentItem.split(".")[:-1])
		curitem = self.CurrentItem.split(".")[-1]
		if self.CurrentLevel > 0:
			newitem = levelBase + "." + str(int(curitem) - 1)
		else:
			newitem = str(int(curitem) - 1)
		if self.AllItems.get(newitem) != None:
			return(newitem)
		else:
			if self.CurrentLevel > 0:
				return(levelBase + "." +  str(len(self.getLevelItemList()) -1 ))
			else:
				return(str(len(self.getLevelItemList()) - 1))

	def setNextItem(self):
		newitem = self.getNextItem()
		self.CurrentItem = newitem

	def setPrevItem(self):
		newitem = self.getPrevItem()
		self.CurrentItem = newitem

	def delLevelItemList(self,leveldescriptor):
		keys = list(self.AllItems)
		for i in keys:
			if i.startswith(leveldescriptor):
				self.AllItems.pop(i)

	def replaceLevelItemList(self,leveldescriptor,newlist):
		self.delLevelItemList(leveldescriptor)
		for i in range(0,len(newlist)):
			self.AllItems[leveldescriptor + str(i)] = newlist[i]

	def currentItemIsAction(self):
		if self.AllItems.get(self.CurrentItem + ".0") == None:
			return(True)
		else:
			return(False)

