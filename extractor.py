# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import re
import lxml.etree as ET
import json
from patent import Patent
from logger import Logger


class NotSupportedDTDConfiguration(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class Extractor():
    def __init__(self, extractor_xpath_configuration, dir="."):
        self.extractor_xpath = extractor_xpath_configuration
        self.dir = dir
        if not os.path.isdir(dir):
            os.makedirs(dir)
        json_data = open(extractor_xpath_configuration)
        self.structure = json.load(json_data)
        json_data.close()
        self.logger = Logger().getLogger("Extractor")

    def parse(self, inputfile):
        tree = ET.parse(inputfile)
        root = tree.getroot()

        try:
            dtdStructure = self.getDTDXpathConfiguration(inputfile, tree)
        except NotSupportedDTDConfiguration as e:
            self.logger.warning(e.message)
            raise e

        patent = Patent()
        patent.documentID = root.findall(dtdStructure["documentID"])[0].text
        patent.title = root.findall(dtdStructure["inventionTitle"])[0].text
        patent.date = root.findall(dtdStructure["date"])[0].text
        patent.abstract = self.node_to_text(inputfile, root, dtdStructure, "abstract")
        patent.description = self.node_to_text(inputfile, root, dtdStructure, "description")
        patent.claims = self.node_to_text(inputfile, root, dtdStructure, "claims")

        section = root.findall(dtdStructure["section"])
        clazz = root.findall(dtdStructure["class"])
        subclass = root.findall(dtdStructure["subclass"])
        main_group = root.findall(dtdStructure["main-group"])
        subgroup = root.findall(dtdStructure["subgroup"])

        tuple = []
        for n in xrange(1, len(section)):
            tuple.append([section[n].text, clazz[n].text, subclass[n].text, main_group[n].text, subgroup[n].text])
        patent.classification = tuple
        return patent

        # patent.serialize(self.dir + '/' + root.attrib['file'] + '.save')

    def node_to_text(self, inputfile, root, structure, filepart):
        try:
            node = root.findall(structure[filepart])[0]
            text = ET.tostring(node, pretty_print=True)
            return re.sub('<[^<]+?>', '', text)
        except IndexError as e:
            self.logger.warning("Node: " + filepart + " doesn't exists in file: " + inputfile)
        return None

    def getDTDXpathConfiguration(self, inputfile, tree):
        try:
            dtdFile = tree.docinfo.internalDTD.system_url
        except Exception:
            raise NotSupportedDTDConfiguration('File: ' + inputfile + ' has not supported xml structure')

        try:
            return self.structure[dtdFile]
        except Exception:
            raise NotSupportedDTDConfiguration(
                'File: ' + inputfile + ' has not implemented structure (' + dtdFile + ')')