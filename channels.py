class Channel:
	def __init__(self, name):
		self.name = name
		self.messages = []

	def newMessage(self,message, sender, channel, time):
		new = {"message": message, "sender": sender, "channel": channel, "time": time}
		self.messages.append(new)
		while len(self.messages) > 100:
			del(self.messages[0])
