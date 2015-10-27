#!/usr/bin/python
"""
Adaptive control algorithm class for leaders, to keep two leaders matianing a constant distance 
@author: Peng Cheng
@date: 2015/9/3 18:52 
		
"""
import time
import numpy as np
#import matplotlib.pyplot as plt

current_milli_time = lambda: int(time.time() * 1000)

R = 6371000    #meters

def haversine_distance(pos1, pos2):
	lon1 = float(pos1['lon'])
	lat1 = float(pos1['lat'])

	lon2 = float(pos2['lon'])
	lat2 = float(pos2['lat'])

	theta1 = lat1 * float(math.pi / 180) 
	theta2 = lat2 * float(math.pi / 180)
	delta_theta = (lat2 - lat1) * float(math.pi / 180)
	delta_lamda = (lon2 - lon1) * float(math.pi / 180)

	a = pow(math.sin(delta_theta/2), 2) + math.cos(theta1) * math.cos(theta2) * pow(math.sin(delta_lamda/2), 2)

	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

	d = R * c

	return d

class leaderControl1(object):

	def __init__(self, vx0, vy0, initial_d12, initial_x, initial_y):
		self.vx0 = vx0
		self.vy0 = vy0
		self.vx = 0.0
		self.vy = 0.0
		self.x = initial_x
		self.y = initial_y
		self.d12 = initial_d12  

	# @param: x1-the x position of the object itself
	#         x2-the x position of another leader
	#         y1-the y position of the object itself
	#         y2-the y position of another leader
	def controller(self, x1, x2, y1, y2):
		currentDisPow = pow(x1-x2, 2) + pow(y1-y2, 2)		
		print currentDisPow
		pos1 = {'lon': y1, 'lat': x1}
		pos2 = {'lon': y2, 'lat': x2}
		#currentDisPow = pow(haversine_distance(pos1,pos2),2)
		self.vx = self.vx0 + (x2 - x1) * (currentDisPow - pow(self.d12, 2)) * 0.0001  #0.02 is arbitrary scale factor
		self.vy = self.vy0 + (y2 - y1) * (currentDisPow - pow(self.d12, 2)) * 0.0001

	# It's better to output control in main function
	'''
	def run(self, vx, vy):
		send_ned_velocity(vx, vy, 0)  # vz = 0.0
	'''
'''
if __name__ == "__main__":
	leader1 = leaderControl(0.0, 0.0, 2.0, 0.0, 8.0)
	leader2 = leaderControl(0.0, 0.0, 2.0, 10.0, 0.0)
	delt_T = 0.5  #s
	lastRecord = current_milli_time()
	cnt = 0
	leader1X=[]
	leader1Y=[]
	leader2X=[]
	leader2Y=[]
	while cnt<50:
		if current_milli_time() - lastRecord >= 500:  #ms
			print "[%d] current time is: " % cnt + str(current_milli_time())
			lastRecord = current_milli_time()
			leader1.controller(leader1.x, leader2.x, leader1.y, leader2.y)
			leader2.controller(leader2.x, leader1.x, leader2.y, leader1.y)

			leader1.x += leader1.vx * delt_T
			leader1.y += leader1.vy * delt_T
			leader2.x += leader2.vx * delt_T
			leader2.y += leader2.vy * delt_T

			cnt += 1
			leader1X.append(leader1.x)
			leader1Y.append(leader1.y)
			leader2X.append(leader2.x)
			leader2Y.append(leader2.y)
			print "x1:" + str(leader1.x)
			print "y1:" + str(leader1.y)
			print "x2:" + str(leader2.x)
			print "y2:" + str(leader2.y)
		else:
			pass
		
	plt.figure(1)
	plt.plot(leader1X,leader1Y)
	plt.plot(leader2X,leader2Y)
	plt.show()
'''