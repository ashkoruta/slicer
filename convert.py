import sys
import os
import re
from GPyckage.Parser import Layer,Path,ScanLine

# function compares beginning of the string with pattern and
# returns true/false + everything after "pattern + 1 MORE character"
# i.e. ;LAYER:1 matched to "LAYER" will return true,1
def matchBegin(str1,pattern):
    L = len(pattern)
    if str1[0:L] == pattern:
        return True,str1[L+1:].strip()
    else:
        return False,''

# helper function: skip lines until the pattern is matched (see above)
def skipLines(fl,pattern):
    while True:
        line = fl.readline()
        if line:
            match, param = matchBegin(line,pattern)
            if not match:
                continue
            return param
        return ''

# TODO: prob would be better to have 1 function, but oh well
def writeXmls(ls,dir_xml,xmlNameCount,chunk):
	# files are numerated as 001,002...
    for i in range(0,chunk): #0,1,...chunk-1
        abs_num = 1 + xmlNameCount + i
        fname = dir_xml + "/scan_{:03d}.xml".format(abs_num)
        ls[i].writeXml(fname,[JV,HV,CV]) #FIXME
        logfile.write("Layer {} written\n".format(abs_num))
    print("layers {}-{} xml written".format(1 + xmlNameCount,xmlNameCount + chunk))
		        
def writeXys(ls,dir_xy,xyNameCount,chunk):
    for i in range(0,chunk): #0,1,...chunk-1
        abs_num = 1 + xyNameCount + i
        logfile.write("{} paths in this layer\n".format(len(ls[i].m_paths)))
        fl = dir_xy + "/layer{}.xy".format(abs_num)
        ls[i].writeXY(fl)
        logfile.write("Layer {} written\n".format(abs_num))
        logfile.flush()
    print("layers {}-{} xy written".format(1 + xyNameCount,xyNameCount + chunk))

def saveObjs(ls,dir_bin,nameCount,chunk):
    for i in range(0,chunk): #0,1,...chunk-1
        abs_num = 1 + nameCount + i
        fname = dir_bin + "/layer{}.pickle".format(abs_num)
        ls[i].save(fname)
    print("layers {}-{} bin written".format(1 + nameCount,nameCount + chunk))

def writeChunk(ls,nameCount,chunk):
    writeXmls(ls,dir_xml,nameCount,chunk)
    writeXys(ls,dir_xy,nameCount,chunk)
    saveObjs(ls,dir_bin,nameCount,chunk)
                
## MAIN EXECUTION STARTS HERE		
print("Converting G-code to XML")

cfg = open('convert.cfg', 'r') # TODO change to cmd line param?
gname = '' # g-code file
HP = 0 # hatch power
HV = 0 # hatch speed
CP = 0 # contour power
CV = 0 # contour speed
JV = 0 # jump speed
X0 = 0 # offset in X if needed
Y0 = 0 # offset in Y, same idea

logfile = open('parser.log','w')

## Read the configuration file

while True:
    line = cfg.readline()
    if not line:
        break
    match,param = matchBegin(line,'Name')
    if match:
        gname = param;
        continue
    match,param = matchBegin(line,'HatchPower')
    if match:
        HP = int(param)
        continue
    match,param = matchBegin(line,'HatchSpeed')
    if match:
        HV = int(param)
        continue
    match,param = matchBegin(line,'ContourPower')
    if match:
        CP = int(param)
        continue
    match,param = matchBegin(line,'ContourSpeed')
    if match:
        CV = int(param)
        continue
    match,param = matchBegin(line,'OffsetX')
    if match:
        X0 = int(param)
        continue
    match,param = matchBegin(line,'OffsetY')
    if match:
        Y0 = int(param)
        continue
    match,param = matchBegin(line,'JumpSpeed')
    if match:
        JV = int(param)
        continue
    
    print('Line unrecognized, abort')
    sys.exit()
            
## Print the parsed settings
logfile.write("G-code file: {}\n".format(gname))
logfile.write("Hatch: power {} speed {}\n".format(HP,HV))
logfile.write("Contour: power {} speed {}\n".format(CP,CV))
logfile.write("Jumps at speed {}\n".format(JV))
logfile.write("Offsets: X {} Y {}\n".format(X0,Y0))

## Read the G-code file
# only G0,G1,;LAYER and ;TYPE lines matter

print("Reading G-code file...")
LayerCount = 0
TotalLayerCount = 0
gf = open(gname,'r')
Layers = []

# skip lines until ;LAYER_COUNT is found
param = skipLines(gf,';LAYER_COUNT')
if not param:
    logfile.write("Didn't find LAYER_COUNT\n")
    print("Didn't find LAYER_COUNT")
    sys.exit()
    
TotalLayerCount = int(param)
logfile.write("Total number of layers: {}\n".format(TotalLayerCount))
print("Total number of layers: {}".format(TotalLayerCount))

logfile.write("Current dir:" + os.getcwd() + "\n")
# make a directory for xy files
dir_xy = gname[0:gname.find('.')] + "_split"
os.mkdir(dir_xy)
# make a directory for xml files
dir_xml = gname[0:gname.find('.')] + "_xml"
os.mkdir(dir_xml)
# make a directory for bin files
dir_bin = gname[0:gname.find('.')] + "_bin"
os.mkdir(dir_bin)

# regular expressions for coordinate parsing
regXStr = 'X-?[0-9]*(\.[0-9]+)?'
regx = re.compile(regXStr)
regYStr = 'Y-?[0-9]*(\.[0-9]+)?'
regy = re.compile(regYStr)

nameCount = 0 # files are scan001,scan002 etc.
chunk = 10 # how many layers we store in memory before xml is written
layerNum = -1
Hatch = -1
lastX = -1 # these two are only needed for <Start> in XML at the beginning of a path
lastY = -1
curPath = Path()

while True:
    line = gf.readline();
    if not line:
        break
    if line[0] == ';': # some useful information is written by Cura in commented lines sometimes
        match1,param1 = matchBegin(line,';LAYER');
        match2,param2 = matchBegin(line,';TYPE');
        if not match1 and not match2:
            continue # ignore everything if it starts with ; and is not either layer or type
        logfile.write('Accumulated {} lines so far\n'.format(len(curPath.lines)))
        if match1:
            # if it's first ever layer, there should be no path yet
            layerNum = int(param1) # it goes like Layer:0
            logfile.write("Layer {} started\n".format(layerNum))
            if layerNum == 0:
                assert(len(curPath.lines) == 0)
                # nothing else to do here
            else: # save parsed lines into prev layer
                logfile.write('Flush to last layer, {} lines\n'.format(len(curPath.lines)))
                logfile.flush()
                assert(len(curPath.lines) > 0)
                Layers[-1].append(curPath)
                # reset
                curPath = Path()
                Hatch = -1        
            # append new layer
            Layers.append(Layer())
            # large parts require too much memory to store everything all at once
            # so save xy & xml files on the fly, in chunks of 10 or so layers
            if len(Layers) > chunk:
                logfile.write('Too many layers, flush to HDD\n')
                writeChunk(Layers,nameCount,chunk)
                Layers = Layers[chunk:] # free the space
                nameCount = nameCount + chunk
        else: # i.e. TYPE, so contour or hatch
            if len(curPath.lines) > 0: # it depends on the state: perfectly normal to be here with no lines, or some (for ex, contour after hatch)
                assert(len(Layers) > 0) # but there must already be a layer
                logfile.write('Flush to current layer {}, {} lines\n'.format(layerNum,len(curPath.lines)))
                Layers[-1].append(curPath)
            # initialize new path collection    
            curPath = Path()
            curPath.start(lastX,lastY)
            logfile.write("Start new path from {},{}\n".format(lastX,lastY)) # 1st path in 1st layer is a special case handled elsewhere below
            if param2 == "FILL":
                Hatch = 1
                curPath.mode = 'Hatch'
                logfile.write("{}: TYPE set to hatch\n".format(param2))
            else:
                Hatch = 0
                curPath.mode = 'Contour'
                logfile.write("{}: TYPE set to contour\n".format(param2))    

    elif line[0] == 'G': # parse mark/jump command
        if layerNum < 0: # something's wrong
            logfile.write("Layer's state is messed-up, abort\n")
            print("Layer's state is messed-up, abort")
            sys.exit()
        if line[0:2] != "G0" and line[0:2] != "G1": # any other G2,G3 whatever - don't care
            logfile.write("Skip non G0/G1 command\n")
            continue
        if line.find("E-") > 0: # some irrelevant move with retraction of filament in Cura
            logfile.write("Skip E- command\n")
            continue
        if line[1] == '0': # jump
            P = 0
            V = JV
        elif line[1] == '1': # mark / contour
            if Hatch < 0: # we should've encountered FILL/WALL indicator before
                logfile.write("Hatch's state is messed-up, abort\n")
                print("Hatch's state is messed-up, abort")
                sys.exit()
            if Hatch == 1:
                P = HP
                V = HV # marking hatch line
            else:
                P = CP
                V = CV # marking contour line
        logfile.write("Proper scanning command {}".format(line))
        logfile.flush()
        x = regx.search(line).group(0)[1:] # X111.111 without first symbol
        y = regy.search(line).group(0)[1:] # same for Y
        # finally, main action
        sl = ScanLine(P,V,float(x) - X0,float(y) - Y0)
        lastX = sl.X # we will need last X,Y of this layer @ the beginning of the next one
        lastY = sl.Y    
        logfile.write(sl.dump() + "\n")
        # special case: 1st ever G0 command is original jump to the starting point
        # it's before any contour/hatch definition
        if P == 0 and Hatch < 0:
            # this move is not relevant for the xml scan file: scanner positions into start point itself
            # (at least paths are correct in LabVIEW once imported)  
            # but start point needs to be saved for first ever line in the actual scan of the layer
            logfile.write('first ever jump, use it for start point\n')
            curPath.start(sl.X,sl.Y)
            continue
        else: # normal case
            curPath.append(sl)
    #ignore lines that start with everything else
    
# Path is appended to a layer only when new path / new layer starts
# so last ever path should be taken care of here
Layers[-1].append(curPath)
# dump leftover layers now
logfile.write('Last layers, flush to HDD\n')
writeChunk(Layers,nameCount,len(Layers))
logfile.flush()
logfile.close()
print('Done')
    
