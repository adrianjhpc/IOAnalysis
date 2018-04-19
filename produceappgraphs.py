import utilities
import sys
import time

def main(argv):

	utilities.setupcsv()
	if(len(argv) != 2):
		print("Expecting filename(s) with the times to process to be provided as command line arguments.")
		print("Not provided so exiting"); 
		return
	for filename in argv[1:]:
		filesystem = 2
		texttimes = utilities.readfile(filename,',',False)
# Start and end times of the periods in question
		times = utilities.converttexttotime(texttimes)
# Start and end times, plus 10 minutes before and 10 minutes after (in that order)
		augmentedtimes = utilities.addbeforeandaftertimes(times)
# Unixtime version of the augmented times to enable database querying
		unixtimes = utilities.getunixtimes(augmentedtimes)
		sourcedata = utilities.opendatabase()
		appdata = utilities.getappdata(sourcedata,unixtimes,augmentedtimes)
		processedappdata = utilities.processappdata(appdata)
		for app in processedappdata:
			print app
#		utilities.graphappdata(ossdata)
	utilities.closedatabase(sourcedata)


if __name__ == '__main__':
	main(sys.argv)


