#!/usr/bin/python
# coding=utf-8
'''
@file: position_pid.py
@brief: To control the quadrotor to a given position(not far away!) using pid control method.
@author: Peng Cheng
@date: 2015/10/26  cpeng@zju.edu.cn

'''
from droneapi.lib import VehicleMode, Location
from pymavlink import mavutil
import time
import math

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
# Set up velocity mappings
# velocity_x > 0 => fly North
# velocity_x < 0 => fly South
# velocity_y > 0 => fly East
# velocity_y < 0 => fly West
# velocity_z < 0 => ascend
# velocity_z > 0 => descend
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

# Get Vehicle Home location ((0 index in Vehicle.commands)
print "Get home location" 
cmds = vehicle.commands
cmds.download()
cmds.wait_valid()
print " Home WP: %s" % cmds[0]

# open or create a file
read = file('/home/odroid/multiDrone_Com/test_modules/position_datalog','a+')

R = 6371000    #meters

'''
@function: to_target_position
@param: target_pos: {'lon': , 'lat': }
@note:  frame:
		x/lat
		|
		|
		|_ _ _ _ y/lon
'''
#def to_target_position(max_v, theta, target_pos):
def to_target_position(target_pos):
	px = 0.1;
	py = 0.1;
	delta_x = R * (target_pos['lat'] - vehicle.location.lat) * float(math.pi / 180)
	delta_y = R * (target_pos['lon'] - vehicle.location.lon) * float(math.pi / 180)
	vx = px * delta_x
	vy = py * delta_y
	
	if vx >= 1:
		vx = 1
	elif vx <= -1:
		vx = -1
	if vy >= 1:
		vy = 1
	elif vy <= -1:
		vy = -1

	send_ned_velocity(vx, vy, 0)

	return vx, vy

'''initialise datas'''
delt_T = 100
lastRecord = current_milli_time()
positionList = [255.0, 255.0]
loop_cnt = 1

home_location = {'lat': cmds[0].x, 'lon': cmds[0].y}
#target_pos = {'lat': home_location['lat']+0.00004, 'lon':home_location['lon']+0.00004}

target_pos = {'lat': 30.2656902, 'lon':120.1195215}


arm_and_takeoff(3.0)

'''control loop'''
while not api.exit:
	if current_milli_time() - lastRecord >= delt_T:
		lastRecord = current_milli_time()
		print "[%s] current time is: %f" % (loop_cnt, lastRecord)
		loop_cnt += 1

		vx_control, vy_control = to_target_position(target_pos)
		print "vx: %f; vy: %f" % (vx_control, vy_control)

		realV = vehicle.velocity  #[vx, vy, vz]
		read.write(str(current_milli_time())+' '+str(realV[0])+' '+str(realV[1])+' '+str(vx_control)+' '+str(vy_control)+' ')
		read.write(str(vehicle.location.lat)+' '+str(vehicle.location.lon)+'\n')

'''finished and landing'''
vehicle.mode = VehicleMode("LAND") 
read.close	
