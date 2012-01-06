"""
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Quick Script by
Johann du Toit
exxonno[at]gmail[dot]com
https://github.com/Johanndutoit/Zip-to-FTP-Backup
"""

import zipfile, os, sys
import datetime
import io
import ConfigParser
import shutil
import ftplib
import datetime
 
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('backupcfg.ini')

"""
Returns the Diff in Month between two dates
"""
def diff_month(d1, d2):
	return (d1.year - d2.year)*12 + d1.month - d2.month
 
def makeArchive(fileList, archive):
    """
    'fileList' is a list of file names - full path each name
    'archive' is the file name for the archive with a full path
    """
    try:
        a = zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED)
        for f in fileList:
            a.write(f)
        a.close()
        return True
    except: return False
 
def dirEntries(dir_name, subdir, *args):
    '''Return a list of file names found in directory 'dir_name'
    If 'subdir' is True, recursively access subdirectories under 'dir_name'.
    Additional arguments, if any, are file extensions to match filenames. Matched
        file names are added to the list.
    If there are no additional arguments, all files found in the directory are
        added to the list.
    Example usage: fileList = dirEntries(r'H:\TEMP', False, 'txt', 'py')
        Only files with 'txt' and 'py' extensions will be added to the list.
    Example usage: fileList = dirEntries(r'H:\TEMP', True)
        All files and all the files in subdirectories under H:\TEMP will be added
        to the list.
    '''
    fileList = []
    for file in os.listdir(dir_name):
        dirfile = os.path.join(dir_name, file)
        if os.path.isfile(dirfile):
            if not args:
                fileList.append(dirfile)
            else:
                if os.path.splitext(dirfile)[1][1:] in args:
                    fileList.append(dirfile)
        # recursively access file names in subdirectories
        elif os.path.isdir(dirfile) and subdir:
            fileList.extend(dirEntries(dirfile, subdir, *args))
    return fileList
	
if __name__ == '__main__':
	print "ZIP to FTP Backup Tool"
	print "v0.0.1 - Johann du Toit"
	print "----------"

	filelistings = [] # All Files that will be added to the Archive

	print "\n====="
	# Add Files From Locations
	for folder in config.options("folders"):
			print "Scanning " + str(folder.strip())
			for fi in dirEntries(folder.strip(' \t\n\r'), True):
					if "WHAT IS TRANSFER.txt" not in fi:
							filelistings.append(fi)
	print "=====\n"

	now = datetime.datetime.now()
	zipname = r'shaka.' + now.strftime("%d.%m.%Y") + '.zip'

	print "\n====="
	print "Add Backup to a ZIP File"
	makeArchive(filelistings, zipname)
	print "Backup was Zipped"
	print "=====\n"

	print "\n====="
	print "Connecting to FTP Server..."

	ftp = ftplib.FTP(config.get("ftp", 'host'))
	
	print "Logging in..."
	
	ftp.login(config.get("ftp", 'username'), config.get("ftp", 'password'))

	print "Getting Directory Listing..."
	
	files = ftp.nlst()
	
	print "Found " + str(len(files)) + " files"
	
	print "Removing Stale Backups older than " + str(config.get("ftp", 'keep_for_months').strip()) + " Month(s)"
	
	count_deleted = 0
	months_from_now = int((datetime.date.today() + datetime.timedelta( ( int(config.get("ftp", 'keep_for_months').strip()) *365) / 12 )).strftime("%m"))
	
	for file in files:
		if "shaka." in file:
			file_parts = file.split('.')
			if len(file_parts) == 5:
				year = int(file_parts[3])
				month = int(file_parts[2])
				date = int(file_parts[1])
				
				date_month_diff = diff_month(datetime.datetime( int(now.strftime("%Y")), int(now.strftime("%m")), int(now.strftime("%d")) ), datetime.datetime(year,month,date))
				
				if date_month_diff >= int(config.get("ftp", 'keep_for_months').strip()):
					count_deleted = count_deleted + 1
					
					try:
						print "Removing Backup " + str(file) + " it's " + str(date_month_diff) + " Month(s) Old"
						ftp.delete(file)
					except:
						pass
	
	print "Removed " + str(count_deleted) + " Backups"
	
	print "Uploading Backup Zip..."
	
	try:
		ftp.storbinary('STOR ' + zipname, open(zipname, 'rb'))
	except:
		pass
	
	print "Closing Connection..."
	
	ftp.close()
	
	print "Deleting Backup ZIP"
	os.remove(zipname)
	
	print "=====\n"
 