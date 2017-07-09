#!/usr/bin/env python

# ***** BEGIN APACHE LICENSE BLOCK *****
#
# Copyright 2017 Ray Cardillo <cardillo.ray@gmail.com>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ***** END APACHE LICENCE BLOCK *****

import optparse
import os
import subprocess
import sys
from copy import copy
import inkex

try:
  from subprocess import DEVNULL
except ImportError:
  DEVNULL = open(os.devnull, 'w')

def checkForPath(command):
  return 0 == subprocess.call([ command, "--version" ], stdout=DEVNULL, stderr=DEVNULL, shell=True)

def error(msg):
  sys.stderr.write((unicode(msg) + "\n").encode("UTF-8"))
  sys.exit(1)

def export(svg, options):
  export_dpi( svg, options, options.baseDPI )

  if options.export2xDPI:
    export_dpi( svg, options, options.baseDPI * 2, "@2x" )

  if options.export4xDPI:
    export_dpi( svg, options, options.baseDPI * 4, "@4x" )

def export_dpi(svg, options, dpi, suffix=""):
  if not os.path.exists(options.outdir):
    os.makedirs(options.outdir)

  def export_resource(params, filename):
    call_params = ["inkscape",
                   "--without-gui",
                   "--export-dpi=%d" % dpi,
                   "--export-png=%s" % filename]

    if isinstance(params, list):
        call_params.extend(params)
    else:
        call_params.append(params)

    call_params.append(svg)

    subprocess.check_call(call_params, stdout=DEVNULL, stderr=subprocess.STDOUT, shell=True)

    if options.strip:
      subprocess.check_call([
                              "convert", "-antialias", "-strip", filename, filename
                            ], stdout=DEVNULL, stderr=subprocess.STDOUT, shell=True)
    if options.optimize:
      subprocess.check_call([
                              "optipng", "-quiet", "-clobber", "-o%d" % options.optimizeLevel, filename
                            ], stdout=DEVNULL, stderr=subprocess.STDOUT, shell=True)

  if options.source == '"selected_ids"':
    params = create_selection_params(options)

    for id in options.ids:
      current_params = ["--export-id=%s" % id]
      current_params.extend(params)
	  
      filename = "%s%s.png" % (id, suffix)
      filepath = os.path.join(options.outdir, filename)

      inkex.errormsg("exporting (%s) at %d DPI -> %s" % (id, dpi, filename))
      export_resource(current_params, filepath)

  else:
    filename = "%s%s.png" % (options.pageName, suffix)
    filepath = os.path.join(options.outdir, filename)

    inkex.errormsg("exporting (%s) at %d DPI -> %s" % (options.pageName, dpi, filename))
    export_resource("--export-area-page", filepath)

def create_selection_params(options):
    params = []
    if options.only_selected:
        params.append("--export-id-only")
    if options.transparent_background:
        params.append("-y 0")
    return params

parser = optparse.OptionParser(usage="usage: %prog [options] SVGfile", option_class=inkex.InkOption)
parser.add_option("--source", action="store", type="choice", choices=('"selected_ids"', '"page"'), help="Export by selected or entire page")
parser.add_option("--id", action="append", dest="ids", metavar="ID", help="ID attribute of objects to export, can be specified multiple times")
parser.add_option("--outdir", action="store", help="Output directory")
parser.add_option("--pageName", action="store", help="Page name (required when --source=page)")
parser.add_option("--only-selected", action="store", type="inkbool", help="Export only selected (without any background or other elements)")
parser.add_option("--transparent-background", action="store", type="inkbool", help="Transparent background")

parser.add_option("--baseDPI", action="store", type="int", help="Base DPI")
parser.add_option("--export2xDPI", action="store", type="inkbool", help="Export @2x Base DPI")
parser.add_option("--export4xDPI", action="store", type="inkbool", help="Export @4x Base DPI")

parser.add_option("--strip", action="store", type="inkbool", help="Use ImageMagick to reduce the image size")
parser.add_option("--optimize", action="store", type="inkbool", help="Use OptiPNG to reduce the image size")
parser.add_option("--optimizeLevel", action="store", type="int", help="OptiPNG optimization level")

(options, args) = parser.parse_args()
if len(args) != 1:
  parser.error("Expected exactly one argument, got %d" % len(args))
svg = args[0]

options.outdir = os.path.expanduser(options.outdir)
if options.outdir is None:
  error("No output directory specified")
if not os.path.isdir(options.outdir):
  error("Bad output directory specified:\n'%s' is no dir" % options.outdir)
if not os.access(options.outdir, os.W_OK):
  error("Bad output directory specified:\nCould not write to '%s'" % options.outdir)

if options.source not in ('"selected_ids"', '"page"'):
  error("Select something to export (selected items or whole page)")
if options.source == '"selected_ids"' and options.ids is None:
  error("Select at least one item to export")
if options.source == '"page"' and not options.pageName:
  error("Please enter a page name")

if not checkForPath("inkscape"):
  error("Make sure you have 'inkscape' on your PATH")
if options.strip and not checkForPath("convert"):
  error("Make sure you have 'convert' on your PATH if you want to reduce the image size using ImageMagick")
if options.optimize and not checkForPath("optipng"):
  error("Make sure you have 'optipng' on your PATH if you want to reduce the image size using OptiPNG")

export(svg, options)

inkex.errormsg("done")