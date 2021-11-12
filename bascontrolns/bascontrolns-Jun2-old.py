# For HTML POST requests.
import requests
# For Python 3.x enumerated types.
from enum import Enum
# For XML parsing.
import xml.etree.ElementTree as et
# For time functions.
import time


###############################################################################
#
class Platform(Enum):

    """BAScontrol platform (hardware) types"""

    BASC_NONE = 0
    BASC_20  = 0
    BASC_PI  = 1
    BASC_AO  = 2
    BASC_PO  = 3
    BASC_ED  = 4


###############################################################################
#
def getUrl(sIpAddress):

    """Returns the full cgi URL of the target"""

    return 'http://' + sIpAddress + '/cgi-bin/xml-cgi'


###############################################################################
#
def getModel(url , secTimeout):

    """Uses RDOM to get the model of the target (BAScontrol22, etc.)"""

    model = 'Error'
    req = '<rdom fcn="get" doc="sts" path="model"/>'
    try:
        rsp = requests.post(url , data = req , timeout = secTimeout)
        if (rsp.status_code == 200):
            root = et.fromstring(rsp.text)
            if root.attrib['rsp'] == 'ack':
                model = root.text
    except OSError:
        # Timeout.
        pass
    return model


###############################################################################
#
def getPlatform(sModel):

    """Returns the Platform type given the model (BASconrol22, etc.)"""

    eRetval = Platform.BASC_NONE
    if sModel.find('20') != -1:
        eRetval = Platform.BASC_20
    elif sModel.find('6R') != -1:
        eRetval = Platform.BASC_PI
    elif sModel.find('PI') != -1:
        eRetval = Platform.BASC_PO
    elif sModel.find('2AO') != -1:
        eRetval = Platform.BASC_AO 
    elif sModel.find('6') != -1:
        eRetval = Platform.BASC_ED       
    return eRetval


###############################################################################
#
# BAScontrol device class.
# Uses RDOM to get/set the present value for all objects on the target that
# are part of the configuration file; UI, BI, AO, BO, and VT's.
#
class Device:

    """BAScontrol device class: Initialize with IP address"""

    def __init__(self , sIpAddress , bInit=True):

        # Assume failure.
        self.online = False
        self.ePlatform = Platform.BASC_NONE
        self.sModel = 'Error'
        # Assign complete IP address.
        self.sFullUrl = getUrl(sIpAddress)

        # Default timeout and retry interval.
        self.timeout = 2
        self.retryInterval = 15
        self.nextRetry = 0

        # Assign default values.
        self.vtQty = 24
        self.uiQty = 0
        self.biQty = 0
        self.aoQty = 0
        self.boQty = 0
        #
        self.uiBase = 0
        self.biBase = 0
        self.aoBase = 0
        self.boBase = 0
        self.vtBase = 0

        # Return if we're not initializing right away.
        if not bInit:
            return
        # Set up the device.
        self.initialize()

    ###########################################################################
    #
    def initialize(self):

        """Checks online status and does setup()"""

        # Is target online?
        if self.isOnline():
            # Setup our data.
            self.setup()
            return True

        # Not online.
        return False

    ###########################################################################
    #
    def isOnline(self):

        """Returns True if the target is online, False otherwise"""

        if self.online:
            return True

        self.sModel = getModel(self.sFullUrl , self.timeout)
        if self.sModel == 'Error':
            self.online = False
            self.ePlatform = Platform.BASC_NONE
            self.retryInterval = int(time.time())+self.retryInterval
        else:
            self.online = True
            self.ePlatform = getPlatform(self.sModel)
            self.retryInterval = 0
        return self.online

    ###########################################################################
    #
    def setup(self):

        """Sets device object quantities per the model"""

        # Get target platform.
        self.ePlatform = getPlatform(self.sModel)
        # Assign the number of IO.
        if self.ePlatform == Platform.BASC_20:
            self.uiQty = 6
            self.biQty = 0
            self.aoQty = 0
            self.boQty = 6
        elif self.ePlatform == Platform.BASC_PI:
            self.uiQty = 6
            self.biQty = 0
            self.aoQty = 0
            self.boQty = 6
            self.vtQty = 24
        elif self.ePlatform == Platform.BASC_AO:
            self.uiQty = 6
            self.biQty = 0
            self.aoQty = 2
            self.boQty = 4
        elif self.ePlatform == Platform.BASC_PO:
            self.uiQty = 6
            self.biQty = 0
            self.aoQty = 0
            self.boQty = 6
            self.vtQty = 24
        elif self.ePlatform == Platform.BASC_ED:
            self.uiQty = 6
            self.biQty = 0
            self.aoQty = 0
            self.boQty = 6
            self.vtQty = 24        
            # Assign 0-based index values.
        self.uiBase = 0
        self.biBase = self.uiQty
        self.aoBase = self.biBase + self.biQty
        self.boBase = self.aoBase + self.aoQty
        self.vtBase = self.boBase + self.boQty

    ###########################################################################
    #
    def readObject(self , iIndex):

        """Returns response text if success, None if failure"""

        # If not online.
        if not self.online:
            # If retry period has expired.
            if int(time.time()) >= self.nextRetry:
                # If we're still offline.
                if not self.isOnline():
                    # New retry time has been set.
                    return None
            # Else need to wait.
            else:
                return None

        # Assume failure.
        retval = None
        # XML read request string.
        req = '<rdom fcn="get" doc="rtd" path="obj[' + str(iIndex) + ']/val_scl"/>'
        # Try to execute the POST.
        try:
            rsp = requests.post(self.sFullUrl, data=req , timeout=self.timeout)
            # If good HTML response.
            if (rsp.status_code == 200):
                root = et.fromstring(rsp.text)
                if root.attrib['rsp'] == 'ack':
                    retval = root.text
            else:
                # Something there, but not BAScontrol.
                self.online = False
        except OSError:
            # Timeout.
            self.online = False
        # If we were taken offline.
        if not self.online:
            # Set for retry.
            self.nextRetry = int(time.time())+self.retryInterval
            # Raise an exception.
            ###raise IOError
            # NOT REACHED
        # And return.
        return retval 

    ###########################################################################
    #
    # This does two POST operations:
    #   1. Checks ws_control to see if it's under wire sheet control.
    #   2. Executes the write if not under wire sheet control.
    #
    def writeObject(self , iIndex , value):

        """Writes the present value of an object using 0-based index"""

        # If not online.
        if not self.online:
            # If retry period has expired.
            if int(time.time()) >= self.nextRetry:
                # If we're still offline.
                if not self.isOnline():
                    # New retry time has been set.
                    return -1
            # Else need to wait.
            else:
                return -1

        # Assume failure.
        retval = -1
        # XML wire sheet control request string.
        req = '<rdom fcn="get" doc="rtd" path="obj[' + str(iIndex) + ']/ws_control"/>'
        # Try to execute first POST request.
        try:
            # Execute POST and get response.
            rsp = requests.post(self.sFullUrl, data=req , timeout=self.timeout)
            # If good HTML response.
            if (rsp.status_code == 200):
                # Parse XML.
                root = et.fromstring(rsp.text)
                # If request was ACK'd.
                if root.attrib['rsp'] == 'ack':
                    # If point is under wire sheet control.
                    if root.text == '1':
                        # We can't write.
                        return -1
                # Else we were NAK'd; SERIOUS PROBLEM
                else:
                    return -1
                #
                # If we get here, we can proceed with the write operation.
                #
                # XML write request string.
                req = '<rdom fcn="set" doc="rtd" path="obj[' + str(iIndex) + ']/val_scl">' + str(value) + '</rdom>'
                # Try to execute POST request.
                try:
                    # Execute POST and get response.
                    rsp = requests.post(self.sFullUrl, data=req , timeout=self.timeout)
                    # If good HTML response.
                    if (rsp.status_code == 200):
                        # Parse XML.
                        root = et.fromstring(rsp.text)
                        #######################################################
                        # This is the only place we can return success.
                        #######################################################
                        if root.attrib['rsp'] == 'ack':
                            retval = 0
                    else:
                        # Something there, but not BAScontrol.
                        self.online = False
                except OSError:
                    # Timeout.
                    self.online = False
            else:
                # Something there, but not BAScontrol.
                self.online = False
        except OSError:
            # Timeout.
            self.online = False
        # If we were taken offline.
        if not self.online:
            # Set for retry.
            self.nextRetry = int(time.time())+self.retryInterval
            # Raise an exception.
            ###raise IOError
            # NOT REACHED
        # And return.
        return retval

    ###########################################################################
    #
    def universalInput(self , iIndex):

        """Reads a universal input using 1-based index (UI1..)"""

        # Sanity check.
        if (iIndex <= 0) or (iIndex > self.uiQty) or (self.ePlatform == Platform.BASC_NONE):
            return None
        # Get 0-based index.
        index = int(iIndex - 1)
        # Execute read.
        value = self.readObject(index)
        # And return.
        return None if value == None else float(value)
        

    ###########################################################################
    #
    def binaryInput(self , iIndex):

        """Reads a binary input using 1-based index (BI1..)"""

        # Sanity check.
        if (iIndex <= 0) or (iIndex > self.biQty) or (self.ePlatform == Platform.BASC_NONE):
            return None
        # Get 0-based index.
        index = int(iIndex - 1 + self.biBase)
        # Execute read.
        value = self.readObject(index)
        # And return.
        return None if value == None else int(value)

    ###########################################################################
    #
    def analogOutput(self , iIndex , fValue = None):

        """Reads or writes an analog output using 1-based index (AO1..)"""

        # Sanity check.
        if (iIndex <= 0) or (iIndex > self.aoQty) or (self.ePlatform == Platform.BASC_NONE):
            return None
        # Get 0-based index.
        index = int(iIndex - 1 + self.aoBase)
        # If reading.
        if fValue == None:
            # Execute read.
            value = self.readObject(index)
            # And return.
            return None if value == None else float(value)
        # Else writing.
        return self.writeObject(index , fValue)

    ###########################################################################
    #
    def binaryOutput(self, iIndex, iValue=None):

        """Reads or writes an binary output using 1-based index (BO1..)"""

        # Sanity check.
        if (iIndex <= 0) or (iIndex > self.boQty) or (self.ePlatform == Platform.BASC_NONE):
            return None
        # Get 0-based index.
        index = int(iIndex - 1 + self.boBase)
        # If reading.
        if iValue == None:
            # Execute read.
            value = self.readObject(index)
            # Return if failure.
            if value == None:
                return None
            # Return with integer value.
            return 0 if int(value) == 0 else 1
        # Else writing.
        return self.writeObject(index, iValue)

    ###########################################################################
    #
    def virtualValue(self , iIndex , bIsBinary , aValue = None):

        """Reads or writes a virtual point using 1-based index (BO1..)"""

        # Sanity check.
        if (iIndex <= 0) or (iIndex > self.vtQty) or (self.ePlatform == Platform.BASC_NONE):
            return None
        # Get 0-based index.
        index = int(iIndex - 1 + self.vtBase)
        # If reading.
        if aValue == None:
            # Execute read.
            value = self.readObject(index)
            # Return if failure.
            if value == None:
                return None
            # Return with value.
            return int(value) if bIsBinary else float(value)
        # Else writing.
        return self.writeObject(index , aValue)
