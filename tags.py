from error import MyError
import datetime
from error import log
from note_conf import HISTORY_LOCATION, PATH, TAGDB
#from common import create_file_if_not_exist

import os
import json

class TagProcessor:

    def __init__(self,name):
        self.name = name

    def _expect(self, value,min, max):
        ''' check that value is within the range'''

        if value < min: raise MyError()
        if value > max: raise MyError()

    def _parseTagForMillis(self, name):
        '''
        name - the tag itself without [ and ]
        return -1 if the tag is not millis

        '''

        if len(name) < 15:
            return -1

        ch1 = 0
        y = name[ch1 : ch1 + 4]
        m = name[ch1 + 4 : ch1 + 6]
        d = name[ch1 + 6 : ch1 + 8]
        h = name[ch1 + 9 : ch1 + 11]
        mi = name[ch1 + 11 : ch1 + 13]
        s = name[ch1 + 13 : ch1 + 15]
        #int year, month, day, hour, min, sec;
        try:
            year = int(y)
            self._expect(year,0,9999)
            month = int(m)
            self._expect(month,1,12)
            day = int(d)
            self._expect(day,1,31)
            hour = int(h)
            self._expect(hour,0,23)
            minute = int(mi)
            self._expect(minute,0,59)
            second = int(s)
            self._expect(second,0,59)


        except Exception as e:
            log(e)
            return -1

        dt = datetime.datetime(year, month, day, hour, minute, second)
        return dt.timestamp()

    def getTagInMillis(self):
        '''
        assume that time tag come first
        return time in Millis or -1

        '''

        try:
            ch1 = self.name.index('[')
            ch2 = self.name.index(']')
        except Exception as e:
            #print(e)
            return -1
        # tag format
        # [20170411-201832].txt
        #log(ch1)
        #log(ch2)
        if ch2 < ch1 + 16:
            return -1
        time_tag = self.name[ch1+1 : ch1 + 16]
        #log(time_tag)
        return self._parseTagForMillis(time_tag)
    def get_time_tag_str(self):
        '''
        :return: time tag as str or None
        '''
        try:
            ch1 = self.name.index('[')
            ch2 = self.name.index(']')
        except Exception as e:
            #print(e)
            return None
        # tag format
        # [20170411-201832].txt
        #log(ch1)
        #log(ch2)
        if ch2 < ch1 + 16:
            return None
        time_tag = self.name[ch1+1 : ch1 + 16]
        #log(time_tag)
        return time_tag

    def getNameWithoutTags(self):
        try:
            ch1 = self.name.index('[')
            ch2 = self.name.index(']')
        except:
            return self.name # no tags

        first_part = self.name[ 0 : ch1 ]
        second_part = ""
        if len(self.name) > ch2 + 1:
            second_part = self.name[ ch2 + 1 : ]
        return first_part + second_part

    def getTag(self):
        ''' return None if no tag exists
            else return string with tags
        '''

        try:
            ch1 = self.name.index('[')
            ch2 = self.name.index(']')
        except:
            return None

        if ch2 <= ch1 + 1 :
            return None

        return self.name[ch1 + 1 : ch2]

    def getTags(self):
        ''' return list of tags '''
        tag_str = self.getTag()

        if tag_str is None:
            return None

        return tag_str.split()

    def get_non_time_tag_str(self):
        ttag = self.get_time_tag_str()
        if ttag is None:
            return self.getTag()
        else:
            return self.getTag().replace(ttag, "")

    def addTag(self, tag, begin):
            ''' return name with the tag, or old name if the tag is already in the name
                begin - boolean
            '''
            tags = self.getTags()
            tag = tag.replace(" ","_") # tag.trim ?
            if tags is not None:
                for s in tags:
                    if s == tag:
                        return self.name # exist already

                ch2 = self.name.find(']')
                ch1 = self.name.find('[')
                if begin:
                    return self.name[ 0 : ch1 + 1 ] + tag + " " + self.name[ ch1 + 1 : ]
                else:
                    return self.name[ 0 : ch2 ] + " " + tag + self.name[ ch2 : ]


            pos = self.name.find('.')
            if (pos == -1): # no extension
                return self.name + '[' + tag + ']'
            else:
                return self.name[ 0 : pos ] + '[' + tag + ']' + self.name[ pos : ]

    def _fillStringWithZeros(self, width, value):
        '''
        int width
        int value

        '''
        curr_width = value // 10 + 1
        res = ""
        for i in range(width - curr_width):
            res += '0'
        res += str(value)
        return res

    def getTimeTag(self, d):
        ''' get time tag from datetime d'''
        # tag format
        # [20170411-201832].txt

        year = d.year
        month = d.month
        day = d.day
        hour = d.hour
        minute = d.minute
        second = d.second
        return str(year) + "" + self._fillStringWithZeros(2, month) + self._fillStringWithZeros(2, day) + \
                        "-" + self._fillStringWithZeros(2, hour) + self._fillStringWithZeros(2, minute) + \
                        self._fillStringWithZeros(2, second)

    def getShortTimeTag(self,d):
        year = d.year
        month = d.month
        day = d.day
        return str(year) + "" + self._fillStringWithZeros(2, month) + self._fillStringWithZeros(2, day)

    def addTimeTag(self, d):
        ''' add time tag to the name based on d=datetime and returns it
            returns the same name if there a time tag already
        '''
        if (self.getTagInMillis() == -1):
            return self.addTag(self.getTimeTag(d),True)
        else:
            return self.name #do nothing if there is a time tag already




def save_last_id():
    path = os.path.join(HISTORY_LOCATION, ".lastid")
    try:
        with open(path, "w") as f:
            f.write(last_id_symbol)
    except:
        pass


def load_last_id():
    path = os.path.join(HISTORY_LOCATION, ".lastid")
    id = "A"
    try:
        with open(path, "r") as f:
            id = f.readline()
    except:
        pass
    return id


def generate_new_id():
    global last_id_symbol
    log("last_id_symbol before",last_id_symbol)
    if last_id_symbol == "Z":
        last_id_symbol = "a"
    elif last_id_symbol == "z":
        last_id_symbol = "A"
    else:
        last_id_symbol = chr(ord(last_id_symbol) + 1)
    log("last_id_symbol after", last_id_symbol)
    save_last_id()
    prefix = TagProcessor("").getShortTimeTag(datetime.datetime.now())
    return prefix + last_id_symbol


tag_dict = {} # {tag:[path]}

def clear_tag_dict():
    global tag_dict
    tag_dict = {}

def add_tag_to_base(tags,path):
    '''

    :param tag: list of tags
    :param path: file path
    :return:
    '''
    global tag_dict
    for t in tags:
        paths = tag_dict.get(t)
        if paths is not None:
            if path not in paths:
                paths.append(path)
        else:
            tag_dict[t] = [path]

def save_tag_base():
    path = os.path.join(PATH, TAGDB)
    try:
        with open(path,"w") as f:
            json.dump(tag_dict,f)
    except:
        pass

def load_tag_base():
    global tag_dict
    path = os.path.join(PATH, TAGDB)
    try:
        with open(path, "r") as f:
            tag_dict = json.load(f)
    except:
        pass

def get_tags_in_file(path):
    '''

    :param path: path to the file to look tags in
    :return: list of tags
    '''
    try:
        with open(path,"r") as f:
            for line in f:
                line = line.strip()
                if "tags:" in line:
                    pos = line.find("tags:")
                    tags_str = line[5+pos:]
                    arr = tags_str.split()
                    if len(arr) > 0:
                        return arr
    except:
        pass

    return []

def get_tag_list():
    '''

    :return: all tags in notebase
    '''
    tags = []
    for t, _ in tag_dict.items():
        tags.append(t)
    tags.sort()
    return tags

def get_paths_by_tag(tag):
    '''

    :param tag:
    :return: a list of paths corresponding to the tag
    '''
    return tag_dict.get(tag)

last_id_symbol = load_last_id()
load_tag_base()