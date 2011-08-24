#!/usr/bin/env python

import os
import shutil
import sys
import optparse
import subprocess

def stripLine(line):
    i = line.find("#")
    if i >= 0:
	line = line[:i]
    return line.strip()

def getOrder():
    pkgOrderFile = open("package-order", "r")
    pkgOrderList = []
    for line in pkgOrderFile:
	name = stripLine(line)
	if name:
	    pkgOrderList.append(name)
    pkgOrderFile.close()
    return pkgOrderList

def getVersions(pkgOrder):
    pkgVersionDict = {"default": None}
    pkgVersionFile = open("package-versions", "r")
    for line in pkgVersionFile:
	line = stripLine(line)
	if not line: continue
	name, version = stripLine(line).split("=")
	name = name.strip()
	i = version.find(":")
	if i < 0:
	    version = version.strip()
	    if not version:
		pkgVersionDict[name] = None
		continue
	    else:
		revision = "HEAD"
	else:
	    revision = version[i+1:].strip()
	    version = version[:i].strip()
	pkgVersionDict[name] = (version, revision)
    return pkgVersionDict

def getDefaultDmsUrl():
    if dms_url is None:
	try:
	    dms_url = os.environ["LSST_DMS"]
	except KeyError:
	    dms_url = "%/DMS" % os.environ.get("LSST_SVN", "svn+ssh://svn.lsstcorp.org")    

def checkout(root, dms_url=None, dry_run=False, update=False, replace=False, remove=False, **kw):
    pkgOrder = getOrder()
    pkgVersions = getVersions(pkgOrder)
    if dms_url is None:
	dms_url = getDefaultDmsUrl()
    for pkgName in pkgOrder:
	pkgDir = os.path.join(root, pkgName)
	pkgVersion = pkgVersions.get(pkgName, pkgVersions["default"])
	if pkgVersion is None:
	    if os.path.exists(pkgDir):
		if remove:
		    sys.stderr.write("Removing unmanaged directory %s\n" % pkgDir)
		    if not dry_run: shutil.rmtree(pkgDir)
		else:
		    sys.stderr.write("Ignoring unmanaged directory %s\n" % pkgDir)
	else:
	    pkgUrl = "%s/%s/%s@%s" % (dms_url, "/".join(pkgName.split("_")), pkgVersion[0], pkgVersion[1])
	    if os.path.exists(pkgDir):
		if update:
		    sys.stderr.write("Switching/updating %s to %s\n" % (pkgDir, pkgUrl))
		    if not dry_run:
			cmd = "svn switch %s %s" % (pkgUrl, pkgDir)
			if os.system(cmd) != 0:
			    raise OSError("Failure in external command: '%s'" % cmd)
		elif replace:
		    sys.stderr.write("Replacing %s with new checkout from %s\n" % (pkgDir, pkgUrl))
		    if not dry_run:
			shutil.rmtree(pkgDir)
			cmd = "svn co %s %s" % (pkgUrl, pkgDir)
			if os.system(cmd) != 0:
			    raise OSError("Failure in external command: '%s'" % cmd)
		else:
		    sys.stderr.write("Using existing directory %s unchanged\n" % pkgDir)
	    else:
		sys.stderr.write("Checking out %s from %s\n" % (pkgDir, pkgUrl))
		if not dry_run:
		    cmd = "svn co %s %s" % (pkgUrl, pkgDir)
		    if os.system(cmd) != 0:
			raise OSError("Failure in external command: '%s'" % cmd)
		    
def update(root, dms_url=None, dry_run=False, **kw):
    pkgOrder = getOrder()
    pkgVersions = getVersions(pkgOrder)
    for pkgName in pkgOrder:
	pkgVersion = pkgVersions.get(pkgName, pkgVersions["default"])
	pkgDir = os.path.join(root, pkgName)
	if pkgVersion is None:
	    if os.path.exists(pkgDir):
		sys.stderr.write("Ignoring unmanaged directory %s\n" % pkgDir)
	    continue
	if not os.path.exists(pkgDir):
	    sys.stderr.write("WARNING: skipping nonexistent directory %s\n" % pkgDir)
	sys.stderr.write("Updating %s\n" % pkgDir)
	if not dry_run:
	    cmd = "svn update %s" % pkgDir
	    if os.system(cmd) != 0:
		raise OSError("Failure in external command: '%s'" % cmd)

def metasetup(root, dry_run=False, **kw):
    pkgOrder = getOrder()
    pkgVersions = getVersions(pkgOrder)
    for pkgName in pkgOrder:
	pkgVersion = pkgVersions.get(pkgName, pkgVersions["default"])
	pkgDir = os.path.join(root, pkgName)
	if pkgVersion is None:
	    if os.path.exists(pkgDir):
		sys.stderr.write("Ignoring unmanaged directory %s\n" % pkgDir)
	    continue
	if not os.path.exists(pkgDir):
	    sys.stderr.write("WARNING: skipping nonexistent directory %s\n" % pkgDir)
	sys.stderr.write("Setting up %s\n" % pkgDir)
	if not dry_run:
	    print "setup -k -r %s;" % pkgDir

def build(root, dry_run=False, scons_args="", **kw):
    pkgOrder = getOrder()
    pkgVersions = getVersions(pkgOrder)
    for pkgName in pkgOrder:
	pkgVersion = pkgVersions.get(pkgName, pkgVersions["default"])
	pkgDir = os.path.join(root, pkgName)
	if pkgVersion is None:
	    if os.path.exists(pkgDir):
		sys.stderr.write("Ignoring unmanaged directory %s\n" % pkgDir)
	    continue
	if not os.path.exists(pkgDir):
	    sys.stderr.write("WARNING: skipping nonexistent directory %s\n" % pkgDir)
	sys.stderr.write("Building %s\n" % pkgDir)
	if not dry_run:
	    cmd = "cd %s && scons %s" % (pkgDir, scons_args)
	    if os.system(cmd) != 0:
		raise OSError("Failure in external command: '%s'" % cmd)	    

def main(args):
    usage = "Usage:\n"\
	    "        manage.py [global options] command\n\n"\
	    "Supported commands are:\n"\
	    "        checkout         Checkout a new stack from SVN or switch URLs\n"\
	    "\n"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-r", "--root", type="string", metavar="DIR", default=".", dest="root",
		      help="Root directory for stack [default: %default]")
    parser.add_option("-n", "--dry-run", action="store_true", metavar="DIR", default=False, dest="dry_run",
		      help="Show actions but do not carry them out")
    parser.add_option("--dms-url", type="string", metavar="DIR", default=None, dest="dms_url",
		      help="SVN URL for DMS packages (usually $LSST_DMS)")
    checkoutGroup = optparse.OptionGroup(parser, "additional options for 'checkout'")
    checkoutGroup.add_option("--update", action="store_true", default=False, dest="update",
			     help="If a managed directory exists, update it with svn switch.")
    checkoutGroup.add_option("--replace", action="store_true", default=False, dest="replace",
			     help="If a managed directory exists, remove it and checkout again.")
    checkoutGroup.add_option("--remove", action="store_true", default=False, dest="remove",
			     help="Delete unmanaged package directories.")
    parser.add_option_group(checkoutGroup)
    buildGroup = optparse.OptionGroup(parser, "additional options for 'build'")
    buildGroup.add_option("--scons-args", type="string", default="", dest="scons_args",
			  help="Additional arguments to pass to SCons")
    parser.add_option_group(buildGroup)
    options, args = parser.parse_args(args)
    if options.update and options.remove:
	parser.error("--update and --replace are mutually exclusive")
    optDict = {"root": options.root, "dry_run": options.dry_run, "dms_url": options.dms_url}
    try:
	cmd = args[1]
    except IndexError:
	parser.error("First positional argument must be a valid command")
    if cmd == "checkout":
	optDict.update(update=options.update, replace=options.replace, remove=options.remove)
	checkout(**optDict)
    elif cmd == "update":
	update(**optDict)
    elif cmd == "metasetup":
	metasetup(**optDict)
    elif cmd == "build":
	optDict.update(scons_args=options.scons_args)
	build(**optDict)
    else:
	parser.error("First positional argument must be a valid command (got %s)" % cmd)
    return 0

if __name__ == "__main__":
    main(sys.argv)
