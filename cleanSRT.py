# import required module
import os
# to execute in a "subs" folder, to replace the name of srt to be understable by MKVtool
 
# iterate over files in
# that directory
for filename in os.listdir():	
	#os.rename(old_name, new_name)
	if(filename.count("_")>0 and filename[-4:]==".srt"):
		print(filename)
		iu = filename.index("_")+1
		f2 = (filename[iu:iu+2]+".srt").lower()
		if(not os.path.isfile(f2)):
			os.rename(filename, f2)
		else:
			if (os.path.getsize(f2)>os.path.getsize(filename)):
				os.remove(f2)
				os.rename(filename, f2)
			else:
				os.remove(filename)
		