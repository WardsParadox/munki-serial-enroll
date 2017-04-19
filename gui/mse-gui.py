#!/usr/bin/python
'''
Runs a gui for enrolling a Mac into Munki based on serial manifests
'''
# -*- coding: utf-8 -*-
# pylint: disable=W0614
import sys
import os
import subprocess
import httplib
from urllib import urlencode
from socket import gethostname
from collections import OrderedDict
from re import sub
from plistlib import readPlist
import objc
from Foundation import NSBundle, \
                       CFPreferencesSynchronize, \
                       CFPreferencesSetValue, \
                       kCFPreferencesAnyUser, \
                       kCFPreferencesAnyHost
from nibbler import *

try:
    script_path = os.path.dirname(os.path.realpath(__file__))
    n = Nibbler(os.path.join(script_path, 'mse-gui.nib'))
except IOError, ImportError:
    print "Unable to load nib!"
    sys.exit(20)

manifests = OrderedDict([
    ("Pretty Title 1", "BuildingManifest1"),
    ("Pretty Title 2", "BuildingManifest1"),
    ("Testing", "Testing")
])

IOKit_bundle = NSBundle.bundleWithIdentifier_('com.apple.framework.IOKit')

functions = [("IOServiceGetMatchingService", b"II@"),
             ("IOServiceMatching", b"@*"),
             ("IORegistryEntryCreateCFProperty", b"@I@@I"),
            ]

objc.loadBundleFunctions(IOKit_bundle, globals(), functions)
# pylint: disable=E0602
def io_key(keyname):
    '''
    frogor/pudquick magic
    '''
    return IORegistryEntryCreateCFProperty(IOServiceGetMatchingService(0,\
     IOServiceMatching("IOPlatformExpertDevice")), keyname, None, 0)
# pylint: enable=E0602

def get_hardware_serial():
    '''
    Get's serial directly from the Board via frogor magic
    '''
    return io_key("IOPlatformSerialNumber")

def quitgui():
    '''
    Quit GUI and Script
    '''
    n.quit()
    sys.exit()

def progress(message):
    '''
    Output value to the "progress" box
    '''
    feedback = n.views['output']
    feedback.setStringValue_(" ")
    feedback.setStringValue_(message)

def setmanifestchoices():
    '''
    Flush manifestselector to load manifests defined above.
    '''
    menu = n.views['manifestselector']
    menu.removeAllItems()
    for manifest in manifests.keys():
        menu.addItemWithTitle_(manifest)

def getmanifests():
    '''
    Gets the manifest chosen from the manifestselector
    '''
    index = n.views['manifestselector'].indexOfSelectedItem()
    values = n.views['manifestselector'].itemTitles()
    return values[index]

def getmachinename():
    '''
    Get's current hostname
    '''
    name = n.views['machinename']
    computername = gethostname()
    name.setStringValue_(computername)
    progress("Got Machine Hostname")

def setmachinename():
    '''
    Set's machine ComputerName,HostName, and LocalHostName to value in field
    '''
    newname = n.views['machinename'].stringValue()
    if newname == "":
        progress("Machine Name is Blank!")
        return
    command = {}
    command[0] = ['/usr/sbin/scutil', '--set', 'ComputerName', str(newname)]
    command[1] = ['/usr/sbin/scutil', '--set', 'HostName', str(newname)]
    command[2] = ['/usr/sbin/scutil', '--set', 'LocalHostName', \
                  str(newname.replace(' ', '-'))]
    for x in command:
        subprocess.call(command[x])
    progress("Set Machine Names")

def createuser():
    '''
    Creates new user based on Field Name if it does not already exist
    '''
    username = n.views['usernamefield'].stringValue()
    shortname = (sub("[^a-zA-Z]", "", username)).lower()
    if username == "":
        progress("Can not create user, Username Field is Empty!")
    else:
        if os.path.exists(os.path.join("/Users", shortname)):
            progress("User Already Exists!")
            return
        else:
            progress("Creating User")
            subprocess.check_output(["/usr/sbin/sysadminctl", "-addUser", \
                                    shortname, "-admin", "-fullName", username])
            subprocess.check_output(["/usr/bin/pwpolicy", "-u", shortname, \
            "-setpolicy", "newPasswordRequired=1"])
            progress("New User Created: ({0})\nHome dir:"
                     "/Users/{1}\nPWPolicy Set!".format(username, shortname))

def getmarketingmodel():
    '''
    Get reliable source for what a machine is. More human readable as well.
    '''
    modelidentifier = subprocess.check_output(["/usr/sbin/sysctl", "-n", "hw.model"]).strip()
    marketingmodel = readPlist("/System/Library/PrivateFrameworks/ServerInformation.framework/Resources/English.lproj/SIMachineAttributes.plist")[modelidentifier]["_LOCALIZABLE_"]["marketingModel"]
    return marketingmodel

def createmanifest():
    '''
    Create the manifest using munki enroll php script in repo.
    '''
    progress("")
    params = {}
    params["serial"] = get_hardware_serial()
    params["school"] = manifests[getmanifests()]
    if n.views['machinename'].stringValue() == "":
        progress("Machine Name is blank!\nPlease fill it in and try again!")
        return
    else:
        params["displayname"] = n.views['machinename'].stringValue()
    if n.views['usernamefield'].stringValue() == "":
        progress("Username field is blank!\nPlease fill it in and try again!")
        return
    else:
        params["user"] = n.views['usernamefield'].stringValue()
    params["notes"] = getmarketingmodel()
    overridebutton = n.views['manifestoverridecheckbox'].stringValue()
    if overridebutton == "0":
        params["override"] = "false"
    else:
        params["override"] = "true"
    encodedparams = urlencode(params)
    conn = httplib.HTTPConnection("munki.example.com")
    conn.request("GET", "/munki-enroll/enroll.php?{}".format(encodedparams))
    response = conn.getresponse()
    data = response.read()
    if "Override not set" in data:
        progress("Manfiest not created! If this is a re-imaged machine, "\
                 "please check override and try again!")
        return
    else:
        CFPreferencesSetValue("ClientIdentifier",
                              None, "/Library/Preferences/ManagedInstalls",
                              kCFPreferencesAnyUser,
                              kCFPreferencesAnyHost
                             )
        CFPreferencesSynchronize("/Library/Preferences/ManagedInstalls",
                                 kCFPreferencesAnyUser,
                                 kCFPreferencesAnyHost
                                )
        progress("Manifest Created!\nRemoved ClientIdentifier from Machine")

def main():
    '''
    Run this thing!
    '''
    n.attach(quitgui, 'quitbutton')
    n.attach(setmachinename, 'machinenamesetbutton')
    n.attach(createmanifest, 'manifestcreatebutton')
    n.attach(createuser, 'usercreatebutton')

    setmanifestchoices()
    getmachinename()
    n.run()

if __name__ == '__main__':
    main()
