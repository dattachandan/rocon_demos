#!/usr/bin/env python
# -*- coding:utf-8 -*-


import rospy
import smach
import smach_ros
import time

import commandset

#
from order_msgs.msg import Order
from std_msgs.msg import Int32


#client program
########################################################
#todo
########################################################
#Recv

def Recv(data):
	print data.user_id, data.table_id, data.robot_id, data.status

	if data._connection_header['topic'] == '/new_order_sub':
		cmdset = commandset.CCmdSet('NewOrderEvent','EVENT_MESSAGE','user_device', 'taskcoordinator')	
		cmdset.setInt('UserID',data.user_id)
		cmdset.setInt('TableID',data.table_id)	
		cmdset.setInt('RobotID',data.robot_id)	
		cmdset.setString('Status',data.status)	

		print "Call Recv Function- cmdset.m_cmdname: [%s]"%cmdset.m_cmdname

	
	elif data._connection_header['topic'] == '/food_preparation_order_sub': 
		
		cmdset = commandset.CCmdSet('FoodPreParationCompleteEvent','EVENT_MESSAGE','kitchen_manager', 'taskcoordinator')	
		cmdset.setInt('UserID',data.user_id)
		cmdset.setInt('TableID',data.table_id)	
		cmdset.setInt('RobotID',data.robot_id)	
		cmdset.setString('Status',data.status)	

		print "Call Recv Function- cmdset.m_cmdname: [%s]"%cmdset.m_cmdname	
		
	EventProc(cmdset)
	
	pass

#Event proc
def EventProc(cmdset):
	##OrderManagingSrv
	if OrderManagingSrv_EvtList.keys().count(cmdset.m_cmdname):
		callSrvCVFlag = False
		
		if cmdset.m_cmdname == 'NewOrderEvent' and cmdset.getValue('Status') == "Idle":
			callSrvCVFlag = True
		else:
			pass
		
		if callSrvCVFlag:		
			print "Call CallbackFunc ",cmdset.m_cmdname
			for i in range(len(OrderManagingSrv_CBList)):
				OrderManagingSrv_CBList[i](cmdset)
	
		##OrderManagingSrv
	if FoodPreparationSrv_EvtList.keys().count(cmdset.m_cmdname):
		callSrvCVFlag = False
		#cmdset.printCmdSet()

		if cmdset.m_cmdname == 'FoodPreParationOrderEvent' and cmdset.getValue('Status') == "Idle":
			callSrvCVFlag = True 
		elif cmdset.m_cmdname == 'FoodPreParationCompleteEvent' and cmdset.getValue('Status') == "PreparationComplete":
			callSrvCVFlag = True
		else:
			pass
		
		if callSrvCVFlag:		
			print "Call CallbackFunc ",cmdset.m_cmdname
			for i in range(len(FoodPreparationSrv_CBList)):
				FoodPreparationSrv_CBList[i](cmdset)
	pass

#RegEventProc
def RegEventProc(SrvName, cb):
	if SrvName.count('OrderManagingSrv'): 
		OrderManagingSrv_CBList.append(cb)
		
	elif SrvName.count('FoodPreparationSrv'): 
		FoodPreparationSrv_CBList.append(cb)
	else:
		pass

#######################################################################################################
##Define Service
#######################################################################################################
##OrderManagingSrv ############################################################

OrderManagingSrv_CBList = []
OrderManagingSrv_EvtList = {'NewOrderEvent':'GlobalEvent'}

global OrderManagingSrv_GlobalEvtFlag; OrderManagingSrv_GlobalEvtFlag = False
global OrderManagingSrv_cmdset; OrderManagingSrv_cmdset = commandset.CCmdSet()

class OrderManagingSrv_Init(smach.State):
	def __init__(self):
		smach.State.__init__(self, outcomes=['success','retry','failure'])
	
	def execute(self, userdata):
		time.sleep(1)
		return 'success'

	
class OrderManagingSrv_Idle(smach.State):
	m_cmdsetList =[]
	
	def __init__(self):
		smach.State.__init__(self, outcomes = ['pushorder', 'retry','failure'])
		RegEventProc(self.__class__.__name__, self.listener)
		
	def listener(self,cmdset):
		global OrderManagingSrv_GlobalEvtFlag
		if cmdset.m_cmdname ==  'NewOrderEvent' and cmdset.getValue('Status') == "Idle":
			self.m_cmdsetList.append(cmdset) 	
		pass
	
	def execute(self, userdata):
		while True:
			while len(self.m_cmdsetList) == 0:
					time.sleep(0.001)		
					pass
			cmdset = self.m_cmdsetList.pop(0)
			
			if cmdset.m_cmdname == 'NewOrderEvent' and cmdset.getValue('Status') == "Idle":
				global OrderManagingSrv_cmdset
				OrderManagingSrv_cmdset = cmdset				
				return 'pushorder'

		
class OrderManagingSrv_PushOrder(smach.State):
	m_IsRunning = [True]
	
	def __init__(self):
		smach.State.__init__(self, outcomes = ['success','retry','failure'])
		RegEventProc(self.__class__.__name__, self.listener)
	
	def listener(self,cmdset):
		if cmdset.m_cmdname ==  'NewOrderEvent' and cmdset.getValue('Status') == "Idle":
			OrderManagingSrv_GlobalEvtFlag = True	
		pass
		
	def execute(self,userdata):
		#print "OrderManagingSrv_PushOrder Start"

		"""
		global OrderManagingSrv_GlobalEvtFlag	
		ResultCode = 'retry'

		if OrderManagingSrv_GlobalEvtFlag == True:			
			OrderManagingSrv_GlobalEvtFlag = False
			OrderManagingSrv = 'failure'
			return ResultCode
		"""
		#execute userevent
		global OrderManagingSrv_cmdset	
		cmdset = OrderManagingSrv_cmdset
		cmdset.setCmdName('FoodPreParationOrderEvent')
		cmdset.setSenderID('OrderManagingSrv')
		cmdset.setReceiverID('FoodPreparationSrv')
		
		#cmdset.printCmdSet()
		EventProc(cmdset)
		
		return 'success'
		
		
		#send event
		
		##Action
		#self.m_IsRunning =[True]	
		#Ret = {}
		#Thread_GotoDirEx = threading.Thread(target=GotoDirEx, args=(self.m_IsRunning,Ret, 1, 65535, True))
		#Thread_GotoDirEx.start()		
		#while self.m_IsRunning[0] == True:
		#	if RemoteSrv_GlobalEvtFlag == True:				
		#		RemoteSrv_GlobalEvtFlag = False
		#		ResultCode =  'failure'
		#		return ResultCode
		#	pass		
		#while Thread_GotoDirEx.isAlive():
		#	pass
		#
		#if Ret['ResultCode'] == 0:
		#	ResultCode = 'success'
		#else:
		#	ResultCode = 'failure'
		
		
		
		


##FoodPreparationSrv ############################################################

FoodPreparationSrv_CBList = []
FoodPreparationSrv_EvtList = {'FoodPreParationOrderEvent':'GlobalEvent', 'FoodPreParationCompleteEvent':'GlobalEvent'}
FoodPreparationSrv_GlobalEvtFlag = False

global FoodPreparationSrv_cmdset; FoodPreparationSrv_cmdset = commandset.CCmdSet()
global FoodPreparationSrv_waitingPreparationFlag; FoodPreparationSrv_waitingPreparationFlag = False
global FoodPreparationSrv_userID; FoodPreparationSrv_UserID = 0
class FoodPreparationSrv_Init(smach.State):
	def __init__(self):
		smach.State.__init__(self, outcomes=['success','retry','failure'])
	
	def execute(self, userdata):
		time.sleep(1)
		return 'success'

	
class FoodPreparationSrv_Idle(smach.State):
	m_cmdsetList =[]
	
	def __init__(self):
		smach.State.__init__(self, outcomes = ['checkKitchenMgr', 'retry','failure'])
		RegEventProc(self.__class__.__name__, self.listener)
		
	def listener(self,cmdset):
		
		if cmdset.m_cmdname == 'FoodPreParationOrderEvent' and cmdset.getValue('Status') == "Idle":
			self.m_cmdsetList.append(cmdset) 
			print "FoodPreparationSrv Push order: ",len(self.m_cmdsetList),cmdset.getValue('UserID')
			#cmdset.printCmdSet()
			for k in range(len(self.m_cmdsetList)):
				print k,":", self.m_cmdsetList[k]
			
		pass
		
	def execute(self, userdata):
		while True:
			while len(self.m_cmdsetList) == 0:
					time.sleep(0.001)		
					pass
			
			for k in range(len(self.m_cmdsetList)):
				print k,":", self.m_cmdsetList[k]
				
			cmdset = self.m_cmdsetList.pop(0)

			print cmdset
			print "FoodPreparationSrv Pop order: ",len(self.m_cmdsetList), cmdset.m_cmdname ,cmdset.getValue('UserID')
			#cmdset.printCmdSet()
			

			if cmdset.m_cmdname == 'FoodPreParationOrderEvent' and cmdset.getValue('Status') == "Idle":
				global FoodPreparationSrv_cmdset
				FoodPreparationSrv_cmdset = cmdset				
				return 'checkKitchenMgr'
				
				
class FoodPreparationSrv_CheckKitchenManager(smach.State):
	m_IsRunning = [True]
	
	def __init__(self):
		smach.State.__init__(self, outcomes = ['pushorder', 'retry','failure'])
		RegEventProc(self.__class__.__name__, self.listener)
		
	def listener(self,cmdset):
		global FoodPreparationSrv_GlobalEvtFlag
		if cmdset.m_cmdname ==  'FoodPreParationOrderEvent' and cmdset.getValue('Status') == "Idle":
			FoodPreparationSrv_GlobalEvtFlag = True	
		
	

	def execute(self, userdata):
		
		"""
		global FoodPreparationSrv_GlobalEvtFlag	
		ResultCode = 'retry'

		if FoodPreparationSrv_GlobalEvtFlag == True:			
			FoodPreparationSrv_GlobalEvtFlag = False
			FoodPreparationSrv = 'failure'
			return ResultCode			
		"""
		
		global FoodPreparationSrv_waitingPreparationFlag;
		while FoodPreparationSrv_waitingPreparationFlag:
				time.sleep(0.001)		
				pass	
		return 'pushorder'	


class FoodPreparationSrv_PushOrder(smach.State):
	m_IsRunning = [True]
	
	def __init__(self):
		smach.State.__init__(self, outcomes = ['success','retry','failure'])
		RegEventProc(self.__class__.__name__, self.listener)
	
	def listener(self,cmdset):
		global FoodPreparationSrv_GlobalEvtFlag
		
		if cmdset.m_cmdname ==  'FoodPreParationOrderEvent' and cmdset.getValue('Status') == "Idle":
			FoodPreparationSrv_GlobalEvtFlag = True	
		pass
		
		
		if cmdset.m_cmdname == 'FoodPreParationCompleteEvent'and cmdset.getValue('Status') == "PreparationComplete":
			global FoodPreparationSrv_waitingPreparationFlag
			FoodPreparationSrv_waitingPreparationFlag = False 
		
	def execute(self,userdata):
		#print "FoodPreparationSrv_PushOrder State Start"
		
		"""
		global FoodPreparationSrv_GlobalEvtFlag	
		ResultCode = 'retry'

		if FoodPreparationSrv_GlobalEvtFlag == True:			
			FoodPreparationSrv_GlobalEvtFlag = False
			FoodPreparationSrv = 'failure'
			return ResultCode
		"""			
		
		global FoodPreparationSrv_cmdset	
		
		#user event
		food_preparation_order = Order()
		cmdset = FoodPreparationSrv_cmdset
		print cmdset.getValue('UserID')
		cmdset.setString('Status','Preparation')
		food_preparation_order.user_id = cmdset.getValue('UserID')
		food_preparation_order.table_id = cmdset.getValue('TableID')
		food_preparation_order.robot_id = cmdset.getValue('RobotID')
		food_preparation_order.status = cmdset.getValue('Status')
		
		global kitchen_mgr_pub
		print food_preparation_order.user_id
		kitchen_mgr_pub.publish(food_preparation_order)
		userId = food_preparation_order.user_id
		
		global FoodPreparationSrv_waitingPreparationFlag
		FoodPreparationSrv_waitingPreparationFlag = True
		
		while FoodPreparationSrv_waitingPreparationFlag :
			time.sleep(1)	
			pass 
		FoodPreparationSrv_UserID = 0
		
				
		cmdset.setCmdName('RobotDeliveryOrderEvent')
		cmdset.setSenderID('FoodPreparationSrv')
		cmdset.setReceiverID('RobotDeliverySrv')
		EventProc(cmdset)
			
		return 'success'


		
		
##RobotDeliverySrv ############################################################

RobotDeliverySrv_CBList = []
RobotDeliverySrv_EvtList = {'RobotDeliveryOrderEvent':'GlobalEvent'}
RobotDeliverySrv_GlobalEvtFlag = False

global RobotDeliverySrv_cmdset; RobotDeliverySrv_cmdset = commandset.CCmdSet()
global RobotDeliverySrv_RobotStatusList; RobotDeliverySrv_RobotStatusList = {}

global robot_num; robot_num = 1	
for k in range(robot_num):
	robot_name = "robot_"+str(k+1)
	RobotDeliverySrv_RobotStatusList[robot_name]="Idle" 

	
class RobotDeliverySrv_Init(smach.State):
	def __init__(self):
		smach.State.__init__(self, outcomes=['success','retry','failure'])
	
	def execute(self, userdata):
		time.sleep(1)
		return 'success'

	
class RobotDeliverySrv_Idle(smach.State):
	m_cmdsetList =[]
	
	def __init__(self):
		smach.State.__init__(self, outcomes = ['checkrobot', 'retry','failure'])
		RegEventProc(self.__class__.__name__, self.listener)
		
	def listener(self,cmdset):
		
		if cmdset.m_cmdname == 'RobotDeliveryOrderEvent' and cmdset.getValue('Status') == "Delivery":
			self.m_cmdsetList.append(cmdset) 
			
		print "RobotDeliverySrv Push order: ",len(self.m_cmdsetList)	
		pass
		
	def execute(self, userdata):
		while True:
			while len(self.m_cmdsetList) == 0:
					time.sleep(0.001)		
					pass
			cmdset = self.m_cmdsetList.pop(0)
			print "RobotDeliverySrv Pop order: ",len(self.m_cmdsetList)
			
			if cmdset.m_cmdname == 'RobotDeliveryOrderEvent' and cmdset.getValue('Status') == "Delivery":
				global RobotDeliverySrv_cmdset
				RobotDeliverySrv_cmdset = cmdset				
				return 'checkrobot'	



class RobotDeliverySrv_CheckRobot(smach.State):
	m_IsRunning = [True]
	
	def __init__(self):
		smach.State.__init__(self, outcomes = ['pushorder', 'retry','failure'],output_keys=["robot_id"])
		RegEventProc(self.__class__.__name__, self.listener)
		
	def listener(self,cmdset):
		global RobotDeliverySrv_GlobalEvtFlag
		if cmdset.m_cmdname ==  'RobotDeliveryOrderEvent' and cmdset.getValue('Status') == "Delivery":
			FoodPreparationSrv_GlobalEvtFlag = True	
		
	

	def execute(self, userdata):
		
		"""
		global RobotDeliverySrv_GlobalEvtFlag	
		ResultCode = 'retry'

		if RobotDeliverySrv_GlobalEvtFlag == True:			
			RobotDeliverySrv_GlobalEvtFlag = False
			RobotDeliverySrv = 'failure'
			return ResultCode			
		"""
		global robot_num			
		while True:
			for k in range(robot_num):
				robot_name = "robot_"+str(k+1)
				if RobotDeliverySrv_robotlist[robot_name] == "Idle":
					RobotDeliverySrv_robotlist[robot_name] == "Delivery" 	
					userdata.robot_name = k+1
					break;
			rospy.sleep(1)
		
		return 'pushorder'	


class RobotDeliverySrv_PushOrder(smach.State):
	m_IsRunning = [True]
	
	def __init__(self):
		smach.State.__init__(self, outcomes = ['success','retry','failure'],input_keys = ["robot_id"])
		RegEventProc(self.__class__.__name__, self.listener)
	
	def listener(self,cmdset):
		global RobotDeliverySrv_GlobalEvtFlag
		
		if cmdset.m_cmdname ==  'RobotDeliveryOrderEvent' and cmdset.getValue('Status') == "Delivery":
			FoodPreparationSrv_GlobalEvtFlag = True	
		pass
		
	def execute(self,userdata):
		#print "FoodPreparationSrv_PushOrder State Start"
		
		"""
		global FoodPreparationSrv_GlobalEvtFlag	
		ResultCode = 'retry'

		if FoodPreparationSrv_GlobalEvtFlag == True:			
			FoodPreparationSrv_GlobalEvtFlag = False
			FoodPreparationSrv = 'failure'
			return ResultCode
		"""			
		
		global RobotDeliverySrv_cmdset	
		
		#user event		
		robot_name = userdata.robot_name
		robot_delivery_order = Order()
		cmdset = RobotDeliverySrv_cmdset
		robot_delivery_order.user_id = cmdset.getValue('UserID')
		robot_delivery_order.table_id = cmdset.getValue('TableID')
		robot_delivery_order.robot_id = cmdset.getValue('RobotID')
		robot_delivery_order.status = cmdset.getValue('Status')
		
		robot_pub_topic = "delivery_order_"+robot_name+"_pub"
		robot_pub_list[robot_pub_topic].publish(robot_delivery_order)
			
		return 'success'
	
#######################################################################################################
##Define Action
####################################################################################################### 


#######################################################################################################
##Main
####################################################################################################### 

def main():
	print "=========================Main start==============================="
	
	####################################################
	rospy.init_node('taskcoordinator', anonymous = True)
	rospy.Subscriber("new_order_sub",Order, Recv)
	####################################################
	
	####################################################
	global kitchen_mgr_pub
	kitchen_mgr_pub = rospy.Publisher('food_preparation_order_pub', Order)
	
	rospy.Subscriber("food_preparation_order_sub",Order, Recv)
	####################################################
	
	####################################################
		
	#init
	global robot_num; robot_num = 1	
	global robot_pub_list; robot_pub_list = {}
	

	robot_init_pub = rospy.Publisher("delivery_robot_init_pub", Int32)
	robot_init_pub.publish(robot_num)
	
	for k in range(robot_num):	
		robot_name = "robot_"+str(k+1)

		robot_pub_topic = "delivery_order_"+robot_name+"_pub"
		robot_pub_list[robot_name]=rospy.Publisher(robot_pub_topic, Order)

		robot_sub_topic = "delivery_order_"+robot_name+"_sub"
		rospy.Subscriber(robot_sub_topic,Order, Recv)
		
		
	####################################################
			
	sm_top = smach.Concurrence(outcomes=['end'], default_outcome = 'end',  outcome_map = {'end':{'OrderManagingSrv':'end',
												'FoodPreparationSrv':'end',
												'RobotDeliverySrv':'end'
												}})
	with sm_top:
		sm_OrderManagingSrv = smach.StateMachine(outcomes = ['end'])
		sm_FoodPreparationSrv = smach.StateMachine(outcomes = ['end'])	
		sm_RobotDeliverySrv = smach.StateMachine(outcomes = ['end'])		
		
		with sm_OrderManagingSrv:
			smach.StateMachine.add('OrderManagingSrv_Init', OrderManagingSrv_Init(), 
														transitions={'success':'OrderManagingSrv_Idle', 'failure':'end', 'retry':'OrderManagingSrv_Init'})
			
			smach.StateMachine.add('OrderManagingSrv_PushOrder', OrderManagingSrv_PushOrder(), 
														transitions={'success':'OrderManagingSrv_Idle', 'failure':'end', 'retry':'OrderManagingSrv_PushOrder'})		
			
			smach.StateMachine.add('OrderManagingSrv_Idle', OrderManagingSrv_Idle(), 
														transitions={'pushorder':'OrderManagingSrv_PushOrder',
																'failure':'end', 
																'retry':'OrderManagingSrv_Init'})
			
			
			pass
		with sm_FoodPreparationSrv:
			smach.StateMachine.add('FoodPreparationSrv_Init', OrderManagingSrv_Init(), 
														transitions={'success':'FoodPreparationSrv_Idle', 'failure':'end', 'retry':'FoodPreparationSrv_Init'})
			
			smach.StateMachine.add('FoodPreparationSrv_PushOrder', FoodPreparationSrv_PushOrder(), 
														transitions={'success':'FoodPreparationSrv_Idle', 'failure':'end', 'retry':'FoodPreparationSrv_PushOrder'})
			smach.StateMachine.add('FoodPreparationSrv_CheckKitchenManager', FoodPreparationSrv_CheckKitchenManager(), 
														transitions={'pushorder':'FoodPreparationSrv_PushOrder', 'failure':'end', 'retry':'FoodPreparationSrv_CheckKitchenManager'})		
			
			smach.StateMachine.add('FoodPreparationSrv_Idle', FoodPreparationSrv_Idle(), 
														transitions={'checkKitchenMgr':'FoodPreparationSrv_CheckKitchenManager',
																'failure':'end', 
																'retry':'FoodPreparationSrv_Init'})
					
			pass
		with sm_RobotDeliverySrv:
			
			smach.StateMachine.add('RobotDeliverySrv_Init', RobotDeliverySrv_Init(), 
														transitions={'success':'RobotDeliverySrv_Idle', 'failure':'end', 'retry':'RobotDeliverySrv_Init'})
			
			smach.StateMachine.add('RobotDeliverySrv_PushOrder', RobotDeliverySrv_PushOrder(), 
														transitions={'success':'RobotDeliverySrv_Idle', 'failure':'end', 'retry':'RobotDeliverySrv_PushOrder'},
														remapping={"robot_id":"robot_id"})
			smach.StateMachine.add('RobotDeliverySrv_CheckRobot', RobotDeliverySrv_CheckRobot(), 
														transitions={'pushorder':'RobotDeliverySrv_PushOrder', 'failure':'end', 'retry':'RobotDeliverySrv_CheckRobot'},
														remapping={"robot_id":"robot_id"})		
			
			smach.StateMachine.add('RobotDeliverySrv_Idle', RobotDeliverySrv_Idle(), 
														transitions={'RobotDeliverySrv':'RobotDeliverySrv_CheckRobot',
																'failure':'end', 
																'retry':'RobotDeliverySrv_Init'})			
			pass
		smach.Concurrence.add('OrderManagingSrv', sm_OrderManagingSrv)
		smach.Concurrence.add('FoodPreparationSrv', sm_FoodPreparationSrv)
		smach.Concurrence.add('RobotDeliverySrv', sm_RobotDeliverySrv)				
		
	outcome = sm_top.execute()



	print "=========================Main end================================="



if __name__ == '__main__':
    main()

