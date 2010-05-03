#!/usr/bin/env python 

""" This program reads out the information of the xml files of an 
ImageRail project. 

"""

from lxml import etree
import string 
import os.path
import ConfigParser

class Reader:
    config = ConfigParser.SafeConfigParser()
    config.read('reader.cfg')
    try:
        plate_dir = config.get('xml', 'plate_dir')
        plate_prefix = config.get('xml', 'plate_prefix')
        xml_name = config.get('xml', 'xml_name')
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        plate_dir, plate_prefix, xml_name = ('Data', 'plate_',
        'ExpMetaData.xml')

    col_nr = 0
    row_nr = 0
    data = {}

    def __init__(self, projectpath):
        self.projectpath = projectpath
        
        """ Take plate 0 (which is always available) and 
        calculate the number of rows and columns

        """
        tree = etree.parse(os.path.join(self.projectpath, self.plate_dir, 
            self.plate_prefix + '0', self.xml_name))
        root = tree.getroot()

#Get the Well ids. First the letters then the numbers.
#In the end we have the number of rows and columns for id mapping
        rows = [child.values()[0][0] for child in root.getchildren()]
        rows_nodups = dict(map(lambda i: (i,1), rows)).keys()
        self.row_nr = len(rows_nodups)
        cols = [int(child.values()[0][1:]) for child in
                root.getchildren()]
        cols_nodups = dict(map(lambda i: (i,1), cols)).keys()
        self.col_nr = len(cols_nodups)

    def get_well_data(self, plateID, ID):
        """ The ID can be in the formats 'B03', 'B3', or 4

        """
        if type(ID) == int:
            letter = string.uppercase[ID % self.row_nr]
            id = [ID, '%s%d' % (letter, ID / self.row_nr + 1), '%s%02d' %
                    (letter, ID / self.row_nr + 1)]
        elif len(ID) == 2:
            id = [ID, ID[:1] + '0' + ID[1:]]
        elif len(ID) > 2:
            id = [ID[:1] + ID[2:], ID]
        else:
            return None
    
        """ Search for the right well, than extract the data out of the
        children of the well (e.g. measurement_time)
        
        """
        tree = etree.parse(os.path.join(self.projectpath, self.plate_dir,
            self.plate_prefix + '0', self.xml_name))
        root = tree.getroot()

        data = {}
        for child in root.getchildren():
            if child.values()[0] in id:
                for grandchildren in child.getchildren():
                    data[grandchildren.tag] = grandchildren.items()
                return data

    def read_all_data(self):
        base_path = os.path.join(self.projectpath, self.plate_dir)
        for p in os.listdir(base_path):
            if p.startswith(self.plate_prefix):
                xml_path = os.path.join(base_path, p, self.xml_name)
                if not os.path.exists(xml_path):
                    continue
                root = etree.parse(xml_path).getroot()

                self.data[p] = {}
                for child in root.getchildren():
                    self.data[p][child.get('id')] = {}
                    for grandchild in child.getchildren():
                        if grandchild.tag in self.data[p][child.get('id')].keys():
                            self.data[p][child.get('id')][grandchild.tag].append(grandchild.items())
                        else:
                            self.data[p][child.get('id')][grandchild.tag] =\
                            [grandchild.items()]
        return self.data

