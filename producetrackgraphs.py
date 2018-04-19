import utilities
import sys
import time

def main(argv):

	utilities.setupcsv()
	if(len(argv) != 3):
		print("Expecting filename with the times to process and 0 or 1 (0 for OSS usage profile graphs and 1 for OSS count bar graph) to be provided as command line arguments.")
		print("Not provided so exiting"); 
		return
	filename = argv[1]
	choice = int(argv[2])
	filesystem = 2
	texttimes = utilities.readfile(filename,',',False)
# Start and end times of the periods in question
	times = utilities.converttexttotime(texttimes)
# Start and end times, plus 10 minutes before and 10 minutes after (in that order)
	augmentedtimes = utilities.addbeforeandaftertimes(times)
# Unixtime version of the augmented times to enable database querying
	unixtimes = utilities.getunixtimes(augmentedtimes)
	sourcedata = utilities.opendatabase()
	ossdata = utilities.getossdata(sourcedata,filesystem,unixtimes,augmentedtimes)
	if(choice == 0):
		utilities.graphossdata(ossdata)
	elif(choice == 1):
		utilities.graphossdataossuse(ossdata)
	else:
		print("Wrong choice")
	utilities.closedatabase(sourcedata)


if __name__ == '__main__':
	main(sys.argv)


