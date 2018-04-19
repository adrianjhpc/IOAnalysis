import utilities
import sys
import time

def main(argv):

	utilities.setupcsv()
	if(len(argv) < 2):
		print("Expecting filename(s) with the times to process to be provided as command line arguments.")
		print("Not provided so exiting"); 
		return
	filesystem = 2
	for nextfile in argv[1:]:
		filename = nextfile
		temp = filename.split("_")
		if(len(temp) == 2):
			temp = temp[1].split(".")[0]
			processcount = int(temp)
		else:
			processcount = 0
		texttimes = utilities.readfile(filename,',',False)
# Start and end times of the periods in question
		times = utilities.converttexttotime(texttimes)
# Start and end times, plus 10 minutes before and 10 minutes after (in that order)
		augmentedtimes = utilities.addbeforeandaftertimes(times)
# Unixtime version of the augmented times to enable database querying
		unixtimes = utilities.getunixtimes(augmentedtimes)
		sourcedata = utilities.opendatabase()
		ossdata = utilities.getossdata(sourcedata,filesystem,unixtimes,augmentedtimes)
		aggregateddata = utilities.processossdata(ossdata)
		utilities.printprocessedossdata(aggregateddata,None,False,processcount)
		utilities.graphprocessedossdata(aggregateddata,None,False,processcount)
#	utilities.deleterecords(sourcedata,4)
#	utilities.deleterecords(sourcedata,1)
	utilities.closedatabase(sourcedata)


if __name__ == '__main__':
	main(sys.argv)


