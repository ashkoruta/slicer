import xml.etree.ElementTree as ET
import json
import pickle

# make pretty XML string
def indent(elem, level=0): # copied from the Internet
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# create <Path> with all internal stuff for the XML
def xmlPath(trjNode, curPath, Vs):
    p = ET.SubElement(trjNode,'Path')
    ptype = ET.SubElement(p,'Type')
    # don't think it's used anywhere but
    # I have to maintain different Paths for separation between Contours and Hatches for
    # legible camera acquisition
    ptype.text = curPath.mode # hatch or contour
    tag = ET.SubElement(p,'Tag')
    tag.text = 'main' # don't think it's used anywhere
    NS = ET.SubElement(p,'NumSegments')
    NS.text = str(len(curPath.lines))
    st = ET.SubElement(p,'Start') # start point. there is some wiggling related to this in the main func
    ex = ET.SubElement(st,'X')
    ex.text = str(curPath.startX)
    ey = ET.SubElement(st,'Y')
    ey.text = str(curPath.startY)
    for s in curPath.lines:
        seg = ET.SubElement(p,'Segment')
        sid = ET.SubElement(seg,'SegmentID')
        sid.text = '0' # unused afaik
        power = ET.SubElement(seg,'Power')
        power.text = str(s.P)
        vel = ET.SubElement(seg,'idxVelocityProfile')
        vel.text = str(Vs.index(s.V))
        e = ET.SubElement(seg,'End')
        xt = ET.SubElement(e,'X')
        xt.text = str(s.X)
        yt = ET.SubElement(e,'Y')
        yt.text = str(s.Y)

# line is an end point + associated power and speed
# aka <Segment>
class ScanLine:
    P = -1
    V = -1
    X = -1
    Y = -1
    def __init__(self,p,v,x,y):
        self.P = p
        self.V = v
        self.X = x
        self.Y = y
    def dump(self): # for raw coordinate files
        return "{}/{} [{},{}]".format(self.P,self.V,self.X,self.Y)
    
# then, can concatenate geometry easily, just need to end 1 jump before each appended file 
# make sure it makes sense though, because start/end might not align.
# best way is to insert all additional ones before the last jump and insert additional jumps to link them
# BUT need to also collect all unique speeds and assign them to combined XML

# corresponds to <Path>, i.e. start point, type, and list of vectors
class Path:
    startX = -1 # these are needed for the first path in the layer
    startY = -1
    mode = ""
    lines = []
    def __init__(self):
        self.startX = -1
        self.startY = -1
        self.lines = []
    def start(self,x,y):
        self.startX = x
        self.startY = y
    def append(self,ln):
        self.lines.append(ln)
    def uniqueSpeeds(self):
        speeds = map(lambda x: x.V, self.lines);
        speeds_list = list(speeds)
        return set(speeds_list)
    def dump(self):
        ret = str(len(self.lines)) + " lines\n"
        ret = ret + "[" + str(self.startX) + "," + str(self.startY) + "]\n"
        for ln in self.lines:
            ret = ret + ln.dump() + "\n"
        return ret

class Layer:
    m_paths = []
    def __init__(self):
        self.m_paths = []
    def append(self,p):
        self.m_paths.append(p)
    def extend(self,l):
        self.m_paths.extend(l.m_paths)
    def uniqueSpeeds(self):
        vs = set()
        for l in self.m_paths:
            vs.update(l.uniqueSpeeds())
        return vs
    def dump(self):
        ret = ""
        for i,m_path in enumerate(self.m_paths):
            ret = ret + "path " + str(i) + "\n";
            ret = ret + m_path.dump() + "\n"
        return ret
    def writeXY(self,fname):
        fl = open(fname,'w+')
        fl.write(self.dump())
        fl.close()
    def writeXml(self,fname,Vs):
        # create root
        root = ET.Element('Build')
        th = ET.SubElement(root, 'Thickness')
        th.text = str(0.03) # doesn't matter: slicer files have 0.05 and builds are with 0.03 - way to go ....
        # prepare velocity list: 0 - jump, 1 - mark, 2 - contour
        vpl = ET.SubElement(root, 'VelocityProfileList')
        for i,v_i in enumerate(Vs): 
            vp = ET.SubElement(vpl,'VelocityProfile')
            vid = ET.SubElement(vp,'ID')
            vid.text = str(i)
            v = ET.SubElement(vp,'Velocity')
            v.text = str(v_i)
            # everything below is unused afaik
            mode = ET.SubElement(vp,'Mode')
            mode.text = "Auto"
            tv1 = ET.SubElement(vp,'tV1')
            tv1.text = '0'
            tv2 = ET.SubElement(vp,'tV2')
            tv2.text = '0'
            tv3 = ET.SubElement(vp,'tV3')
            tv3.text = '0'
            tv4 = ET.SubElement(vp,'tV4')
            tv4.text = '0'
        # create trajectory
        trj = ET.SubElement(root, 'Trajectory')
        tid = ET.SubElement(trj,'TravelerID') # aka laser id which have only 1
        tid.text = '1' # don't think it's used anywhere
        delay = ET.SubElement(trj,'SyncDelay')
        delay.text = '0' # don't think it's used anywhere
        for curPath in self.m_paths:
            xmlPath(trj,curPath,Vs)
        # finally, write xml file
        indent(root)
        xml_string = ET.tostring(root)
        fl = open(fname,'wb+')
        fl.write(xml_string)
        fl.close()
        #print "layer {} xml written".format(count)		
    def save(self,fname):
        # save JSON representation - decided against it
        #fl = open(dir_bin + "/layer{}.json".format(count),'w+')
        #json.dump(obj=self,fp=fl)
        #fl.close()
        # save Pickle too
        fl = open(fname,'wb+')
        pickle.dump(obj=self,file=fl)
        fl.close()
        
            
        
