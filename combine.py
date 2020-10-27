import sys
import os
import pickle
from GPyckage.Parser import Layer,Path,ScanLine

NF = len(sys.argv) - 1 # number of files to combine
if NF < 2:
    print('What are you doing?')
    print('Usage: combine.py dir1 dir2 dir3')
    exit()

dirsToComb = sys.argv[1:]
print ('Files to combine:', dirsToComb)

# what's the number of files in each directory? 
fileCounts = []
for d in dirsToComb:
    fileCounts.append(len(os.listdir(d)))

print('File counts:', fileCounts)
fileCountMax = max(fileCounts)
print('Total number of layers ', fileCountMax)

os.mkdir('combined_xml')
os.mkdir('combined_xy')
os.mkdir('combined_bin')

# read in one file from each directory, parse them in, combine, write out
for i in range(1,fileCountMax):
    # names for combined files
    combined_xml = "combined_xml/scan_{:03d}.xml".format(i)
    combined_xy = "combined_xy/layer{}.xy".format(i)
    combined_bin = "combined_bin/layer{}.pickle".format(i)
    comb_layer = Layer()
    for di,dname in enumerate(dirsToComb):
        # are there still files in this directory?
        if fileCounts[di] < i:
            continue 
        # read in an appropriate file
        fname = dname + '/layer{}.pickle'.format(i)
        if i%10 == 0:
            print(fname)
        fl = open(fname, 'rb')
        cur_layer = pickle.load(fl)
        comb_layer.extend(cur_layer) # extends path list of comb_layer by paths from the cur_layer
        # I don't need to start next path where the previous ended, it works fine without it 
    # produce list of unique speeds
    Vs = list(comb_layer.uniqueSpeeds())
    # dump that as XML & XY file into "combined"
    comb_layer.save(combined_bin)
    comb_layer.writeXY(combined_xy)
    comb_layer.writeXml(combined_xml,Vs) #FIXME put true speeds here
 
print("Done") 