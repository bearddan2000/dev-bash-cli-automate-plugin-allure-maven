#!/usr/bin/python3.8

import re, sys
import xml.dom.minidom as MD
import xml.etree.ElementTree as ET

def clean(xmlStr, header):
    '''
    Remove special characters and extra spaces from xml str
    Replace maven namespace with generic root tag
    :param xmlStr: slurped pom file
    :param header: maven namespaces
    :return: xml.etree ready string
    '''
    xmlStr = re.sub('[\n|\t]', '', xmlStr)
    xmlStr = re.sub(' +', ' ', xmlStr)
    xmlStr = re.sub('> <', '><', xmlStr)
    xmlStr = re.sub(header, '<root>', xmlStr)
    xmlStr = re.sub('<\?xml*>', '', xmlStr)
    return re.sub('</project>', '</root>', xmlStr)

def addArtifactElemen(parent, arr):
    '''
    Adds a group of tags all at once
    :param parent: The element to attach our group
    :param arr: array of groupId, artifactId, and version
    :return: None
    '''
    groupId = ET.SubElement(parent, "groupId")
    artifactId = ET.SubElement(parent, "artifactId")
    version = ET.SubElement(parent, "version")

    groupId.text = arr[0]
    artifactId.text = arr[1]
    version.text = arr[2]

def changeName(tree):
    '''
    To make pom more descriptive
    :param tree: the document root
    :return: None
    '''
    root = tree.findall(".//name")[0]
    root.text += "-Allure"

def addPropertie(tree, dict_tag):
    '''
    Adds maven variables
    :param tree: the document root
    :param dict_tag: dictionary of tag attributes
    :return: None
    '''
    props = tree.findall(".//properties")[0]
    prop = ET.SubElement(props, dict_tag['name'])
    prop.text = dict_tag['value']

def findElementBySubElementText(tree, str_elem, search):
    '''
    Searches sub elements' for a given string
    :param tree: the document root
    :param str_elem: full or partial to look for
    :param search: group xpath to search
    :return: parent element or None
    '''
    return tree.findtext(f".//plugins/plugin/artifactId", str_elem)

def buildEmbeddedElements(parent, dict_array_tag):
    el = ET.SubElement(parent, dict_array_tag[0]['name'])
    if dict_array_tag[0]['value']:
        el.text = dict_array_tag[0]['value']

    if dict_array_tag[0]['sib']:
        dict_array_tag.pop(0)
        if dict_array_tag:
            return buildEmbeddedElements(parent, dict_array_tag)
    else:
        dict_array_tag.pop(0)
        if dict_array_tag:
            return buildEmbeddedElements(el, dict_array_tag)

    return el

def checkPattern(parent, str_val):

    el = parent.find(str_val)

    if not el:
        el = ET.SubElement(parent, str_val)

    return el

def editSurefirePlugin(tree):
    root = findElementBySubElementText(tree, 'surefire', ".//plugins")
    if not root:
        print("surefire plugin not found, exiting")
        sys.exit(-1)

    conf = checkPattern(root, 'configuration')
    properties = checkPattern(conf, 'properties')

    argline = ET.SubElement(properties, "argLine")
    argline.text = "-javaagent:\"${settings.localRepository}/org/aspectj/aspectjweaver/${aspectj.version}/aspectjweaver-${aspectj.version}.jar\""

    dict_array_tag = [
        {'name': 'systemProperties', 'value': None, 'sib': False},
        {'name': 'property', 'value': None, 'sib': False},
        {'name': 'name', 'value': 'allure.results.directory', 'sib': True},
        {'name': 'value', 'value': """${project.build.directory}/allure-results""", 'sib': False}
    ]

    buildEmbeddedElements(conf, dict_array_tag)

    dict_array_tag = [
        {'name': 'dependencies', 'value': None, 'sib': False},
        {'name': 'dependency', 'value': None, 'sib': False},
        {'name': 'groupId', 'value': 'org.aspectj', 'sib': True},
        {'name': 'artifactId', 'value': 'aspectjweaver', 'sib': True},
        {'name': 'version', 'value': """${aspectj.version}""", 'sib': False},
    ]

    buildEmbeddedElements(root, dict_array_tag)

def addAllurePlugin(tree):
    root = tree.findall(".//plugins")[0]
    plugin = ET.SubElement(root, "plugin")
    addArtifactElemen(plugin, ['io.qameta.allure', 'allure-maven', '2.10.0'])
    dict_array_tag = [
        {'name': 'configuration', 'value': None, 'sib': False},
        {'name': 'reportVersion', 'value': """${allure.version}""", 'sib': True},
        {'name': 'allureDownloadUrl',
         'value': """${allure.cmd.download.url}/${allure.version}/allure-commandline-${allure.version}.zip""",
         'sib': False}
    ]
    buildEmbeddedElements(plugin, dict_array_tag)

def addAllureDep(tree):
    dict_array_tag = [
        {'name': 'dependency', 'value': None, 'sib': False},
        {'name': 'groupId', 'value': 'io.qamea.allure', 'sib': True},
        {'name': 'artifactId', 'value': '', 'sib': True},
        {'name': 'version', 'value': """${allure.version}""", 'sib': True},
        {'name': 'scope', 'value': 'test', 'sib': False}
    ]
    el = findElementBySubElementText(tree, "testng", search=".//dependencies/dependency")
    if el:
        dict_array_tag[2]['value'] = 'allure-testng'
    else:
        el = findElementBySubElementText(tree, "junit", ".//dependency")
        dict_array_tag[2]['value'] = 'allure-junit5'

    print(el)
    # buildEmbeddedElements(el, dict_array_tag)

def redoDir(lst, idx, repl):
    del lst[idx]
    lst.insert(idx, repl)

def main():
    tree = None
    header = """<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">"""
    with open(sys.argv[1], encoding='utf-8') as f:
        xmlStr = f.readlines()
        redoDir(xmlStr, 0, """<?xml version="1.0" ?>""")
        redoDir(xmlStr, 1, header)
        xmlStr = clean("".join(xmlStr), header)
        tree = ET.fromstring(xmlStr)
    changeName(tree)
    addPropertie(tree, {'name': 'allure.cmd.download.url',
                        'value': 'https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline'})
    addPropertie(tree, {'name': "allure.version", 'value': "2.17.2"})
    addPropertie(tree, {'name': "aspectj.version", 'value': "1.9.5"})
    addAllureDep(tree)
    editSurefirePlugin(tree)
    addAllurePlugin(tree)

    xmlstr = MD.parseString(ET.tostring(tree)).toprettyxml(indent="   ")
    with open(sys.argv[1], "w") as f:
        xmlStr = xmlStr.replace('&quot;', '"')
        xmlstr = xmlstr.replace('<root>', header).replace('</root>', '</project>')
        f.write(xmlstr)


if __name__ == '__main__':
    main()
