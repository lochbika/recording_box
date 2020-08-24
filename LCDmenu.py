class LCDmenu:
	def __init__(self,AllItems):
		self.AllItems = AllItems
		self.CurrentItem = None
		self.CurrentLevel = 0
		self.CurrentLevelItemList = []
		self.MaxDepth = 0


	def getLevelItemList(self):
		keys = list(self.AllItems)
		self.CurrentLevelItemList = []
		for i in keys:
			i_nodots = i.replace(".","")
			if len(i_nodots) is self.CurrentLevel + 1:
				self.CurrentLevelItemList.append(self.AllItems[i])
		return(self.CurrentLevelItemList)


	def enterMenu():
		CurrentItem = "0"
		CurrentLevel = 0
#		CurrentLevelItemList = 
