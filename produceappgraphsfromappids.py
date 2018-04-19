import utilities
import sys
import time

def main(argv):

	utilities.setupcsv()
	if(len(argv) != 2 and len(argv) != 3):
		print("Expecting filename(s) with the times to process (and possibly an outliers file) to be provided as command line arguments.")
		print("Not provided so exiting"); 
		return
	filename = argv[1]
	addoutliers = False
	if(len(argv) == 3):
		outliersfile = argv[2]
		addoutliers = True
	appids = utilities.readfile(filename,',',False)
	outliers = []
	if(addoutliers):
		outliers = utilities.readfile(outliersfile,',',False)
	sourcedata = utilities.opendatabase()
	appdata = utilities.getappdatafromappids(sourcedata,appids)
	processedappdata = utilities.processappdatafromappids(appdata)
	utilities.printappdata(processedappdata,outliers,addoutliers)
	utilities.graphappdata(processedappdata,rotatexlabels=True,reducexlabels=True,graphoutliers=addoutliers,outliers=outliers)
	utilities.closedatabase(sourcedata)


if __name__ == '__main__':
	main(sys.argv)


