import utilities
import sys
import time

def main(argv):

	utilities.setupcsv()
	if(len(argv) != 3):
		print("Expecting filename with all times and filename with outlier times to process to be provided as command line arguments.")
		print("Not provided so exiting"); 
		return
	timesfile = argv[1]
	outlierfile = argv[2]
	filesystem = 2
	dataset = outlierfile.split("_")[0]
	alltimes = utilities.readfile(timesfile,',',False)
	outliertimes = utilities.readfile(outlierfile,',',False)
# Start and end times of the periods in question
	alltimes = utilities.converttexttotime(alltimes)
	outliertimes = utilities.converttexttotime(outliertimes)
# Start and end times, plus 10 minutes before and 10 minutes after (in that order)
	augmentedalltimes = utilities.addbeforeandaftertimes(alltimes)
# Unixtime version of the augmented times to enable database querying
	unixalltimes = utilities.getunixtimes(augmentedalltimes)
	sourcedata = utilities.opendatabase()
	ossdata = utilities.getossdata(sourcedata,filesystem,unixalltimes,augmentedalltimes)
	aggregatedalldata = utilities.processossdata(ossdata)
	utilities.printprocessedossdata(aggregatedalldata,outliertimes,True,dataset)
	utilities.graphprocessedossdata(aggregatedalldata,outliertimes,True,dataset)
	utilities.closedatabase(sourcedata)


if __name__ == '__main__':
	main(sys.argv)


