# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

try:
    from _pyreport import *
except ImportError:
    from report._py3report import *

from report.io import TextIO, GTKIO, NewtIO

#Compatibility with report package:
# Author(s): Gavin Romig-Koch <gavin@redhat.com>
# ABRT Team

import os

SYSTEM_RELEASE_PATHS = ["/etc/system-release","/etc/redhat-release"]
SYSTEM_RELEASE_DEPS = ["system-release", "redhat-release"]

_hardcoded_default_product = ""
_hardcoded_default_version = ""

"""
def getProduct_fromRPM():
    try:
        import rpm
        ts = rpm.TransactionSet()
        for each_dep in SYSTEM_RELEASE_DEPS:
            mi = ts.dbMatch('provides', each_dep)
            for h in mi:
                if h['name']:
                    return h['name'].split("-")[0].capitalize()

        return ""
    except:
        return ""

def getVersion_fromRPM():
    try:
        import rpm
        ts = rpm.TransactionSet()
        for each_dep in SYSTEM_RELEASE_DEPS:
            mi = ts.dbMatch('provides', each_dep)
            for h in mi:
                if h['version']:
                    return str(h['version'])

        return ""
    except:
        return ""
"""

def getProduct_fromFILE():
    for each_path in SYSTEM_RELEASE_PATHS:
        if os.path.exists(each_path):
            file = None
            try:
                file = open(each_path, "r")
            except IOError as e:
                return ""

            content = file.read()
            if content.startswith("Red Hat Enterprise Linux"):
                return "Red Hat Enterprise Linux"

            if content.startswith("Fedora"):
                return "Fedora"

            i = content.find(" release")
            if i > -1:
                return content[0:i]

    return ""

def getVersion_fromFILE():
    for each_path in SYSTEM_RELEASE_PATHS:
        if os.path.exists(each_path):
            file = None
            try:
                file = open(each_path, "r")
            except IOError as e:
                return ""

            content = file.read()
            if content.find("Rawhide") > -1:
                return "rawhide"

            clist = content.split(" ")
            i = clist.index("release")
            return clist[i+1]
        else:
            return ""

def getProduct_fromPRODUCT():
    try:
        from pyanaconda import product
        return product.productName
    except:
        try:
            import product
            return product.productName
        except:
            return ""

def getVersion_fromPRODUCT():
    try:
        from pyanaconda import product
        return product.productVersion
    except:
        try:
            import product
            return product.productVersion
        except:
            return ""


def getProduct():
    """Attempt to determine the product of the running system at first attempt
       from the release configuration file or if the first attempt fails by
       asking anaconda
       Always return as a string.
    """
    for getter in (getProduct_fromFILE, getProduct_fromPRODUCT):
        product = getter()
        if product:
            return product

    return _hardcoded_default_product

def getVersion():
    """Attempt to determine the version of the running system at first attempt
       from the release configuration file or if the first attempt fails by
       asking anaconda
       Always return as a string.
    """
    for getter in (getVersion_fromFILE, getVersion_fromPRODUCT):
        version = getter()
        if version:
            return version

    return _hardcoded_default_version

def createAlertSignature(component, hashmarkername, hashvalue, summary, alertSignature, executable=None, package=None):
    pd = problem_data()
    pd.add("component", component)
    pd.add("hashmarkername", hashmarkername)
    pd.add("duphash", hashvalue)
    pd.add("reason", summary)
    pd.add("description", alertSignature)
    if executable:
        pd.add("executable", executable)
    if package:
        pd.add("package", package)
    pd.add_basics()

    return pd

# used in anaconda / python-meh
def createPythonUnhandledExceptionSignature(**kwargs):
    mandatory_args = ["component", "hashmarkername", "duphash", "reason",
                    "description"]

    for arg in mandatory_args:
        if arg not in kwargs:
            raise AttributeError("missing argument {0}".format(arg))

    pd = problem_data()
    for (key, value) in kwargs.iteritems():
        pd.add(key, value)
    product = getProduct()
    if product:
        pd.add("product", product)
    version = getVersion()
    if version:
        pd.add("version", version)
    #libreport expect the os_release as in /etc/redhat-release
    if (version and product):
        # need to add "release", parse_release() expects format "<product> release <version>"
        pd.add("os_release", product +" release "+ version)
    pd.add_basics() # adds required items
    pd.add_current_proccess() # adds executable and component

    return pd

"""
def report(cd, io_unused):
    state = run_event_state()
    #state.logging_callback = logfunc
    r = state.run_event_on_problem_data(cd, "report")
    return r
"""

def report(pd, io):

    flags = None
    if isinstance(io, TextIO.TextIO):
        flags = LIBREPORT_RUN_CLI
    elif isinstance(io, NewtIO.NewtIO):
        flags = LIBREPORT_WAIT  # wait for report to finish, so we can restore the screen
        flags |= LIBREPORT_RUN_NEWT # run newt first
        io.screen.suspend() # save the state of anaconda windows before we fork
        result = report_problem_in_memory(pd, flags)
        io.screen.resume() # restore the previously saved state
        return result

    result = report_problem(pd)
