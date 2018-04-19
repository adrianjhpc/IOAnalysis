#-*- coding: utf-8 -*-

import sys,getopt
import csv
import re
import math
import time as unixtime
import string
from dateutil import parser
from datetime import datetime
from datetime import timedelta
import MySQLdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.pylab as plab
from matplotlib.dates import DateFormatter
from matplotlib import rcParams
from matplotlib.ticker import IndexFormatter,MaxNLocator

def setupcsv():
	maxInt = sys.maxsize
	decrement = True

	while decrement:
	# decrease the maxInt value by factor 10
	# as long as the OverflowError occurs.

		decrement = False
		try:
			csv.field_size_limit(maxInt)
		except OverflowError:
			maxInt = int(maxInt/10)
			decrement = True

def readfile(filename,delimiter,header=True):
	names = []
	if(not header):
		i = 1
	else:
		i = 0
	with open(filename,'rt') as merchfile:
		merchreader = csv.reader(merchfile, delimiter=delimiter)
		for row in merchreader:
			# Ignoring header
			if(i >= 1):
				names.append(row)
			i = i + 1
	return names

def converttexttotime(inputtext):
	outputtimes = []
	for time in inputtext:
		if(len(time) > 0):
			templist = []
			templist.append(parser.parse(time[0]))
			templist.append(parser.parse(time[1]))
			outputtimes.append(templist)
	return outputtimes

def addbeforeandaftertimes(inputtimes):
	for idx,time in enumerate(inputtimes):
		inputtimes[idx].append(time[0]-timedelta(minutes=10))
		inputtimes[idx].append(time[1]+timedelta(minutes=10))
	return inputtimes

def getunixtimes(times):
	unixtimes = []
	for time in times:
		temptimes = []
		for individualtimes in time:
			temptimes.append(converttounixtime(individualtimes))
			
		unixtimes.append(temptimes)
	return unixtimes

def converttounixtime(time):
	return int(unixtime.mktime(time.timetuple()))

def opendatabase():

	try:
		db = MySQLdb.connect(user='root',passwd='1ns0mn1a',db='ARCHER')

		return db
	except Exception as err:
		print(err)

def closedatabase(connect):
	if not (connect is None):
		connect.close()

def deleterecords(connect,filesystem):
	if not (connect is None):
		cursor = connect.cursor()

		query = ("SELECT count(*) FROM oss where fs = %s")

		cursor.execute(query, (filesystem,))

		(numberofrows,)=cursor.fetchone()
		chunksize=1000000
		numberofgroups = (numberofrows/chunksize)+1

		for i in range(1, numberofgroups):
			print("Deleting chunk " + str(i) + " of " + str(numberofgroups) + "\n")
			deletequery = ("DELETE FROM oss where fs = %s limit %s")
			cursor.execute(deletequery, (filesystem, chunksize))
			connect.commit()
		cursor.close()

def getossdata(connect,filesystem,unixtimes,times):
	returndata = []
	if not (connect is None):
		cursor = connect.cursor()

		query = ("SELECT time,read_kb,read_ops,write_kb,write_ops,other,client,oss FROM oss where fs = %s and time >= %s AND time <= %s")

		for idx,time in enumerate(unixtimes):
			cursor.execute(query, (filesystem,time[0],time[1]))
			alldata = cursor.fetchall()
			tempdata = []
			tempdata.append(times[idx][0])
			tempdata.append(times[idx][1])
			for entry in alldata:
				tempdata.append(entry)
			returndata.append(tempdata)
	return returndata

# Expecting a database table like this:
# +-------+---------------------+------+-----+---------+-------+
#| Field | Type		       | Null | Key | Default | Extra |
#+-------+---------------------+------+-----+---------+-------+
#| apid  | int(10) unsigned    | YES  | UNI | NULL    |       |
#| start | int(10) unsigned    | YES  | MUL | NULL    |       |
#| end   | int(10) unsigned    | YES  |     | 0       |       |
#| gni   | tinyint(3) unsigned | YES  |     | NULL    |       |
#| nodes | mediumtext	       | YES  |     | NULL    |       |
#| job   | int(10) unsigned    | YES  |     | NULL    |       |
#+-------+---------------------+------+-----+---------+-------+

def getappdata(connect,unixtimes,times):
	returndata = []
	if not (connect is None):
		cursor = connect.cursor()

		query = ("SELECT start,end,nodes FROM app_details where (end >= %s AND start <= %s)")

		for idx,time in enumerate(unixtimes):
			cursor.execute(query, (time[0],time[1]))
			alldata = cursor.fetchall()
			tempdata = []
			tempdata.append(times[idx][0])
			tempdata.append(times[idx][1])
			for entry in alldata:
				# Need to add 1 hour on to the times as the app times (from the database) here are 1 hour out from the timestamps in the profile times
				# This is likely to be a daylight saving thing, so may need to be fixed properly (i.e. so hours aren't added when not needed) for
				# more wider use.
				tempdata.append([datetime.fromtimestamp(entry[0])+timedelta(hours=1),datetime.fromtimestamp(entry[1])+timedelta(hours=1),entry[2]])
			returndata.append(tempdata)
	return returndata

# Expecting a database table like this:
# +-------+---------------------+------+-----+---------+-------+
#| Field | Type		       | Null | Key | Default | Extra |
#+-------+---------------------+------+-----+---------+-------+
#| apid  | int(10) unsigned    | YES  | UNI | NULL    |       |
#| start | int(10) unsigned    | YES  | MUL | NULL    |       |
#| end   | int(10) unsigned    | YES  |     | 0       |       |
#| gni   | tinyint(3) unsigned | YES  |     | NULL    |       |
#| nodes | mediumtext	       | YES  |     | NULL    |       |
#| job   | int(10) unsigned    | YES  |     | NULL    |       |
#+-------+---------------------+------+-----+---------+-------+

def getappdatafromappids(connect,appids):
	returndata = []
	if not (connect is None):
		cursor = connect.cursor()

		query = ("SELECT start,end,nodes FROM app_details where (job = %s)")

		for nextid in appids:
			if(len(nextid) != 0):
				cursor.execute(query,(nextid[0],))
				alldata = cursor.fetchall()
   				tempdata = []
				tempdata.append(nextid)
				for entry in alldata:
					# Need to add 1 hour on to the times as the app times (from the database) here are 1 hour out from the timestamps in the profile times
					# This is likely to be a daylight saving thing, so may need to be fixed properly (i.e. so hours aren't added when not needed) for 
					# more wider use.
					tempdata.append([datetime.fromtimestamp(entry[0])+timedelta(hours=1),datetime.fromtimestamp(entry[1])+timedelta(hours=1),entry[2]])
				returndata.append(tempdata)
	return returndata

# Process OSS Data takes the raw database output and creates a data structure from it. Currently it the output data structure has the following form:
# Element Number	Element Data
# 0			Start time
# 1			End time
# 2			Max read KB
# 3			Min read KB
# 4			Number of read samples
# 5			Total read KB
# 6			Max read operations
# 7			Min read operations
# 8			Number of read operation samples
# 9			Total number of read operations
# 10			Total read KB/Total number of read operations
# 11			Max write KB
# 12			Min write KB
# 13			Number of write samples
# 14			Total write KB
# 15			Max write operations
# 16			Min write operations
# 17			Number of write operation samples
# 18			Total number of write operations
# 19			Total write KB/Total number of write operations
def processossdata(ossdata):
	aggregatedata = []
	for oss in ossdata:
		tempdata = []
		tempdata.append(oss[0])
		tempdata.append(oss[1])
		max_read_ops = 0
		min_read_ops = sys.maxint
		num_read_ops = 0
		read_ops = 0
		max_write_ops = 0
		min_write_ops = sys.maxint
		num_write_ops = 0
		write_ops = 0
		max_read_kb = 0
		min_read_kb = sys.maxint
		num_read_kb = 0
		read_kb = 0
		max_write_kb = 0
		min_write_kb = sys.maxint
		num_write_kb = 0
		write_kb = 0
		for data in oss[2:]:
			read_ops = read_ops + data[2]
			if(data[2] != 0): max_read_ops = max(max_read_ops, data[2])
			if(data[2] != 0): min_read_ops = min(min_read_ops, data[2])
			if(data[2] != 0): num_read_ops = num_read_ops + 1
			read_kb = read_kb + data[1]
			if(data[1] != 0): max_read_kb = max(max_read_kb, data[1])
			if(data[1] != 0): min_read_kb = min(min_read_kb, data[1])
			if(data[1] != 0): num_read_kb = num_read_kb + 1
			write_ops = write_ops + data[4]
			if(data[4] != 0): max_write_ops = max(max_write_ops, data[4])
			if(data[4] != 0): min_write_ops = min(min_write_ops, data[4])
			if(data[4] != 0): num_write_ops = num_write_ops + 1
			write_kb = write_kb + data[3]
			if(data[3] != 0): max_write_kb = max(max_write_kb, data[3])
			if(data[3] != 0): min_write_kb = min(min_write_kb, data[3])
			if(data[3] != 0): num_write_kb = num_write_kb + 1
		tempdata.append(max_read_kb)
		if(min_read_kb == sys.maxint): min_read_kb = 0
		tempdata.append(min_read_kb)
		tempdata.append(num_read_kb)
		tempdata.append(read_kb)
		tempdata.append(max_read_ops)
		if(min_read_ops == sys.maxint): min_read_ops = 0
		tempdata.append(min_read_ops)
		tempdata.append(num_read_ops)
		tempdata.append(read_ops)
		ratio = 0
		if(read_ops != 0): ratio = read_kb/read_ops
		tempdata.append(ratio)
		tempdata.append(max_write_kb)
		if(min_write_kb == sys.maxint): min_write_kb = 0
		tempdata.append(min_write_kb)
		tempdata.append(num_write_kb)
		tempdata.append(write_kb)
		tempdata.append(max_write_ops)
		if(min_write_ops == sys.maxint): min_write_ops = 0
		tempdata.append(min_write_ops)
		tempdata.append(num_write_ops)
		tempdata.append(write_ops)
		ratio = 0
		if(write_ops != 0): ratio = write_kb/write_ops
		tempdata.append(ratio)
		aggregatedata.append(tempdata)
	return aggregatedata

def processappdata(appdata):
	aggregateddata = []
	for overalldata in appdata:
		tempdata = []
		starttime = overalldata[0]
		endtime = overalldata[1]
		aggregateddata.append(starttime)
		aggregateddata.append(endtime)
		for actualdata in overalldata[2:]:
			nodelist = actualdata[2].split(",")
			expandednodelist = []
			numberofnodes = 0
			numberofentries = 0
			for node in nodelist:
				numberofentries = numberofentries+1
				if("-" in node):
					elements = node.split("-")
					numberofnodes = numberofnodes + (int(elements[1])-int(elements[0])+1)
					for x in range(int(elements[0]),int(elements[1])+1):
						expandednodelist.append(int(x))
				else:
					numberofnodes = numberofnodes + 1
					expandednodelist.append(int(node))
			expandednodelist = sorted(expandednodelist)
			spread = (float(expandednodelist[len(expandednodelist)-1]-expandednodelist[0])+1.0)/float(numberofnodes)
			tempdata.append(str(actualdata[0]))
			tempdata.append(str(actualdata[1]))
			tempdata.append(nodelist)
			tempdata.append(numberofnodes)
			tempdata.append(numberofentries)
			tempdata.append(expandednodelist)
			tempdata.append(spread)
		aggregateddata.append(tempdata)
	return aggregateddata


def processappdatafromappids(appdata):
	aggregateddata = []
	for overalldata in appdata:
		tempdata = []
		appid = overalldata[0]
		tempdata.append(appid)
		for actualdata in overalldata[1:]:
			nodelist = actualdata[2].split(",")
			expandednodelist = []
			numberofnodes = 0
			numberofentries = 0
			for node in nodelist:
				numberofentries = numberofentries+1
				if("-" in node):
					elements = node.split("-")
					numberofnodes = numberofnodes + (int(elements[1])-int(elements[0])+1)
					for x in range(int(elements[0]),int(elements[1])+1):
						expandednodelist.append(int(x))
				else:
					numberofnodes = numberofnodes + 1
					expandednodelist.append(int(node))
			expandednodelist = sorted(expandednodelist)
			spread = (float(expandednodelist[len(expandednodelist)-1]-expandednodelist[0])+1.0)/float(numberofnodes)
			tempdata.append(actualdata[0])
			tempdata.append(actualdata[1])
			tempdata.append(nodelist)
			tempdata.append(numberofnodes)
			tempdata.append(numberofentries)
			tempdata.append(expandednodelist)
			tempdata.append(spread)
		aggregateddata.append(tempdata) 
	return aggregateddata

def graphossdata(ossdata):
	for oss in ossdata:
		starttime = oss[0]
		endtime = oss[1]
		readkbtimes = []
		readkb = []
		writekbtimes = []
		writekb = []
		readopstimes = []
		readops = []
		writeopstimes = []
		writeops = []
		for data in oss[2:]:
			time = datetime.fromtimestamp(data[0])
			if(data[1] != 0): 
				readkbtimes.append(time)
				readkb.append(data[1])
			if(data[2] != 0):
				readopstimes.append(time)
				readops.append(data[2])
			if(data[3] != 0): 
				writekbtimes.append(time)
				writekb.append(data[3])
			if(data[4] != 0): 
				writeopstimes.append(time)
				writeops.append(data[4])

		if(len(readkb) != 0): creategraph(readkb,readkbtimes,None,None,False,None,None,None,None,False,"",str(starttime) + " ReadKB Profile",dayfmt=False)
		if(len(readops) != 0): creategraph(readops,readopstimes,None,None,False,None,None,None,None,False,"",str(starttime) + " ReadOps Profile",dayfmt=False)
		if(len(writekb) != 0): creategraph(writekb,writekbtimes,None,None,False,None,None,None,None,False,"",str(starttime) + " WriteKB Profile",dayfmt=False)
		if(len(writeops) != 0): creategraph(writeops,writeopstimes,None,None,False,None,None,None,None,False,"",str(starttime) + " WriteOps Profile",dayfmt=False)

def graphossdataossuse(ossdata):
	for oss in ossdata:
		osses = []
		osscounts = []
		for data in oss[2:]:
			thisoss = data[7]
			if(data[7] in osses):
				osscounts[osses.index(thisoss)] = osscounts[osses.index(thisoss)] + 1
			else:
				osses.append(thisoss)
				osscounts.append(1)

		if(len(osses) != 0):
			osses, osscounts = zip(*sorted(zip(osses, osscounts)))
			createbargraph(osscounts,osses,"blue",str(oss[0]) + " - " + str(oss[1]),"OSS","Usage count","OSS_"+str(oss[0]).replace(" ","_")+"--"+str(oss[1]).replace(" ","_"))

def graphappdata(appdata,rotatexlabels=False,reducexlabels=False,graphoutliers=False,outliers=[]):
	if(graphoutliers):
		flagoffset = len(appdata[0])
		# Mark up with entries contain outliers
		for idx,time in enumerate(appdata):
			found = False
			starttime = time[1]
			endtime = time[2]
			for outliertime in outliers:
				if(parser.parse(outliertime[0]) >= starttime and parser.parse(outliertime[1]) <= endtime):
					found = True
					break
			appdata[idx].append(found)

	rcParams.update({'figure.autolayout': True})

	times = []
	spreads = []
	colours = []
	for app in appdata:
		if(len(app) == 8 or (graphoutliers and len(app) == 9)):
			times.append(str(app[1]))
			spreads.append(float(app[7]))
			colour = "Blue"
			if(graphoutliers):
				if(app[flagoffset]): colour = "Red"
			colours.append(colour)
	if(len(spreads) != 0):
		createbargraph(spreads,times,colours,"Node spreads","Time","Spread ratio","NodeSpreads",rotatexlabels=rotatexlabels,reducexlabels=reducexlabels)
		createbargraph(spreads,times,colours,"Node spreads","Time","Spread ratio","NodeSpreadsZoom",rotatexlabels=rotatexlabels,reducexlabels=reducexlabels,zoom=True)

def printappdata(appdata,outliertimes=[],printoutliers=False):
	print("=================")
	headerstring = "Start Time	End Time	Number of Nodes	Number of Node Sequences	Node Spread"
	if(printoutliers):
		headerstring = headerstring + "	Outlier"
	print(headerstring)
	for app in appdata:
		if(len(app) == 8):
			printstring = (str(app[1]) + "	" + str(app[2]) + "	" + str(app[4]) + "	" + str(app[5]) + "	" + str(app[7]))
                        if(printoutliers):
                                found = False
                                starttime = app[1]
                                endtime = app[2]
                                for time in outliertimes:
                                        if(parser.parse(time[0]) >= starttime and parser.parse(time[1]) <= endtime):
                                                found = True
                                                break
                                if(found):
                                        printstring = printstring + "   " + "True"
			print(printstring)

		else:
			print("Problem: " + str(app))


def printprocessedossdata(ossdata,outliertimes,printoutliers,processcount):
	print(str(processcount)+ " processes")
	print("=================")
	headerstring = "Start Time       End Time	Read KB Read Ops	Read KB/Ops     Write KB	Write Ops       Write KB/Ops"
	if(printoutliers):
		headerstring = headerstring + "	Outlier"
	print(headerstring)
	for oss in ossdata:
		printstring = str(oss[0])+"	"+str(oss[1])+"	"+str(oss[5])+"	"+str(oss[9])+"	"+str(oss[10])+"	"+str(oss[14])+"	"+str(oss[18])+"	"+str(oss[19])
		if(printoutliers):
			if(outliertimes):
				found = False
				starttime = oss[0] 
				endtime = oss[1]
				for time in outliertimes:
					if(time[0] >= starttime and time[1] <= endtime): 
						found = True
						break
				if(found):
					printstring = printstring + "	" + "True"
		print(printstring)


def graphprocessedossdata(ossdata,outliersdata,graphoutliers,processcount):

	
	if(graphoutliers):
		flagoffset = len(ossdata[0])
		# Mark up with entries contain outliers
		for idx,time in enumerate(ossdata):
			found = False
			for outliertime in outliersdata:
				if(outliertime[0] >= time[0] and outliertime[1] <= time[1]):
					found = True
					break	
			ossdata[idx].append(found)
	times = []
	datas = []
	outlierstimes = []
	outliersdatas = []
	for time in ossdata:
		if(graphoutliers and time[flagoffset]):
			outlierstimes.append(time[0])
			outliersdatas.append(time[5])
		else:
			times.append(time[0])
			datas.append(time[5])
	creategraph(datas,times,outliersdatas,outlierstimes,graphoutliers,None,None,None,None,False,processcount,"Data Read KB")

	times = []
	datas = []
	outlierstimes = []
	outliersdatas = []
	for time in ossdata:
		if(graphoutliers and time[flagoffset]):
			outlierstimes.append(time[0])
			outliersdatas.append(time[9])
		else:
			times.append(time[0])
			datas.append(time[9])
	creategraph(datas,times,outliersdatas,outlierstimes,graphoutliers,None,None,None,None,False,processcount,"Data Read Operations")

	times = []
	datas = []
	outlierstimes = []
	outliersdatas = []
	for time in ossdata:
		if(graphoutliers and time[flagoffset]):
			outlierstimes.append(time[0])
			outliersdatas.append(time[10])
		else:
			times.append(time[0])
			datas.append(time[10])
	creategraph(datas,times,outliersdatas,outlierstimes,graphoutliers,None,None,None,None,False,processcount,"Data ReadKB/Operations")


	times = []
	datas = []
	outlierstimes = []
	outliersdatas = []
	for time in ossdata:
		if(graphoutliers and time[flagoffset]):
			outlierstimes.append(time[0])
			outliersdatas.append(time[14])
		else:
			times.append(time[0])
			datas.append(time[14])
	creategraph(datas,times,outliersdatas,outlierstimes,graphoutliers,None,None,None,None,False,processcount,"Data Write KB")

	times = []
	datas = []
	outlierstimes = []
	outliersdatas = []
	for time in ossdata:
		if(graphoutliers and time[flagoffset]):
			outlierstimes.append(time[0])
			outliersdatas.append(time[18])
		else:
			times.append(time[0])
			datas.append(time[18])
	creategraph(datas,times,outliersdatas,outlierstimes,graphoutliers,None,None,None,None,False,processcount,"Data Write Operations")

	times = []
	datas = []
	outlierstimes = []
	outliersdatas = []
	for time in ossdata:
		if(graphoutliers and time[flagoffset]):
			outlierstimes.append(time[0])
			outliersdatas.append(time[19])
		else:
			times.append(time[0])
			datas.append(time[19])
	creategraph(datas,times,outliersdatas,outlierstimes,graphoutliers,None,None,None,None,False,processcount,"Data WriteKB/Operations")

# Element Number	Element Data
# 0		     Start time
# 1		     End time
# 2		     Max read KB
# 3		     Min read KB
# 4		     Number of read samples
# 5		     Total read KB
# 6		     Max read operations
# 7		     Min read operations
# 8		     Number of read operation samples
# 9		     Total number of read operations
# 10		    Total read KB/Total number of read operations
# 11		    Max write KB
# 12		    Min write KB
# 13		    Number of write samples
# 14		    Total write KB
# 15		    Max write operations
# 16		    Min write operations
# 17		    Number of write operation samples
# 18		    Total number of write operations
# 19		    Totail write KB/Total number of write operations


	times = []
	datas = []
	datasmin = []
	datasmax = []
	outlierstimes = []
	outliersdatas = []
	outliersdatasmin = []
	outliersdatasmax = []
	for time in ossdata:
		if(graphoutliers and time[flagoffset]):
			outlierstimes.append(time[0])
			outliersdatas.append(time[5]/time[4])
			outliersdatasmin.append(time[3])
			outliersdatasmax.append(time[2])
		else:
			times.append(time[0])
			datas.append(time[5]/time[4])
			datasmin.append(time[3])
			datasmax.append(time[2])
	creategraph(datas,times,outliersdatas,outlierstimes,graphoutliers,datasmin,datasmax,outliersdatasmin,outliersdatasmax,True,processcount,"Data Mean ReadKB")

	times = []
	datas = []
	datasmin = []
	datasmax = []
	outlierstimes = []
	outliersdatas = []
	outliersdatasmin = []
	outliersdatasmax = []
	for time in ossdata:
		if(graphoutliers and time[flagoffset]):
			outlierstimes.append(time[0])
			outliersdatas.append(time[9]/time[8])
			outliersdatasmin.append(time[7])
			outliersdatasmax.append(time[8])
		else:
			times.append(time[0])
			datas.append(time[9]/time[8])
			datasmin.append(time[7])
			datasmax.append(time[6])
	creategraph(datas,times,outliersdatas,outlierstimes,graphoutliers,datasmin,datasmax,outliersdatasmin,outliersdatasmax,True,processcount,"Data Mean Read Operations")


	times = []
	datas = []
	datasmin = []
	datasmax = []
	outlierstimes = []
	outliersdatas = []
	outliersdatasmin = []
	outliersdatasmax = []
	for time in ossdata:
		if(graphoutliers and time[flagoffset]):
			outlierstimes.append(time[0])
			outliersdatas.append(time[14]/time[13])
			outliersdatasmin.append(time[12])
			outliersdatasmax.append(time[11])
		else:
			times.append(time[0])
			datas.append(time[14]/time[13])
			datasmin.append(time[12])
			datasmax.append(time[11])
	creategraph(datas,times,outliersdatas,outlierstimes,graphoutliers,datasmin,datasmax,outliersdatasmin,outliersdatasmax,True,processcount,"Data Mean WriteKB")

	times = []
	datas = []
	datasmin = []
	datasmax = []
	outlierstimes = []
	outliersdatas = []
	outliersdatasmin = []
	outliersdatasmax = []
	for time in ossdata:
		if(graphoutliers and time[flagoffset]):
			outlierstimes.append(time[0])
			outliersdatas.append(time[18]/time[17])
			outliersdatasmin.append(time[16])
			outliersdatasmax.append(time[15])
		else:
			times.append(time[0])
			datas.append(time[18]/time[17])
			datasmin.append(time[16])
			datasmax.append(time[15])
	creategraph(datas,times,outliersdatas,outlierstimes,graphoutliers,datasmin,datasmax,outliersdatasmin,outliersdatasmax,True,processcount,"Data Mean Write Operations")



def creategraph(datas,times,outliersdatas,outlierstimes,graphoutliers,mindatas,maxdatas,outliermindatas,outliermaxdatas,errorbars,processcount,graphtype,dayfmt=True):
	
	figure, ax = plt.subplots()
	ax.set_xlabel("Date")
	ax.set_ylabel(graphtype)
	if(errorbars):
		ax.errorbar(times,datas,yerr=[mindatas,maxdatas],capsize=2,linestyle='None',marker="x",color="blue")
	else:
		ax.plot(times,datas,"bx",color="blue")
	if(graphoutliers):
		if(errorbars):
			ax.errorbar(outlierstimes,outliersdatas,yerr=[outliermindatas,outliermaxdatas],capsize=2,linestyle='None',marker="+",color="red")
		else:
			ax.plot(outlierstimes,outliersdatas,"b+",color="red")
	if(dayfmt):
		myFmt = DateFormatter("%b%d")
	else:
		myFmt = DateFormatter("%H:%M:%S")
	ax.xaxis.set_major_formatter(myFmt)
	figure.autofmt_xdate()
	for tick in ax.get_xticklabels():
		tick.set_rotation(90)
	tempfilename = graphtype.replace("/", " ")
	tempfilenamelist = tempfilename.split(" ")
	filename = ""
	for tempfile in tempfilenamelist:
		filename = filename + tempfile
	figure.savefig(filename+"_"+str(processcount)+".png")
	plt.close()		

def createbargraph(values,labels,colours,graphtitle,xlabel,ylabel,filename,rotatexlabels=False,reducexlabels=False,zoom=False):

	figure, ax = plt.subplots()
	ax.set_xlabel(xlabel)
	ax.set_ylabel(ylabel)


	ax.bar(range(len(values)),values,color=colours,tick_label=labels)
	ax.set_title(graphtitle)
	if(zoom):
		plt.ylim(0, max(values)/5)
	if(rotatexlabels):
		for tick in ax.get_xticklabels():
			tick.set_rotation(90)
	if(reducexlabels):
		ax.xaxis.set_major_locator(MaxNLocator(10))
		ax.xaxis.set_major_formatter(IndexFormatter(labels))
	figure.savefig(filename+".png")
	plt.close()
