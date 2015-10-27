#!/usr/bin/python
# coding=utf-8
"""
simulation 
@author: Peng Cheng
		 Hongliang Shen
		 Xi Zhang 
@date: 2015/9/6    21:19    v0.2: the original version.
	   2015/9/10   21:40    v0.3: use a child thread to read datas for better instantaneity.
		
"""
from droneapi.lib import VehicleMode, Location
from pymavlink import mavutil
import time
import serial
import threading
import math

from leaderControl1 import leaderControl1

# function: record currrent time(s)
current_milli_time = lambda: int(time.time() * 1000)

# First get an instance of the API endpoint
api = local_connect()
# Get the connected vehicle (currently only one vehicle can be returned).
vehicle = api.get_vehicles()[0]

# function: takeoff to the target height
def arm_and_takeoff(aTargetAltitude):
	print "Basic pre-arm checks"
	if vehicle.mode.name == "INITIALISING":
		print "Waiting for vehicle to initialise"
		time.sleep(1)
	while vehicle.gps_0.fix_type < 2:
		print "Waiting for GPS........", vehicle.gps_0.fix_type
		time.sleep(1)

	print "Arming motors"

	vehicle.mode = VehicleMode("GUIDED")
	vehicle.armed = True
	vehicle.flush()

	while not vehicle.armed and not api.exit:
		print "Waiting for arming..."
		time.sleep(1)

	print "Take off!"
	vehicle.commands.takeoff(aTargetAltitude)
	vehicle.flush()

	#Wait until the vehicle reaches a safe height
	while not api.exit:
		print "Altitude: ", vehicle.location.alt
		if vehicle.location.alt >= aTargetAltitude*0.95:
			print "Reached target altitude"
			break;
		time.sleep(1)

# function: controlling vehicle movement using velocity
def send_ned_velocity(velocity_x, velocity_y, velocity_z):
    """
    Move vehicle in direction based on specified velocity vectors.
    """
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
        0b0000111111000111, # type_mask (only speeds enabled)
        0, 0, 0, # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z, # x, y, z velocity in m/s
        0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)
    # send command to vehicle
    vehicle.send_mavlink(msg)
    vehicle.flush()


def send_global_velocity(velocity_x, velocity_y, velocity_z):
    """
    Move vehicle in direction based on specified velocity vectors.
    """
    msg = vehicle.message_factory.set_position_target_global_int_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT, # frame
        0b0000111111000111, # type_mask (only speeds enabled)
        0, # lat_int - X Position in WGS84 frame in 1e7 * meters
        0, # lon_int - Y Position in WGS84 frame in 1e7 * meters
        0, # alt - Altitude in meters in AMSL altitude(not WGS84 if absolute or relative)
                   # altitude above terrain if GLOBAL_TERRAIN_ALT_INT
        velocity_x, # X velocity in NED frame in m/s
                velocity_y, # Y velocity in NED frame in m/s
                velocity_z, # Z velocity in NED frame in m/s
        0, 0, 0, # afx, afy, afz acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)
    # send command to vehicle
    vehicle.send_mavlink(msg)
    vehicle.flush()

'''initialise datas'''
delt_T = 1000  #500ms
lastRecord = current_milli_time()
CONST_VX0 = 0.0
CONST_VY0 = 0.0
CONST_D12 = 3.0   #m
loop_cnt = 1
R = 6371000    #meters

arm_and_takeoff(3.5)
#leader object 
leader = leaderControl1(CONST_VX0, CONST_VY0, CONST_D12, vehicle.location.lat, vehicle.location.lon)

'''control loop'''
while not api.exit:
    if current_milli_time() - lastRecord >= delt_T:  #500ms
        lastRecord = current_milli_time()
        print "[%s] current time is: %f" % (loop_cnt, lastRecord)
        loop_cnt += 1

        # read
        neighbourLon = 149.165053 * float(math.pi / 180) * R
        neighbourLat = -35.362081 * float(math.pi / 180) * R

        # control
        leader.x = vehicle.location.lat * float(math.pi / 180) * R
        leader.y = vehicle.location.lon * float(math.pi / 180) * R
        leader.controller(leader.x, neighbourLat, leader.y, neighbourLon)

        print "vx: %f, vy: %f" % (leader.vx, leader.vy)
	'''
        if leader.vx >= 10: #speed protection
            leader.vx = 10
        elif leader.vx <= -10:
            leader.vx = -10
        if leader.vy >= 10:
            leader.vy = 10
        elif leader.vy <= -10:
            leader.vy = -10
	'''
        send_ned_velocity(leader.vx, leader.vy, 0)  #vz = 0.0

'''finished and landing'''
vehicle.mode = VehicleMode("LAND") 
