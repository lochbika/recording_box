class LCDmenu:
	def __init__(self,AllItems):
		self.AllItems = AllItems
		self.CurrentItem = "0"
		self.CurrentLevel = len(self.CurrentItem.replace(".","")) - 1
		self.CurrentLevelItemList = []
		self.MaxDepth = 0

	def levelCurrent(self):
		self.CurrentLevel = len(self.CurrentItem.replace(".","")) - 1

	def getLevelItemList(self):
		keys = list(self.AllItems)
		self.CurrentLevelItemList = []
		for i in keys:
			i_nodots = i.replace(".","")
			if len(i_nodots) is self.CurrentLevel + 1:
				if i.startswith(self.CurrentItem[:-1]) and self.CurrentLevel > 0:
					self.CurrentLevelItemList.append(self.AllItems[i])
				elif self.CurrentLevel == 0:
					self.CurrentLevelItemList.append(self.AllItems[i])
		return(self.CurrentLevelItemList)

	def levelDescent(self):
		if self.AllItems.get(self.CurrentItem + ".0") != None:
			self.CurrentItem = self.CurrentItem + ".0"
			self.CurrentLevel = self.CurrentLevel + 1

	def levelAscent(self):
		if len(self.CurrentItem) > 1:
			self.CurrentItem = self.CurrentItem[:-2]
			self.CurrentLevel = self.CurrentLevel - 1

	def getNextItem(self):
		ndig = len(self.CurrentItem.split(".")[-1]) * -1
		newitem = self.CurrentItem[:ndig] + str(int(self.CurrentItem[ndig:]) + 1)
		if self.AllItems.get(newitem) != None:
			return(newitem)
		else:
			return(self.CurrentItem[:ndig] + "0")

	def getPrevItem(self):
		ndig = len(self.CurrentItem.split(".")[-1]) * -1
		newitem = self.CurrentItem[:ndig] + str(int(self.CurrentItem[ndig:]) - 1)
		if self.AllItems.get(newitem) != None:
			return(newitem)
		else:
			return(self.CurrentItem[:ndig] + str(len(self.getLevelItemList()) - 1))

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

