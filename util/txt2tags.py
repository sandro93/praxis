#!/usr/bin/env python
# txt2tags - generic text conversion tool
# http://txt2tags.org
#
# Copyright 2001-2010 Aurelio Jargas
#
# License: http://www.gnu.org/licenses/gpl-2.0.txt
# Subversion: http://svn.txt2tags.org
# Bug tracker: http://bugs.txt2tags.org
#
########################################################################
#
#   BORING CODE EXPLANATION AHEAD
#
# Just read it if you wish to understand how the txt2tags code works.
#
########################################################################
#
# The code that [1] parses the marked text is separated from the
# code that [2] insert the target tags.
#
#   [1] made by: def convert()
#   [2] made by: class BlockMaster
#
# The structures of the marked text are identified and its contents are
# extracted into a data holder (Python lists and dictionaries).
#
# When parsing the source file, the blocks (para, lists, quote, table)
# are opened with BlockMaster, right when found. Then its contents,
# which spans on several lines, are feeded into a special holder on the
# BlockMaster instance. Just when the block is closed, the target tags
# are inserted for the full block as a whole, in one pass. This way, we
# have a better control on blocks. Much better than the previous line by
# line approach.
#
# In other words, whenever inside a block, the parser *holds* the tag
# insertion process, waiting until the full block is read. That was
# needed primary to close paragraphs for the XHTML target, but
# proved to be a very good adding, improving many other processing.
#
# -------------------------------------------------------------------
#
# These important classes are all documented:
# CommandLine, SourceDocument, ConfigMaster, ConfigLines.
#
# There is a RAW Config format and all kind of configuration is first
# converted to this format. Then a generic method parses it.
#
# These functions get information about the input file(s) and take
# care of the init processing:
# get_infiles_config(), process_source_file() and convert_this_files()
#
########################################################################

#XXX Python coding warning
# Avoid common mistakes:
# - do NOT use newlist=list instead newlist=list[:]
# - do NOT use newdic=dic   instead newdic=dic.copy()
# - do NOT use dic[key]     instead dic.get(key)
# - do NOT use del dic[key] without key in dic before

#XXX Smart Image Align don't work if the image is a link
# Can't fix that because the image is expanded together with the
# link, at the linkbank filling moment. Only the image is passed
# to parse_images(), not the full line, so it is always 'middle'.

#XXX Paragraph separation not valid inside Quote
# Quote will not have <p></p> inside, instead will close and open
# again the <blockquote>. This really sux in CSS, when defining a
# different background color. Still don't know how to fix it.

#XXX TODO (maybe)
# New mark or macro which expands to an anchor full title.
# It is necessary to parse the full document in this order:
#  DONE  1st scan: HEAD: get all settings, including %!includeconf
#  DONE  2nd scan: BODY: expand includes & apply %!preproc
#        3rd scan: BODY: read titles and compose TOC info
#        4th scan: BODY: full parsing, expanding [#anchor] 1st
# Steps 2 and 3 can be made together, with no tag adding.
# Two complete body scans will be *slow*, don't know if it worths.
# One solution may be add the titles as postproc rules


##############################################################################

# User config (1=ON, 0=OFF)

USE_I18N    = 1   # use gettext for i18ned messages?        (default is 1)
COLOR_DEBUG = 1   # show debug messages in colors?          (default is 1)
BG_LIGHT    = 0   # your terminal background color is light (default is 0)
HTML_LOWER  = 0   # use lowercased HTML tags instead upper? (default is 0)

##############################################################################


# These are all the core Python modules used by txt2tags (KISS!)
import re
import os
import sys
import locale
import time  # %%date, %%mtime
import getopt
import textwrap
import csv
import string
import struct
import unicodedata
# import urllib  # read remote files (URLs) -- postponed, see issue 96
# import email  # %%mtime for remote files -- postponed, see issue 96


# Program information
my_url = 'http://txt2tags.org'
my_name = 'txt2tags'
my_email = 'verde@aurelio.net'
my_revision = '$Revision$'  # automatic, from SVN
my_version = '2.6'

# Add SVN revision number to version: 1.2.345
my_version = '%s.%s' % (my_version, re.sub(r'\D', '', my_revision))

# i18n - just use if available
if USE_I18N:
    try:
        import gettext
        # If your locale dir is different, change it here
        cat = gettext.Catalog('txt2tags', localedir='/usr/share/locale/')
        _ = cat.gettext
    except:
        _ = lambda x: x
else:
    _ = lambda x: x

# FLAGS   : the conversion related flags  , may be used in %!options
# OPTIONS : the conversion related options, may be used in %!options
# ACTIONS : the other behavior modifiers, valid on command line only
# MACROS  : the valid macros with their default values for formatting
# SETTINGS: global miscellaneous settings, valid on RC file only
# NO_TARGET: actions that don't require a target specification
# NO_MULTI_INPUT: actions that don't accept more than one input file
# CONFIG_KEYWORDS: the valid %!key:val keywords
#
# FLAGS and OPTIONS are configs that affect the converted document.
# They usually have also a --no-<option> to turn them OFF.
#
# ACTIONS are needed because when handling multiple input files, strange
# behavior may occur, such as use command line interface for the
# first file and gui for the second. There is no --no-<action>.
# Options --version and --help inside %!options are odd.
#
FLAGS = {
    'headers': 1,
    'enum-title': 0,
    'mask-email': 0,
    'toc-only': 0,
    'toc': 0,
    'qa': 0,
    'rc': 1,
    'css-sugar': 0,
    'css-inside': 0,
    'quiet': 0,
    'slides': 0,
    'spread': 0,
    'web': 0,
    'fix-path': 0,
    'embed-images': 0,
    }
OPTIONS = {
    'target': '',
    'toc-level': 3,
    'toc-title': '',
    'style': '',
    'infile': '',
    'outfile': '',
    'encoding': '',
    'config-file': '',
    'split': 0,
    'lang': '',
    'width': 0,
    'height': 0,
    'chars': '',
    'show-config-value': '',
    'template': '',
    'dirname': '',  # internal use only
    }
ACTIONS = {
    'help': 0,
    'version': 0,
    'gui': 0,
    'verbose': 0,
    'debug': 0,
    'dump-config': 0,
    'dump-source': 0,
    'targets': 0,
    }
MACROS = {
    # date
    'date': '%Y%m%d',
    'mtime': '%Y%m%d',
    # files
    'infile': '%f',
    'currentfile': '%f',
    'outfile': '%f',
    # app
    'appurl': '',
    'appname': '',
    'appversion': '',
    # conversion
    'target': '',
    'cmdline': '',
    'encoding': '',
    # header
    'header1': '',
    'header2': '',
    'header3': '',
    # Creative Commons license
    'cc': '',
    }
SETTINGS = {}  # for future use
NO_TARGET = [
    'help',
    'version',
    'gui',
    'toc-only',
    'dump-config',
    'dump-source',
    'targets',
    ]
NO_MULTI_INPUT = [
    'gui',
    'dump-config',
    'dump-source'
    ]
CONFIG_KEYWORDS = [
    'cc',
    'target',
    'encoding',
    'style',
    'stylepath',  # internal use only
    'options',
    'preproc',
    'postproc',
    'postvoodoo',
    'guicolors',
    ]


TARGET_NAMES = {
  'txt2t'  : _('Txt2tags document'),
  'html'   : _('HTML page'),
  'html5'  : _('HTML5 page'),
  'xhtml'  : _('XHTML page'),
  'xhtmls' : _('XHTML Strict page'),
  'sgml'   : _('SGML document'),
  'dbk'    : _('DocBook document'),
  'tex'    : _('LaTeX document'),
  'lout'   : _('Lout document'),
  'man'    : _('UNIX Manual page'),
  'mgp'    : _('MagicPoint presentation'),
  'wiki'   : _('Wikipedia page'),
  'gwiki'  : _('Google Wiki page'),
  'doku'   : _('DokuWiki page'),
  'pmw'    : _('PmWiki page'),
  'moin'   : _('MoinMoin page'),
  'pm6'    : _('PageMaker document'),
  'txt'    : _('Plain Text'),
  'aat'    : _('ASCII Art Text'),
  'aap'    : _('ASCII Art Presentation'),
  'aas'    : _('ASCII Art Spreadsheet'),
  'aatw'   : _('ASCII Art Text Web'),
  'aapw'   : _('ASCII Art Presentation Web'),
  'aasw'   : _('ASCII Art Spreadsheet Web'),
  'adoc'   : _('AsciiDoc document'),
  'rst'    : _('ReStructuredText document'),
  'csv'    : _('CSV spreadsheet'),
  'ods'    : _('Open Document Spreadsheet'),
  'creole' : _('Creole 1.0 document'),
  'md'     : _('Markdown document'),
  'bbcode' : _('BBCode document'),
  'red'    : _('Redmine Wiki page'),
  'spip'   : _('SPIP article'),
  'rtf'    : _('RTF document'),
}
TARGETS = list(TARGET_NAMES.keys())
TARGETS.sort()


TARGET_TYPES = {
  'html'   : (_('HTML'), ('html', 'html5', 'xhtml', 'xhtmls', 'aatw', 'aapw', 'aasw')),
  'wiki'   : (_('WIKI'), ('txt2t', 'wiki', 'gwiki', 'doku', 'pmw', 'moin', 'adoc', 'rst', 'creole', 'md', 'bbcode', 'red', 'spip')),
  'office' : (_('OFFICE'), ('sgml', 'dbk', 'tex', 'lout', 'mgp', 'pm6', 'csv', 'ods', 'rtf')),
  'text'   : (_('TEXT'), ('man', 'txt', 'aat', 'aap', 'aas')),
}


DEBUG = 0     # do not edit here, please use --debug
VERBOSE = 0   # do not edit here, please use -v, -vv or -vvv
QUIET = 0     # do not edit here, please use --quiet
GUI = 0       # do not edit here, please use --gui
AUTOTOC = 1   # do not edit here, please use --no-toc or %%toc

DFT_TEXT_WIDTH   = 72  # do not edit here, please use --width
DFT_SLIDE_WIDTH  = 80  # do not edit here, please use --width
DFT_SLIDE_HEIGHT = 25  # do not edit here, please use --height

# ASCII Art config
AA_KEYS = 'corner border side bar1 bar2 level2 level3 level4 level5 bullet hhead vhead'.split()
AA_VALUES = '+-|-==-^"-=$'  # do not edit here, please use --chars
AA = dict(list(zip(AA_KEYS, AA_VALUES)))
AA_COUNT = 0
AA_TITLE = ''
AA_MARKS = []
AA_QA = """       ________
   /#**TXT2TAGS**#\\
 /#####/      \####CC\\
/###/            \#BY#|
^-^               |NC#|
                  /SA#|
               /#####/
            /#####/
          /####/
         /###/
        |###|
        |###|
         \o/
          
         ___
        F2.7G
         (C)""".split('\n')

# ReStructuredText config
# http://docs.python.org/release/2.7/documenting/rest.html#sections
RST_KEYS = 'title level1 level2 level3 level4 level5 bar1 bullet'.split()
RST_VALUES = '#*=-^"--'  # do not edit here, please use --chars
RST = dict(list(zip(RST_KEYS, RST_VALUES)))

RC_RAW = []
CMDLINE_RAW = []
CONF = {}
BLOCK = None
TITLE = None
regex = {}
TAGS = {}
rules = {}

# Gui globals
askopenfilename = None
showinfo = None
showwarning = None
showerror = None

lang = 'english'
TARGET = ''

STDIN = STDOUT = '-'
MODULEIN = MODULEOUT = '-module-'
ESCCHAR   = '\x00'
SEPARATOR = '\x01'
LISTNAMES = {'-': 'list', '+': 'numlist', ':': 'deflist'}
LINEBREAK = {'default': '\n', 'win': '\r\n', 'mac': '\r'}

# Platform specific settings
LB = LINEBREAK.get(sys.platform[:3]) or LINEBREAK['default']

VERSIONSTR = _("%s version %s <%s>") % (my_name, my_version, my_url)


def Usage():
    fmt1 = "%4s  %-15s %s"
    fmt2 = "%4s, %-15s %s"
    return '\n'.join([
        '',
        _("Usage: %s [OPTIONS] [infile.t2t ...]") % my_name,
        '',
        fmt1 % (''  , '--targets'      , _("print a list of all the available targets and exit")),
        fmt2 % ('-t', '--target=TYPE'  , _("set target document type. currently supported:")),
        fmt1 % (''  , ''               , ', '.join(TARGETS[:8]) + ','),
        fmt1 % (''  , ''               , ', '.join(TARGETS[8:17]) + ','),
        fmt1 % (''  , ''               , ', '.join(TARGETS[17:26]) + ','),
        fmt1 % (''  , ''               , ', '.join(TARGETS[26:])),
        fmt2 % ('-i', '--infile=FILE'  , _("set FILE as the input file name ('-' for STDIN)")),
        fmt2 % ('-o', '--outfile=FILE' , _("set FILE as the output file name ('-' for STDOUT)")),
        fmt1 % (''  , '--encoding=ENC' , _("inform source file encoding (UTF-8, iso-8859-1, etc)")),
        fmt1 % (''  , '--toc'          , _("add an automatic Table of Contents to the output")),
        fmt1 % (''  , '--toc-title=S'  , _("set custom TOC title to S")),
        fmt1 % (''  , '--toc-level=N'  , _("set maximum TOC level (depth) to N")),
        fmt1 % (''  , '--toc-only'     , _("print the Table of Contents and exit")),
        fmt2 % ('-n', '--enum-title'   , _("enumerate all titles as 1, 1.1, 1.1.1, etc")),
        fmt1 % (''  , '--style=FILE'   , _("use FILE as the document style (like HTML CSS)")),
        fmt1 % (''  , '--css-sugar'    , _("insert CSS-friendly tags for HTML/XHTML")),
        fmt1 % (''  , '--css-inside'   , _("insert CSS file contents inside HTML/XHTML headers")),
        fmt1 % (''  , '--embed-images' , _("embed image data inside HTML, html5, xhtml, RTF, aat and aap documents")),
        fmt2 % ('-H', '--no-headers'   , _("suppress header and footer from the output")),
        fmt2 % ('-T', '--template=FILE', _("use FILE as the template for the output document")),
        fmt1 % (''  , '--mask-email'   , _("hide email from spam robots. x@y.z turns <x (a) y z>")),
        fmt1 % (''  , '--width=N'      , _("set the output's width to N columns (used by aat, aap and aatw targets)")),
        fmt1 % (''  , '--height=N'     , _("set the output's height to N rows (used by aap target)")),
        fmt1 % (''  , '--chars=S'      , _("set the output's chars to S (used by all aa targets and rst)")),
        fmt1 % (''  , ''               , _("aa default " + AA_VALUES + " rst default " + RST_VALUES)),
        fmt2 % ('-C', '--config-file=F', _("read configuration from file F")),
        fmt1 % (''  , '--fix-path'     , _("fix resources path (image, links, CSS) when needed")),
        fmt1 % (''  , '--gui'          , _("invoke Graphical Tk Interface")),
        fmt2 % ('-q', '--quiet'        , _("quiet mode, suppress all output (except errors)")),
        fmt2 % ('-v', '--verbose'      , _("print informative messages during conversion")),
        fmt2 % ('-h', '--help'         , _("print this help information and exit")),
        fmt2 % ('-V', '--version'      , _("print program version and exit")),
        fmt1 % (''  , '--dump-config'  , _("print all the configuration found and exit")),
        fmt1 % (''  , '--dump-source'  , _("print the document source, with includes expanded")),
        '',
        _("Example:"),
        "     %s -t html --toc %s" % (my_name, _("file.t2t")),
        '',
        _("The 'no-' prefix disables the option:"),
        '     --no-toc, --no-style, --no-enum-title, ...',
        '',
        _("By default, converted output is saved to 'infile.<target>'."),
        _("Use --outfile to force an output file name."),
        _("If  input file is '-', reads from STDIN."),
        _("If output file is '-', dumps output to STDOUT."),
        '',
        my_url,
        '',
    ])


##############################################################################


# Here is all the target's templates
# You may edit them to fit your needs
#  - the %(HEADERn)s strings represent the Header lines
#  - the %(STYLE)s string is changed by --style contents
#  - the %(ENCODING)s string is changed by --encoding contents
#  - if any of the above is empty, the full line is removed
#  - use %% to represent a literal %
#
HEADER_TEMPLATE = {
    'aat': """\
""",
    'csv': """\
""",
    'rst': """\
""",
    'ods': """<?xml version='1.0' encoding='UTF-8'?>
<office:document xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" office:version="1.1" office:mimetype="application/vnd.oasis.opendocument.spreadsheet"><office:meta><meta:generator>Txt2tags www.txt2tags.org</meta:generator></office:meta><office:automatic-styles/><office:body><office:spreadsheet>
""",
    'txt': """\
%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",

    'txt2t': """\
%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
%%! style    : %(STYLE)s
%%! encoding : %(ENCODING)s
""",

    'sgml': """\
<!doctype linuxdoc system>
<article>
<title>%(HEADER1)s
<author>%(HEADER2)s
<date>%(HEADER3)s
""",

    'html': """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
<META NAME="generator" CONTENT="http://txt2tags.org">
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=%(ENCODING)s">
<LINK REL="stylesheet" TYPE="text/css" HREF="%(STYLE)s">
<TITLE>%(HEADER1)s</TITLE>
</HEAD><BODY BGCOLOR="white" TEXT="black">
<CENTER>
<H1>%(HEADER1)s</H1>
<FONT SIZE="4"><I>%(HEADER2)s</I></FONT><BR>
<FONT SIZE="4">%(HEADER3)s</FONT>
</CENTER>
""",

    'htmlcss': """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
<META NAME="generator" CONTENT="http://txt2tags.org">
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=%(ENCODING)s">
<LINK REL="stylesheet" TYPE="text/css" HREF="%(STYLE)s">
<TITLE>%(HEADER1)s</TITLE>
</HEAD>
<BODY>

<DIV CLASS="header" ID="header">
<H1>%(HEADER1)s</H1>
<H2>%(HEADER2)s</H2>
<H3>%(HEADER3)s</H3>
</DIV>
""",

    'html5': """\
<!doctype html>
<html>
<head>
<meta charset=%(ENCODING)s>
<title>%(HEADER1)s</title>
<meta name="generator" content="http://txt2tags.org"/>
<link rel="stylesheet" href="%(STYLE)s"/>
<style>
body{background-color:#fff;color:#000;}
hr{background-color:#000;border:0;color:#000;}
hr.heavy{height:5px;}
hr.light{height:1px;}
img{border:0;display:block;}
img.right{margin:0 0 0 auto;}
table,img.center{border:0;margin:0 auto;}
table th,table td{padding:4px;}
.center,header{text-align:center;}
.right{text-align:right;}
.tableborder,.tableborder td,.tableborder th{border:1px solid #000;}
.underline{text-decoration:underline;}
</style>
</head>
<body>
<header>
<hgroup>
<h1>%(HEADER1)s</h1>
<h2>%(HEADER2)s</h2>
<h3>%(HEADER3)s</h3>
</hgroup>
</header>
<article>
""",

    'html5css': """\
<!doctype html>
<html>
<head>
<meta charset=%(ENCODING)s>
<title>%(HEADER1)s</title>
<meta name="generator" content="http://txt2tags.org"/>
<link rel="stylesheet" href="%(STYLE)s"/>
</head>
<body>
<header>
<hgroup>
<h1>%(HEADER1)s</h1>
<h2>%(HEADER2)s</h2>
<h3>%(HEADER3)s</h3>
</hgroup>
</header>
<article>
""",

    'xhtml': """\
<?xml version="1.0"
      encoding="%(ENCODING)s"
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>%(HEADER1)s</title>
<meta name="generator" content="http://txt2tags.org" />
<link rel="stylesheet" type="text/css" href="%(STYLE)s" />
</head>
<body bgcolor="white" text="black">
<div align="center">
<h1>%(HEADER1)s</h1>
<h2>%(HEADER2)s</h2>
<h3>%(HEADER3)s</h3>
</div>
""",

    'xhtmlcss': """\
<?xml version="1.0"
      encoding="%(ENCODING)s"
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>%(HEADER1)s</title>
<meta name="generator" content="http://txt2tags.org" />
<link rel="stylesheet" type="text/css" href="%(STYLE)s" />
</head>
<body>

<div class="header" id="header">
<h1>%(HEADER1)s</h1>
<h2>%(HEADER2)s</h2>
<h3>%(HEADER3)s</h3>
</div>
""",

    'xhtmls': """\
<?xml version="1.0"
      encoding="%(ENCODING)s"
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>%(HEADER1)s</title>
<meta name="generator" content="http://txt2tags.org" />
<link rel="stylesheet" type="text/css" href="%(STYLE)s" />
<style type="text/css">body {background-color:#FFFFFF ; color:#000000}</style>
</head>
<body>
<div style="text-align:center">
<h1>%(HEADER1)s</h1>
<h2>%(HEADER2)s</h2>
<h3>%(HEADER3)s</h3>
</div>
""",

    'xhtmlscss': """\
<?xml version="1.0"
      encoding="%(ENCODING)s"
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>%(HEADER1)s</title>
<meta name="generator" content="http://txt2tags.org" />
<link rel="stylesheet" type="text/css" href="%(STYLE)s" />
</head>
<body>

<div class="header" id="header">
<h1>%(HEADER1)s</h1>
<h2>%(HEADER2)s</h2>
<h3>%(HEADER3)s</h3>
</div>
""",

    'dbk': """\
<?xml version="1.0"
      encoding="%(ENCODING)s"
?>
<!DOCTYPE article PUBLIC "-//OASIS//DTD DocBook XML V4.5//EN"\
 "docbook/dtd/xml/4.5/docbookx.dtd">
<article lang="en">
  <articleinfo>
    <title>%(HEADER1)s</title>
    <authorgroup>
      <author><othername>%(HEADER2)s</othername></author>
    </authorgroup>
    <date>%(HEADER3)s</date>
  </articleinfo>
""",

    'man': """\
.TH "%(HEADER1)s" 1 "%(HEADER3)s" "%(HEADER2)s"
""",

# TODO style to <HR>
    'pm6': """\
<PMTags1.0 win><C-COLORTABLE ("Preto" 1 0 0 0)
><@Normal=
  <FONT "Times New Roman"><CCOLOR "Preto"><SIZE 11>
  <HORIZONTAL 100><LETTERSPACE 0><CTRACK 127><CSSIZE 70><C+SIZE 58.3>
  <C-POSITION 33.3><C+POSITION 33.3><P><CBASELINE 0><CNOBREAK 0><CLEADING -0.05>
  <GGRID 0><GLEFT 7.2><GRIGHT 0><GFIRST 0><G+BEFORE 7.2><G+AFTER 0>
  <GALIGNMENT "justify"><GMETHOD "proportional"><G& "ENGLISH">
  <GPAIRS 12><G%% 120><GKNEXT 0><GKWIDOW 0><GKORPHAN 0><GTABS $>
  <GHYPHENATION 2 34 0><GWORDSPACE 75 100 150><GSPACE -5 0 25>
><@Bullet=<@-PARENT "Normal"><FONT "Abadi MT Condensed Light">
  <GLEFT 14.4><G+BEFORE 2.15><G%% 110><GTABS(25.2 l "")>
><@PreFormat=<@-PARENT "Normal"><FONT "Lucida Console"><SIZE 8><CTRACK 0>
  <GLEFT 0><G+BEFORE 0><GALIGNMENT "left"><GWORDSPACE 100 100 100><GSPACE 0 0 0>
><@Title1=<@-PARENT "Normal"><FONT "Arial"><SIZE 14><B>
  <GCONTENTS><GLEFT 0><G+BEFORE 0><GALIGNMENT "left">
><@Title2=<@-PARENT "Title1"><SIZE 12><G+BEFORE 3.6>
><@Title3=<@-PARENT "Title1"><SIZE 10><GLEFT 7.2><G+BEFORE 7.2>
><@Title4=<@-PARENT "Title3">
><@Title5=<@-PARENT "Title3">
><@Quote=<@-PARENT "Normal"><SIZE 10><I>>

%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",

    'mgp': """\
#!/usr/X11R6/bin/mgp -t 90
%%deffont "normal"    xfont  "utopia-medium-r", charset "iso8859-1"
%%deffont "normal-i"  xfont  "utopia-medium-i", charset "iso8859-1"
%%deffont "normal-b"  xfont  "utopia-bold-r"  , charset "iso8859-1"
%%deffont "normal-bi" xfont  "utopia-bold-i"  , charset "iso8859-1"
%%deffont "mono"      xfont "courier-medium-r", charset "iso8859-1"
%%default 1 size 5
%%default 2 size 8, fore "yellow", font "normal-b", center
%%default 3 size 5, fore "white",  font "normal", left, prefix "  "
%%tab 1 size 4, vgap 30, prefix "     ", icon arc "red" 40, leftfill
%%tab 2 prefix "            ", icon arc "orange" 40, leftfill
%%tab 3 prefix "                   ", icon arc "brown" 40, leftfill
%%tab 4 prefix "                          ", icon arc "darkmagenta" 40, leftfill
%%tab 5 prefix "                                ", icon arc "magenta" 40, leftfill
%%%%------------------------- end of headers -----------------------------
%%page





%%size 10, center, fore "yellow"
%(HEADER1)s

%%font "normal-i", size 6, fore "white", center
%(HEADER2)s

%%font "mono", size 7, center
%(HEADER3)s
""",

    'moin': """\
'''%(HEADER1)s'''

''%(HEADER2)s''

%(HEADER3)s
""",

    'gwiki': """\
*%(HEADER1)s*

%(HEADER2)s

_%(HEADER3)s_
""",

    'adoc': """\
= %(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",

    'doku': """\
===== %(HEADER1)s =====

**//%(HEADER2)s//**

//%(HEADER3)s//
""",

    'pmw': """\
(:Title %(HEADER1)s:)

(:Description %(HEADER2)s:)

(:Summary %(HEADER3)s:)
""",

    'wiki': """\
'''%(HEADER1)s'''

%(HEADER2)s

''%(HEADER3)s''
""",

    'red': """\
h1. %(HEADER1)s

Author: %(HEADER2)s
Date: %(HEADER3)s
""",

    'tex': \
r"""\documentclass{article}
\usepackage{graphicx}
\usepackage{paralist} %% needed for compact lists
\usepackage[normalem]{ulem} %% needed by strike
\usepackage[urlcolor=blue,colorlinks=true]{hyperref}
\usepackage[%(ENCODING)s]{inputenc}  %% char encoding
\usepackage{%(STYLE)s}  %% user defined

\title{%(HEADER1)s}
\author{%(HEADER2)s}
\begin{document}
\date{%(HEADER3)s}
\maketitle
\clearpage
""",

    'lout': """\
@SysInclude { doc }
@Document
  @InitialFont { Times Base 12p }  # Times, Courier, Helvetica, ...
  @PageOrientation { Portrait }    # Portrait, Landscape
  @ColumnNumber { 1 }              # Number of columns (2, 3, ...)
  @PageHeaders { Simple }          # None, Simple, Titles, NoTitles
  @InitialLanguage { English }     # German, French, Portuguese, ...
  @OptimizePages { Yes }           # Yes/No smart page break feature
//
@Text @Begin
@Display @Heading { %(HEADER1)s }
@Display @I { %(HEADER2)s }
@Display { %(HEADER3)s }
#@NP                               # Break page after Headers
""",

# @SysInclude { tbl }                   # Tables support
# setup: @MakeContents { Yes }          # show TOC
# setup: @SectionGap                    # break page at each section

    'creole': """\
%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",

    'md': """\
%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",

    'bbcode': """\
%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",

    'spip': """\
{{{%(HEADER1)s}}}

{{%(HEADER2)s}}

{%(HEADER3)s}

""",

    'rtf': \
r"""{\rtf1\ansi\ansicpg1252\deff0
{\fonttbl
{\f0\froman Times;}
{\f1\fswiss Arial;}
{\f2\fmodern Courier;}
}
{\colortbl;\red0\green0\blue255;}
{\stylesheet
{\s1\sbasedon222\snext1\f0\fs24\cf0 Normal;}
{\s2\sbasedon1\snext2{\*\txttags paragraph}\f0\fs24\qj\sb0\sa0\sl480\slmult1\li0\ri0\fi360 Body Text;}
{\s3\sbasedon2\snext3{\*\txttags verbatim}\f2\fs20\ql\sb0\sa240\sl240\slmult1\li720\ri720\fi0 Verbatim;}
{\s4\sbasedon2\snext4{\*\txttags quote}\f0\fs24\qj\sb0\sa0\sl480\slmult1\li720\ri720\fi0 Block Quote;}
{\s10\sbasedon1\snext10\keepn{\*\txttags maintitle}\f1\fs24\qc\sb0\sa0\sl480\slmult1\li0\ri0\fi0 Title;}
{\s11\sbasedon1\snext2\keepn{\*\txttags title1}\f1\fs24\qc\sb240\sa240\sl480\slmult1\li0\ri0\fi0\b Heading 1;}
{\s12\sbasedon11\snext2\keepn{\*\txttags title2}\f1\fs24\ql\sb240\sa240\sl480\slmult1\li0\ri0\fi0\b Heading 2;}
{\s13\sbasedon11\snext2\keepn{\*\txttags title3}\f1\fs24\ql\sb240\sa240\sl480\slmult1\li360\ri0\fi0\b Heading 3;}
{\s14\sbasedon11\snext2\keepn{\*\txttags title4}\f1\fs24\ql\sb240\sa240\sl480\slmult1\li360\ri0\fi0\b\i Heading 4;}
{\s15\sbasedon11\snext2\keepn{\*\txttags title5}\f1\fs24\ql\sb240\sa240\sl480\slmult1\li360\ri0\fi0\i Heading 5;}
{\s21\sbasedon2\snext21{\*\txttags list}\f0\fs24\qj\sb0\sa0\sl480\slmult1{\*\txttags list indent}\li720\ri0\fi-360 List;}
}
{\*\listtable
{\list\listtemplateid1
{\listlevel\levelnfc23\leveljc0\levelstartat1\levelfollow0{\leveltext \'01\'95;}{\levelnumbers;}{\*\txttags list indent}\li720\ri0\fi-360}
{\listlevel\levelnfc23\leveljc0\levelstartat1\levelfollow0{\leveltext \'01\'95;}{\levelnumbers;}{\*\txttags list indent}\li1080\ri0\fi-360}
{\listlevel\levelnfc23\leveljc0\levelstartat1\levelfollow0{\leveltext \'01\'95;}{\levelnumbers;}{\*\txttags list indent}\li1440\ri0\fi-360}
{\listlevel\levelnfc23\leveljc0\levelstartat1\levelfollow0{\leveltext \'01\'95;}{\levelnumbers;}{\*\txttags list indent}\li1800\ri0\fi-360}
{\listlevel\levelnfc23\leveljc0\levelstartat1\levelfollow0{\leveltext \'01\'95;}{\levelnumbers;}{\*\txttags list indent}\li2160\ri0\fi-360}
{\listlevel\levelnfc23\leveljc0\levelstartat1\levelfollow0{\leveltext \'01\'95;}{\levelnumbers;}{\*\txttags list indent}\li2520\ri0\fi-360}
{\listlevel\levelnfc23\leveljc0\levelstartat1\levelfollow0{\leveltext \'01\'95;}{\levelnumbers;}{\*\txttags list indent}\li2880\ri0\fi-360}
{\listlevel\levelnfc23\leveljc0\levelstartat1\levelfollow0{\leveltext \'01\'95;}{\levelnumbers;}{\*\txttags list indent}\li3240\ri0\fi-360}
{\listlevel\levelnfc23\leveljc0\levelstartat1\levelfollow0{\leveltext \'01\'95;}{\levelnumbers;}{\*\txttags list indent}\li3600\ri0\fi-360}
\listid1}
{\list\listtemplateid2
{\listlevel\levelnfc0\leveljc0\levelstartat1\levelfollow0{\leveltext \'02\'00.;}{\levelnumbers\'01;}{\*\txttags list indent}\li720\ri0\fi-360}
{\listlevel\levelnfc0\leveljc0\levelstartat1\levelfollow0{\leveltext \'02\'01.;}{\levelnumbers\'01;}{\*\txttags list indent}\li1080\ri0\fi-360}
{\listlevel\levelnfc0\leveljc0\levelstartat1\levelfollow0{\leveltext \'02\'02.;}{\levelnumbers\'01;}{\*\txttags list indent}\li1440\ri0\fi-360}
{\listlevel\levelnfc0\leveljc0\levelstartat1\levelfollow0{\leveltext \'02\'03.;}{\levelnumbers\'01;}{\*\txttags list indent}\li1800\ri0\fi-360}
{\listlevel\levelnfc0\leveljc0\levelstartat1\levelfollow0{\leveltext \'02\'04.;}{\levelnumbers\'01;}{\*\txttags list indent}\li2160\ri0\fi-360}
{\listlevel\levelnfc0\leveljc0\levelstartat1\levelfollow0{\leveltext \'02\'05.;}{\levelnumbers\'01;}{\*\txttags list indent}\li2520\ri0\fi-360}
{\listlevel\levelnfc0\leveljc0\levelstartat1\levelfollow0{\leveltext \'02\'06.;}{\levelnumbers\'01;}{\*\txttags list indent}\li2880\ri0\fi-360}
{\listlevel\levelnfc0\leveljc0\levelstartat1\levelfollow0{\leveltext \'02\'07.;}{\levelnumbers\'01;}{\*\txttags list indent}\li3240\ri0\fi-360}
{\listlevel\levelnfc0\leveljc0\levelstartat1\levelfollow0{\leveltext \'02\'08.;}{\levelnumbers\'01;}{\*\txttags list indent}\li3600\ri0\fi-360}
\listid2}
{\list\listtemplateid3
{\listlevel\levelnfc0\leveljc1\levelstartat1\levelfollow1{\leveltext \'02\'00.;}{\levelnumbers\'01;}}
{\listlevel\levelnfc0\leveljc1\levelstartat1\levelfollow1{\leveltext \'04\'00.\'01.;}{\levelnumbers\'01\'03;}}
{\listlevel\levelnfc0\leveljc1\levelstartat1\levelfollow1{\leveltext \'06\'00.\'01.\'02.;}{\levelnumbers\'01\'03\'05;}}
{\listlevel\levelnfc0\leveljc1\levelstartat1\levelfollow1{\leveltext \'08\'00.\'01.\'02.\'03.;}{\levelnumbers\'01\'03\'05\'07;}}
{\listlevel\levelnfc0\leveljc1\levelstartat1\levelfollow1{\leveltext \'10\'00.\'01.\'02.\'03.\'04.;}{\levelnumbers\'01\'03\'05\'07\'09;}}
{\listlevel\levelnfc0\leveljc1\levelstartat1\levelfollow1{\leveltext \'02\'05.;}{\levelnumbers\'01;}}
{\listlevel\levelnfc0\leveljc1\levelstartat1\levelfollow1{\leveltext \'02\'06.;}{\levelnumbers\'01;}}
{\listlevel\levelnfc0\leveljc1\levelstartat1\levelfollow1{\leveltext \'02\'07.;}{\levelnumbers\'01;}}
{\listlevel\levelnfc0\leveljc1\levelstartat1\levelfollow0{\leveltext \'02\'08.;}{\levelnumbers\'01;}}
\listid3}
}
{\listoverridetable
{\listoverride\listid1\listoverridecount0\ls1}
{\listoverride\listid2\listoverridecount0\ls2}
{\listoverride\listid3\listoverridecount0\ls3}
}
{\info
{\title %(HEADER1)s }
{\author %(HEADER2)s }
}
\deflang1033\widowctrl\hyphauto\uc1\fromtext
\paperw12240\paperh15840
\margl1440\margr1440\margt1440\margb1440
\sectd
{\header\pard\qr\plain\f0 Page \chpgn\par}
{\pard\plain\s10\keepn{\*\txttags maintitle}\f1\fs24\qc\sb2880\sa0\sl480\slmult1\li0\ri0\fi0 %(HEADER1)s\par}
{\pard\plain\s10\keepn{\*\txttags maintitle}\f1\fs24\qc\sb0\sa0\sl480\slmult1\li0\ri0\fi0 %(HEADER2)s\par}
{\pard\plain\s10\keepn{\*\txttags maintitle}\f1\fs24\qc\sb0\sa0\sl480\slmult1\li0\ri0\fi0 %(HEADER3)s\par}
""",

}


##############################################################################


def getTags(config):
    "Returns all the known tags for the specified target"

    keys = """
    title1              numtitle1
    title2              numtitle2
    title3              numtitle3
    title4              numtitle4
    title5              numtitle5
    title1Open          title1Close
    title2Open          title2Close
    title3Open          title3Close
    title4Open          title4Close
    title5Open          title5Close
    blocktitle1Open     blocktitle1Close
    blocktitle2Open     blocktitle2Close
    blocktitle3Open     blocktitle3Close

    paragraphOpen       paragraphClose
    blockVerbOpen       blockVerbClose  blockVerbLine
    blockQuoteOpen      blockQuoteClose blockQuoteLine
    blockVerbSep
    blockCommentOpen    blockCommentClose

    fontMonoOpen        fontMonoClose
    fontBoldOpen        fontBoldClose
    fontItalicOpen      fontItalicClose
    fontUnderlineOpen   fontUnderlineClose
    fontStrikeOpen      fontStrikeClose

    listOpen            listClose
    listOpenCompact     listCloseCompact
    listItemOpen        listItemClose     listItemLine
    numlistOpen         numlistClose
    numlistOpenCompact  numlistCloseCompact
    numlistItemOpen     numlistItemClose  numlistItemLine
    deflistOpen         deflistClose
    deflistOpenCompact  deflistCloseCompact
    deflistItem1Open    deflistItem1Close
    deflistItem2Open    deflistItem2Close deflistItem2LinePrefix

    bar1                bar2
    url                 urlMark      urlMarkAnchor   urlImg
    email               emailMark
    img                 imgAlignLeft  imgAlignRight  imgAlignCenter
                       _imgAlignLeft _imgAlignRight _imgAlignCenter

    tableOpen           tableClose
    _tableBorder        _tableAlignLeft      _tableAlignCenter
    tableRowOpen        tableRowClose        tableRowSep
    tableTitleRowOpen   tableTitleRowClose
    tableCellOpen       tableCellClose       tableCellSep
    tableTitleCellOpen  tableTitleCellClose  tableTitleCellSep
    _tableColAlignLeft  _tableColAlignRight  _tableColAlignCenter
    tableCellAlignLeft  tableCellAlignRight  tableCellAlignCenter
    _tableCellAlignLeft _tableCellAlignRight _tableCellAlignCenter
    _tableCellColSpan   tableColAlignSep
    _tableCellColSpanChar                    _tableCellBorder
    _tableCellMulticolOpen
    _tableCellMulticolClose
    tableCellHead       tableTitleCellHead

    bodyOpen            bodyClose
    cssOpen             cssClose
    tocOpen             tocClose             TOC
    anchor
    comment
    pageBreak
    EOD
    """.split()

    # TIP: \a represents the current text inside the mark
    # TIP: ~A~, ~B~ and ~C~ are expanded to other tags parts

    alltags = {

    'aat': {
        'title1'               : '\a'                     ,
        'title2'               : '\a'                     ,
        'title3'               : '\a'                     ,
        'title4'               : '\a'                     ,
        'title5'               : '\a'                     ,
        'blockQuoteLine'       : '\t'                     ,
        'listItemOpen'         : AA['bullet'] + ' '       ,
        'numlistItemOpen'      : '\a. '                   ,
        'bar1'                 : aa_line(AA['bar1'], config['width']),
        'bar2'                 : aa_line(AA['bar2'], config['width']),
        'url'                  : '\a'                     ,
        'urlMark'              : '\a[\a]'                 ,
        'email'                : '\a'                     ,
        'emailMark'            : '\a[\a]'                 ,
        'img'                  : '[\a]'                   ,
        'imgEmbed'             : '\a'                     ,
        'fontBoldOpen'         : '*'                      ,
        'fontBoldClose'        : '*'                      ,
        'fontItalicOpen'       : '/'                      ,
        'fontItalicClose'      : '/'                      ,
        'fontUnderlineOpen'    : '_'                      ,
        'fontUnderlineClose'   : '_'                      ,
        'fontStrikeOpen'       : '-'                      ,
        'fontStrikeClose'      : '-'                      ,
    },

    'rst': {
        'title1'               : '\a'                     ,
        'title2'               : '\a'                     ,
        'title3'               : '\a'                     ,
        'title4'               : '\a'                     ,
        'title5'               : '\a'                     ,
        'blockVerbOpen'        : '::\n'                   ,
        'blockQuoteLine'       : '    '                   ,
        'listItemOpen'         : RST['bullet'] + ' '      ,
        'numlistItemOpen'      : '\a. '                   ,
        'bar1'                 : aa_line(RST['bar1'], 10) ,
        'url'                  : '\a'                     ,
        'urlMark'              : '`\a <\a>`_'             ,
        'email'                : '\a'                     ,
        'emailMark'            : '`\a <\a>`_'             ,
        'img'                  : '\n\n.. image:: \a\n   :align: ~A~\n\nENDIMG',
        'urlImg'               : '\n   :target: '         ,
        '_imgAlignLeft'        : 'left'                   ,
        '_imgAlignCenter'      : 'center'                 ,
        '_imgAlignRight'       : 'right'                  ,
        'fontMonoOpen'         : '``'                     ,
        'fontMonoClose'        : '``'                     ,
        'fontBoldOpen'         : '**'                     ,
        'fontBoldClose'        : '**'                     ,
        'fontItalicOpen'       : '*'                      ,
        'fontItalicClose'      : '*'                      ,
        'comment'              : '.. \a'                  ,
        'TOC'                  : '\n.. contents::'        ,
    },

    'txt': {
        'title1'               : '  \a'      ,
        'title2'               : '\t\a'      ,
        'title3'               : '\t\t\a'    ,
        'title4'               : '\t\t\t\a'  ,
        'title5'               : '\t\t\t\t\a',
        'blockQuoteLine'       : '\t'        ,
        'listItemOpen'         : '- '        ,
        'numlistItemOpen'      : '\a. '      ,
        'bar1'                 : '\a'        ,
        'url'                  : '\a'        ,
        'urlMark'              : '\a (\a)'   ,
        'email'                : '\a'        ,
        'emailMark'            : '\a (\a)'   ,
        'img'                  : '[\a]'      ,
    },

    'csv': {
    },

    'txt2t': {
        'title1' : '         = \a =~A~' ,
        'title2' : '        == \a ==~A~' ,
        'title3' : '       === \a ===~A~' ,
        'title4' : '      ==== \a ====~A~' ,
        'title5' : '     ===== \a =====~A~' ,
        'numtitle1' : '         + \a +~A~' ,
        'numtitle2' : '        ++ \a ++~A~' ,
        'numtitle3' : '       +++ \a +++~A~' ,
        'numtitle4' : '      ++++ \a ++++~A~' ,
        'numtitle5' : '     +++++ \a +++++~A~' ,
        'anchor' : '[\a]',
        'blockVerbOpen' : '```' ,
        'blockVerbClose' : '```' ,
        'blockQuoteLine' : '\t' ,
        'blockCommentOpen' : '%%%' ,
        'blockCommentClose' : '%%%' ,
        'fontMonoOpen' : '``' ,
        'fontMonoClose' : '``' ,
        'fontBoldOpen' : '**' ,
        'fontBoldClose' : '**' ,
        'fontItalicOpen' : '//' ,
        'fontItalicClose' : '//' ,
        'fontUnderlineOpen' : '__' ,
        'fontUnderlineClose' : '__' ,
        'fontStrikeOpen' : '--' ,
        'fontStrikeClose' : '--' ,
        'listItemOpen' : '- ' ,
        'numlistItemOpen' : '+ ' ,
        'deflistItem1Open' : ': ' ,
        'listClose': '-',
        'numlistClose': '+',
        'deflistClose': ':',
        'bar1' : '-------------------------' ,
        'bar2' : '=========================' ,
        'url' : '\a' ,
        'urlMark' : '[\a \a]' ,
        #'urlMarkAnchor' : '' ,
        'email' : '\a' ,
        'emailMark' : '[\a \a]' ,
        'img' : '[\a]' ,
        '_tableBorder' : '|' ,
        '_tableAlignLeft' : '' ,
        '_tableAlignCenter' : '   ' ,
        'tableRowOpen' : '~A~' ,
        'tableRowClose' : '~B~' ,
#        'tableRowSep' : '' ,
        'tableTitleRowOpen' : '~A~|' ,
        'tableCellOpen' : '| ' ,
        'tableCellClose' : ' ~S~' ,
#        'tableCellSep' : '' ,
        'tableCellAlignLeft' : '\a  ' ,
        'tableCellAlignRight' : '  \a' ,
        'tableCellAlignCenter' : '  \a  ' ,
#        '_tableCellColSpan' : '' ,
        '_tableCellColSpanChar' : '|' ,
        'comment' : '% \a' ,
    },

    'ods': {
        'tableOpen'            : '<table:table table:name="Table">',
        'tableClose'           : '</table:table>'                  ,
        'tableRowOpen'         : '<table:table-row>'               ,
        'tableRowClose'        : '</table:table-row>'              ,
        'tableCellOpen'        : '<table:table-cell><text:p>'      ,
        'tableCellClose'       : '</text:p></table:table-cell>'    ,
        'EOD'                  : '</office:spreadsheet></office:body></office:document>',
    },

    'html': {
        'paragraphOpen'        : '<P>'            ,
        'paragraphClose'       : '</P>'           ,
        'title1'               : '<H1~A~>\a</H1>' ,
        'title2'               : '<H2~A~>\a</H2>' ,
        'title3'               : '<H3~A~>\a</H3>' ,
        'title4'               : '<H4~A~>\a</H4>' ,
        'title5'               : '<H5~A~>\a</H5>' ,
        'anchor'               : ' ID="\a"',
        'blockVerbOpen'        : '<PRE>'          ,
        'blockVerbClose'       : '</PRE>'         ,
        'blockQuoteOpen'       : '<BLOCKQUOTE>'   ,
        'blockQuoteClose'      : '</BLOCKQUOTE>'  ,
        'fontMonoOpen'         : '<CODE>'         ,
        'fontMonoClose'        : '</CODE>'        ,
        'fontBoldOpen'         : '<B>'            ,
        'fontBoldClose'        : '</B>'           ,
        'fontItalicOpen'       : '<I>'            ,
        'fontItalicClose'      : '</I>'           ,
        'fontUnderlineOpen'    : '<U>'            ,
        'fontUnderlineClose'   : '</U>'           ,
        'fontStrikeOpen'       : '<S>'            ,
        'fontStrikeClose'      : '</S>'           ,
        'listOpen'             : '<UL>'           ,
        'listClose'            : '</UL>'          ,
        'listItemOpen'         : '<LI>'           ,
        'numlistOpen'          : '<OL>'           ,
        'numlistClose'         : '</OL>'          ,
        'numlistItemOpen'      : '<LI>'           ,
        'deflistOpen'          : '<DL>'           ,
        'deflistClose'         : '</DL>'          ,
        'deflistItem1Open'     : '<DT>'           ,
        'deflistItem1Close'    : '</DT>'          ,
        'deflistItem2Open'     : '<DD>'           ,
        'bar1'                 : '<HR NOSHADE SIZE=1>'        ,
        'bar2'                 : '<HR NOSHADE SIZE=5>'        ,
        'url'                  : '<A HREF="\a">\a</A>'        ,
        'urlMark'              : '<A HREF="\a">\a</A>'        ,
        'email'                : '<A HREF="mailto:\a">\a</A>' ,
        'emailMark'            : '<A HREF="mailto:\a">\a</A>' ,
        'img'                  : '<IMG~A~ SRC="\a" BORDER="0" ALT="">',
        'imgEmbed'             : '<IMG~A~ SRC="\a" BORDER="0" ALT="">', 
        '_imgAlignLeft'        : ' ALIGN="left"'  ,
        '_imgAlignCenter'      : ' ALIGN="middle"',
        '_imgAlignRight'       : ' ALIGN="right"' ,
        'tableOpen'            : '<TABLE~A~~B~ CELLPADDING="4">',
        'tableClose'           : '</TABLE>'       ,
        'tableRowOpen'         : '<TR>'           ,
        'tableRowClose'        : '</TR>'          ,
        'tableCellOpen'        : '<TD~A~~S~>'     ,
        'tableCellClose'       : '</TD>'          ,
        'tableTitleCellOpen'   : '<TH~S~>'        ,
        'tableTitleCellClose'  : '</TH>'          ,
        '_tableBorder'         : ' BORDER="1"'    ,
        '_tableAlignCenter'    : ' ALIGN="center"',
        '_tableCellAlignRight' : ' ALIGN="right"' ,
        '_tableCellAlignCenter': ' ALIGN="center"',
        '_tableCellColSpan'    : ' COLSPAN="\a"'  ,
        'cssOpen'              : '<STYLE TYPE="text/css">',
        'cssClose'             : '</STYLE>'       ,
        'comment'              : '<!-- \a -->'    ,
        'EOD'                  : '</BODY></HTML>'
    },

    #TIP xhtml inherits all HTML definitions (lowercased)
    #TIP http://www.w3.org/TR/xhtml1/#guidelines
    #TIP http://www.htmlref.com/samples/Chapt17/17_08.htm
    'xhtml': {
        'listItemClose'        : '</li>'          ,
        'numlistItemClose'     : '</li>'          ,
        'deflistItem2Close'    : '</dd>'          ,
        'bar1'                 : '<hr class="light" />',
        'bar2'                 : '<hr class="heavy" />',
        'img'                  : '<img~A~ src="\a" border="0" alt=""/>',
        'imgEmbed'             : '<img~A~ SRC="\a" border="0" alt=""/>'
    },

    'xhtmls': {
        'fontBoldOpen'         : '<strong>'       ,
        'fontBoldClose'        : '</strong>'      ,
        'fontItalicOpen'       : '<em>'           ,
        'fontItalicClose'      : '</em>'          ,
        'fontUnderlineOpen'    : '<span style="text-decoration:underline">',
        'fontUnderlineClose'   : '</span>'        ,
        'fontStrikeOpen'       : '<span style="text-decoration:line-through">',  # use <del> instead ?
        'fontStrikeClose'      : '</span>'        ,
        'listItemClose'        : '</li>'          ,
        'numlistItemClose'     : '</li>'          ,
        'deflistItem2Close'    : '</dd>'          ,
        'bar1'                 : '<hr class="light" />',
        'bar2'                 : '<hr class="heavy" />',
        'img'                  : '<img~a~ src="\a" alt=""/>',
        'imgEmbed'             : '<img~a~ src="\a" alt=""/>',
        '_imgAlignLeft'        : ' style="text-align:left"'  ,
        '_imgAlignCenter'      : ' style="text-align:center"',
        '_imgAlignRight'       : ' style="text-align:right"' ,
        '_tableAlignCenter'    : ' style="text-align:center"',
        '_tableCellAlignRight' : ' style="text-align:right"' ,
        '_tableCellAlignCenter': ' style="text-align:center"',
    },
    'html5': {
        'fontBoldOpen'         : '<strong>'       ,
        'fontBoldClose'        : '</strong>'      ,
        'fontItalicOpen'       : '<em>'           ,
        'fontItalicClose'      : '</em>'          ,
        'fontUnderlineOpen'    : '<span class="underline">',
        'fontUnderlineClose'   : '</span>'        ,
        'fontStrikeOpen'       : '<del>'          ,
        'fontStrikeClose'      : '</del>'         ,
        'listItemClose'        : '</li>'          ,
        'numlistItemClose'     : '</li>'          ,
        'deflistItem2Close'    : '</dd>'          ,
        'bar1'                 : '<hr class="light"/>'        ,
        'bar2'                 : '<hr class="heavy"/>'        ,
        'img'                  : '<img~a~ src="\a" alt=""/>'  ,
        'imgEmbed'             : '<img~a~ src="\a" alt=""/>'  ,
        '_imgAlignLeft'        : ' class="left"'  ,
        '_imgAlignCenter'      : ' class="center"',
        '_imgAlignRight'       : ' class="right"' ,
        'tableOpen'            : '<table~a~~b~>'  ,
        '_tableBorder'         : ' class="tableborder"'      ,
        '_tableAlignCenter'    : ' style="text-align:center"',
        '_tableCellAlignRight' : ' class="right"' ,
        '_tableCellAlignCenter': ' class="center"',
        'cssOpen'              : '<style>'        ,
        'tocOpen'              : '<nav>'          ,
        'tocClose'             : '</nav>'         ,
        'EOD'                  : '</article></body></html>'
    },

    'sgml': {
        'paragraphOpen'        : '<p>'                ,
        'title1'               : '<sect>\a~A~<p>'     ,
        'title2'               : '<sect1>\a~A~<p>'    ,
        'title3'               : '<sect2>\a~A~<p>'    ,
        'title4'               : '<sect3>\a~A~<p>'    ,
        'title5'               : '<sect4>\a~A~<p>'    ,
        'anchor'               : '<label id="\a">'    ,
        'blockVerbOpen'        : '<tscreen><verb>'    ,
        'blockVerbClose'       : '</verb></tscreen>'  ,
        'blockQuoteOpen'       : '<quote>'            ,
        'blockQuoteClose'      : '</quote>'           ,
        'fontMonoOpen'         : '<tt>'               ,
        'fontMonoClose'        : '</tt>'              ,
        'fontBoldOpen'         : '<bf>'               ,
        'fontBoldClose'        : '</bf>'              ,
        'fontItalicOpen'       : '<em>'               ,
        'fontItalicClose'      : '</em>'              ,
        'fontUnderlineOpen'    : '<bf><em>'           ,
        'fontUnderlineClose'   : '</em></bf>'         ,
        'listOpen'             : '<itemize>'          ,
        'listClose'            : '</itemize>'         ,
        'listItemOpen'         : '<item>'             ,
        'numlistOpen'          : '<enum>'             ,
        'numlistClose'         : '</enum>'            ,
        'numlistItemOpen'      : '<item>'             ,
        'deflistOpen'          : '<descrip>'          ,
        'deflistClose'         : '</descrip>'         ,
        'deflistItem1Open'     : '<tag>'              ,
        'deflistItem1Close'    : '</tag>'             ,
        'bar1'                 : '<!-- \a -->'        ,
        'url'                  : '<htmlurl url="\a" name="\a">'        ,
        'urlMark'              : '<htmlurl url="\a" name="\a">'        ,
        'email'                : '<htmlurl url="mailto:\a" name="\a">' ,
        'emailMark'            : '<htmlurl url="mailto:\a" name="\a">' ,
        'img'                  : '<figure><ph vspace=""><img src="\a"></figure>',
        'tableOpen'            : '<table><tabular ca="~C~">'           ,
        'tableClose'           : '</tabular></table>' ,
        'tableRowSep'          : '<rowsep>'           ,
        'tableCellSep'         : '<colsep>'           ,
        '_tableColAlignLeft'   : 'l'                  ,
        '_tableColAlignRight'  : 'r'                  ,
        '_tableColAlignCenter' : 'c'                  ,
        'comment'              : '<!-- \a -->'        ,
        'TOC'                  : '<toc>'              ,
        'EOD'                  : '</article>'
    },

    'dbk': {
        'paragraphOpen'        : '<para>'                            ,
        'paragraphClose'       : '</para>'                           ,
        'title1Open'           : '~A~<sect1><title>\a</title>'       ,
        'title1Close'          : '</sect1>'                          ,
        'title2Open'           : '~A~  <sect2><title>\a</title>'     ,
        'title2Close'          : '  </sect2>'                        ,
        'title3Open'           : '~A~    <sect3><title>\a</title>'   ,
        'title3Close'          : '    </sect3>'                      ,
        'title4Open'           : '~A~      <sect4><title>\a</title>' ,
        'title4Close'          : '      </sect4>'                    ,
        'title5Open'           : '~A~        <sect5><title>\a</title>',
        'title5Close'          : '        </sect5>'                  ,
        'anchor'               : '<anchor id="\a"/>\n'               ,
        'blockVerbOpen'        : '<programlisting>'                  ,
        'blockVerbClose'       : '</programlisting>'                 ,
        'blockQuoteOpen'       : '<blockquote><para>'                ,
        'blockQuoteClose'      : '</para></blockquote>'              ,
        'fontMonoOpen'         : '<code>'                            ,
        'fontMonoClose'        : '</code>'                           ,
        'fontBoldOpen'         : '<emphasis role="bold">'            ,
        'fontBoldClose'        : '</emphasis>'                       ,
        'fontItalicOpen'       : '<emphasis>'                        ,
        'fontItalicClose'      : '</emphasis>'                       ,
        'fontUnderlineOpen'    : '<emphasis role="underline">'       ,
        'fontUnderlineClose'   : '</emphasis>'                       ,
        # 'fontStrikeOpen'       : '<emphasis role="strikethrough">'   ,  # Don't know
        # 'fontStrikeClose'      : '</emphasis>'                       ,
        'listOpen'             : '<itemizedlist>'                    ,
        'listClose'            : '</itemizedlist>'                   ,
        'listItemOpen'         : '<listitem><para>'                  ,
        'listItemClose'        : '</para></listitem>'                ,
        'numlistOpen'          : '<orderedlist numeration="arabic">' ,
        'numlistClose'         : '</orderedlist>'                    ,
        'numlistItemOpen'      : '<listitem><para>'                  ,
        'numlistItemClose'     : '</para></listitem>'                ,
        'deflistOpen'          : '<variablelist>'                    ,
        'deflistClose'         : '</variablelist>'                   ,
        'deflistItem1Open'     : '<varlistentry><term>'              ,
        'deflistItem1Close'    : '</term>'                           ,
        'deflistItem2Open'     : '<listitem><para>'                  ,
        'deflistItem2Close'    : '</para></listitem></varlistentry>' ,
        # 'bar1'                 : '<>'                                ,  # Don't know
        # 'bar2'                 : '<>'                                ,  # Don't know
        'url'                  : '<ulink url="\a">\a</ulink>'        ,
        'urlMark'              : '<ulink url="\a">\a</ulink>'        ,
        'email'                : '<email>\a</email>'                 ,
        'emailMark'            : '<email>\a</email>'                 ,
        'img'                  : '<mediaobject><imageobject><imagedata fileref="\a"/></imageobject></mediaobject>',
        # '_imgAlignLeft'        : ''                                 ,  # Don't know
        # '_imgAlignCenter'      : ''                                 ,  # Don't know
        # '_imgAlignRight'       : ''                                 ,  # Don't know
        'tableOpenDbk'         : '<informaltable><tgroup cols="n_cols"><tbody>',
        'tableClose'           : '</tbody></tgroup></informaltable>' ,
        'tableRowOpen'         : '<row>'                             ,
        'tableRowClose'        : '</row>'                            ,
        'tableCellOpen'        : '<entry>'                           ,
        'tableCellClose'       : '</entry>'                          ,
        'tableTitleRowOpen'    : '<thead>'                           ,
        'tableTitleRowClose'   : '</thead>'                          ,
        '_tableBorder'         : ' frame="all"'                      ,
        '_tableAlignCenter'    : ' align="center"'                   ,
        '_tableCellAlignRight' : ' align="right"'                    ,
        '_tableCellAlignCenter': ' align="center"'                   ,
        '_tableCellColSpan'    : ' COLSPAN="\a"'                     ,
        'TOC'                  : '<index/>'                          ,
        'comment'              : '<!-- \a -->'                       ,
        'EOD'                  : '</article>'
    },

    'tex': {
        'title1'               : '~A~\section*{\a}'     ,
        'title2'               : '~A~\\subsection*{\a}'   ,
        'title3'               : '~A~\\subsubsection*{\a}',
        # title 4/5: DIRTY: para+BF+\\+\n
        'title4'               : '~A~\\paragraph{}\\textbf{\a}\\\\\n',
        'title5'               : '~A~\\paragraph{}\\textbf{\a}\\\\\n',
        'numtitle1'            : '\n~A~\section{\a}'      ,
        'numtitle2'            : '~A~\\subsection{\a}'    ,
        'numtitle3'            : '~A~\\subsubsection{\a}' ,
        'anchor'               : '\\hypertarget{\a}{}\n'  ,
        'blockVerbOpen'        : '\\begin{verbatim}'   ,
        'blockVerbClose'       : '\\end{verbatim}'     ,
        'blockQuoteOpen'       : '\\begin{quotation}'  ,
        'blockQuoteClose'      : '\\end{quotation}'    ,
        'fontMonoOpen'         : '\\texttt{'           ,
        'fontMonoClose'        : '}'                   ,
        'fontBoldOpen'         : '\\textbf{'           ,
        'fontBoldClose'        : '}'                   ,
        'fontItalicOpen'       : '\\textit{'           ,
        'fontItalicClose'      : '}'                   ,
        'fontUnderlineOpen'    : '\\underline{'        ,
        'fontUnderlineClose'   : '}'                   ,
        'fontStrikeOpen'       : '\\sout{'             ,
        'fontStrikeClose'      : '}'                   ,
        'listOpen'             : '\\begin{itemize}'    ,
        'listClose'            : '\\end{itemize}'      ,
        'listOpenCompact'      : '\\begin{compactitem}',
        'listCloseCompact'     : '\\end{compactitem}'  ,
        'listItemOpen'         : '\\item '             ,
        'numlistOpen'          : '\\begin{enumerate}'  ,
        'numlistClose'         : '\\end{enumerate}'    ,
        'numlistOpenCompact'   : '\\begin{compactenum}',
        'numlistCloseCompact'  : '\\end{compactenum}'  ,
        'numlistItemOpen'      : '\\item '             ,
        'deflistOpen'          : '\\begin{description}',
        'deflistClose'         : '\\end{description}'  ,
        'deflistOpenCompact'   : '\\begin{compactdesc}',
        'deflistCloseCompact'  : '\\end{compactdesc}'  ,
        'deflistItem1Open'     : '\\item['             ,
        'deflistItem1Close'    : ']'                   ,
        'bar1'                 : '\\hrulefill{}'       ,
        'bar2'                 : '\\rule{\linewidth}{1mm}',
        'url'                  : '\\htmladdnormallink{\a}{\a}',
        'urlMark'              : '\\htmladdnormallink{\a}{\a}',
        'email'                : '\\htmladdnormallink{\a}{mailto:\a}',
        'emailMark'            : '\\htmladdnormallink{\a}{mailto:\a}',
        'img'                  : '\\includegraphics{\a}',
        'tableOpen'            : '\\begin{center}\\begin{tabular}{|~C~|}',
        'tableClose'           : '\\end{tabular}\\end{center}',
        'tableRowOpen'         : '\\hline ' ,
        'tableRowClose'        : ' \\\\'    ,
        'tableCellSep'         : ' & '      ,
        '_tableColAlignLeft'   : 'l'        ,
        '_tableColAlignRight'  : 'r'        ,
        '_tableColAlignCenter' : 'c'        ,
        '_tableCellAlignLeft'  : 'l'        ,
        '_tableCellAlignRight' : 'r'        ,
        '_tableCellAlignCenter': 'c'        ,
        '_tableCellColSpan'    : '\a'       ,
        '_tableCellMulticolOpen'  : '\\multicolumn{\a}{|~C~|}{',
        '_tableCellMulticolClose' : '}',
        'tableColAlignSep'     : '|'        ,
        'comment'              : '% \a'     ,
        'TOC'                  : '\\tableofcontents',
        'pageBreak'            : '\\clearpage',
        'EOD'                  : '\\end{document}'
    },

    'lout': {
        'paragraphOpen'        : '@LP'                     ,
        'blockTitle1Open'      : '@BeginSections'          ,
        'blockTitle1Close'     : '@EndSections'            ,
        'blockTitle2Open'      : ' @BeginSubSections'      ,
        'blockTitle2Close'     : ' @EndSubSections'        ,
        'blockTitle3Open'      : '  @BeginSubSubSections'  ,
        'blockTitle3Close'     : '  @EndSubSubSections'    ,
        'title1Open'           : '~A~@Section @Title { \a } @Begin',
        'title1Close'          : '@End @Section'           ,
        'title2Open'           : '~A~ @SubSection @Title { \a } @Begin',
        'title2Close'          : ' @End @SubSection'       ,
        'title3Open'           : '~A~  @SubSubSection @Title { \a } @Begin',
        'title3Close'          : '  @End @SubSubSection'   ,
        'title4Open'           : '~A~@LP @LeftDisplay @B { \a }',
        'title5Open'           : '~A~@LP @LeftDisplay @B { \a }',
        'anchor'               : '@Tag { \a }\n'       ,
        'blockVerbOpen'        : '@LP @ID @F @RawVerbatim @Begin',
        'blockVerbClose'       : '@End @RawVerbatim'   ,
        'blockQuoteOpen'       : '@QD {'               ,
        'blockQuoteClose'      : '}'                   ,
        # enclosed inside {} to deal with joined**words**
        'fontMonoOpen'         : '{@F {'               ,
        'fontMonoClose'        : '}}'                  ,
        'fontBoldOpen'         : '{@B {'               ,
        'fontBoldClose'        : '}}'                  ,
        'fontItalicOpen'       : '{@II {'              ,
        'fontItalicClose'      : '}}'                  ,
        'fontUnderlineOpen'    : '{@Underline{'        ,
        'fontUnderlineClose'   : '}}'                  ,
        # the full form is more readable, but could be BL EL LI NL TL DTI
        'listOpen'             : '@BulletList'         ,
        'listClose'            : '@EndList'            ,
        'listItemOpen'         : '@ListItem{'          ,
        'listItemClose'        : '}'                   ,
        'numlistOpen'          : '@NumberedList'       ,
        'numlistClose'         : '@EndList'            ,
        'numlistItemOpen'      : '@ListItem{'          ,
        'numlistItemClose'     : '}'                   ,
        'deflistOpen'          : '@TaggedList'         ,
        'deflistClose'         : '@EndList'            ,
        'deflistItem1Open'     : '@DropTagItem {'      ,
        'deflistItem1Close'    : '}'                   ,
        'deflistItem2Open'     : '{'                   ,
        'deflistItem2Close'    : '}'                   ,
        'bar1'                 : '@DP @FullWidthRule'  ,
        'url'                  : '{blue @Colour { \a }}'      ,
        'urlMark'              : '\a ({blue @Colour { \a }})' ,
        'email'                : '{blue @Colour { \a }}'      ,
        'emailMark'            : '\a ({blue Colour{ \a }})'   ,
        'img'                  : '~A~@IncludeGraphic { \a }'  ,  # eps only!
        '_imgAlignLeft'        : '@LeftDisplay '              ,
        '_imgAlignRight'       : '@RightDisplay '             ,
        '_imgAlignCenter'      : '@CentredDisplay '           ,
        # lout tables are *way* complicated, no support for now
        #'tableOpen'            : '~A~@Tbl~B~\naformat{ @Cell A | @Cell B } {',
        #'tableClose'           : '}'     ,
        #'tableRowOpen'         : '@Rowa\n'       ,
        #'tableTitleRowOpen'    : '@HeaderRowa'       ,
        #'tableCenterAlign'     : '@CentredDisplay '         ,
        #'tableCellOpen'        : '\a {'                     ,  # A, B, ...
        #'tableCellClose'       : '}'                        ,
        #'_tableBorder'         : '\nrule {yes}'             ,
        'comment'              : '# \a'                     ,
        # @MakeContents must be on the config file
        'TOC'                  : '@DP @ContentsGoesHere @DP',
        'pageBreak'            : '@NP'                      ,
        'EOD'                  : '@End @Text'
    },

    # http://moinmo.in/HelpOnMoinWikiSyntax
    'moin': {
        'title1'                : '= \a ='        ,
        'title2'                : '== \a =='      ,
        'title3'                : '=== \a ==='    ,
        'title4'                : '==== \a ===='  ,
        'title5'                : '===== \a =====',
        'blockVerbOpen'         : '{{{'           ,
        'blockVerbClose'        : '}}}'           ,
        'blockQuoteLine'        : '  '            ,
        'fontMonoOpen'          : '{{{'           ,
        'fontMonoClose'         : '}}}'           ,
        'fontBoldOpen'          : "'''"           ,
        'fontBoldClose'         : "'''"           ,
        'fontItalicOpen'        : "''"            ,
        'fontItalicClose'       : "''"            ,
        'fontUnderlineOpen'     : '__'            ,
        'fontUnderlineClose'    : '__'            ,
        'fontStrikeOpen'        : '--('           ,
        'fontStrikeClose'       : ')--'           ,
        'listItemOpen'          : ' * '           ,
        'numlistItemOpen'       : ' \a. '         ,
        'deflistItem1Open'      : ' '             ,
        'deflistItem1Close'     : '::'            ,
        'deflistItem2LinePrefix': ' :: '          ,
        'bar1'                  : '----'          ,
        'bar2'                  : '--------'      ,
        'url'                   : '[[\a]]'          ,
        'urlMark'               : '[[\a|\a]]'       ,
        'email'                 : '\a'          ,
        'emailMark'             : '[[mailto:\a|\a]]'       ,
        'img'                   : '{{\a}}'          ,
        'tableRowOpen'          : '||'            ,  # || one || two ||
        'tableCellOpen'         : '~S~~A~ '       ,
        'tableCellClose'        : ' ||'           ,
        '_tableCellAlignRight'  : '<)>'           ,  # ||<)> right ||
        '_tableCellAlignCenter' : '<:>'           ,  # ||<:> center ||
        '_tableCellColSpanChar' : '||'            ,  # || cell |||| 2 cells spanned ||
        # Another option for span is ||<-2> two cells spanned ||
        # But mixing span+align is harder with the current code:
        # ||<-2:> two cells spanned and centered ||
        # ||<-2)> two cells spanned and right aligned ||
        # Just appending attributes doesn't work:
        # ||<-2><:> no no no ||
        'comment'               : '/* \a */'      ,
        'TOC'                   : '[[TableOfContents]]'
    },

    # http://code.google.com/p/support/wiki/WikiSyntax
    'gwiki': {
        'title1'               : '= \a ='        ,
        'title2'               : '== \a =='      ,
        'title3'               : '=== \a ==='    ,
        'title4'               : '==== \a ===='  ,
        'title5'               : '===== \a =====',
        'blockVerbOpen'        : '{{{'           ,
        'blockVerbClose'       : '}}}'           ,
        'blockQuoteLine'       : '  '            ,
        'fontMonoOpen'         : '{{{'           ,
        'fontMonoClose'        : '}}}'           ,
        'fontBoldOpen'         : '*'             ,
        'fontBoldClose'        : '*'             ,
        'fontItalicOpen'       : '_'             ,  # underline == italic
        'fontItalicClose'      : '_'             ,
        'fontStrikeOpen'       : '~~'            ,
        'fontStrikeClose'      : '~~'            ,
        'listItemOpen'         : ' * '           ,
        'numlistItemOpen'      : ' # '           ,
        'url'                  : '\a'            ,
        'urlMark'              : '[\a \a]'       ,
        'email'                : 'mailto:\a'     ,
        'emailMark'            : '[mailto:\a \a]',
        'img'                  : '[\a]'          ,
        'tableRowOpen'         : '|| '           ,
        'tableRowClose'        : ' ||'           ,
        'tableCellSep'         : ' || '          ,
    },

    # http://powerman.name/doc/asciidoc
    'adoc': {
        'title1'               : '== \a'         ,
        'title2'               : '=== \a'        ,
        'title3'               : '==== \a'       ,
        'title4'               : '===== \a'      ,
        'title5'               : '===== \a'      ,
        'blockVerbOpen'        : '----'          ,
        'blockVerbClose'       : '----'          ,
        'fontMonoOpen'         : '+'             ,
        'fontMonoClose'        : '+'             ,
        'fontBoldOpen'         : '*'             ,
        'fontBoldClose'        : '*'             ,
        'fontItalicOpen'       : '_'             ,
        'fontItalicClose'      : '_'             ,
        'listItemOpen'         : '- '            ,
        'listItemLine'         : '\t'            ,
        'numlistItemOpen'      : '. '            ,
        'url'                  : '\a'            ,
        'urlMark'              : '\a[\a]'        ,
        'email'                : 'mailto:\a'     ,
        'emailMark'            : 'mailto:\a[\a]' ,
        'img'                  : 'image::\a[]'   ,
    },

    # http://www.dokuwiki.org/syntax
    # http://www.dokuwiki.org/playground:playground
    # Hint: <br> is \\ $
    # Hint: You can add footnotes ((This is a footnote))
    'doku': {
        'title1'               : '===== \a =====',
        'title2'               : '==== \a ===='  ,
        'title3'               : '=== \a ==='    ,
        'title4'               : '== \a =='      ,
        'title5'               : '= \a ='        ,
        # DokuWiki uses '  ' identation to mark verb blocks (see indentverbblock)
        'blockQuoteLine'       : '>'             ,
        'fontMonoOpen'         : "''"            ,
        'fontMonoClose'        : "''"            ,
        'fontBoldOpen'         : "**"            ,
        'fontBoldClose'        : "**"            ,
        'fontItalicOpen'       : "//"            ,
        'fontItalicClose'      : "//"            ,
        'fontUnderlineOpen'    : "__"            ,
        'fontUnderlineClose'   : "__"            ,
        'fontStrikeOpen'       : '<del>'         ,
        'fontStrikeClose'      : '</del>'        ,
        'listItemOpen'         : '  * '          ,
        'numlistItemOpen'      : '  - '          ,
        'bar1'                 : '----'          ,
        'url'                  : '[[\a]]'        ,
        'urlMark'              : '[[\a|\a]]'     ,
        'email'                : '[[\a]]'        ,
        'emailMark'            : '[[\a|\a]]'     ,
        'img'                  : '{{\a}}'        ,
        'imgAlignLeft'         : '{{\a }}'       ,
        'imgAlignRight'        : '{{ \a}}'       ,
        'imgAlignCenter'       : '{{ \a }}'      ,
        'tableTitleRowOpen'    : '^ '            ,
        'tableTitleRowClose'   : ' ^'            ,
        'tableTitleCellSep'    : ' ^ '           ,
        'tableRowOpen'         : '| '            ,
        'tableRowClose'        : ' |'            ,
        'tableCellSep'         : ' | '           ,
        # DokuWiki has no attributes. The content must be aligned!
        # '_tableCellAlignRight' : '<)>'           ,  # ??
        # '_tableCellAlignCenter': '<:>'           ,  # ??
        # DokuWiki colspan is the same as txt2tags' with multiple |||
        # 'comment'             : '## \a'         ,  # ??
        # TOC is automatic
    },

    # http://www.pmwiki.org/wiki/PmWiki/TextFormattingRules
    # http://www.pmwiki.org/wiki/Main/WikiSandbox
    'pmw': {
        'title1'               : '~A~! \a '      ,
        'title2'               : '~A~!! \a '     ,
        'title3'               : '~A~!!! \a '    ,
        'title4'               : '~A~!!!! \a '   ,
        'title5'               : '~A~!!!!! \a '  ,
        'blockQuoteOpen'       : '->'            ,
        'blockQuoteClose'      : '\n'            ,
        # In-text font
        'fontLargeOpen'        : "[+"            ,
        'fontLargeClose'       : "+]"            ,
        'fontLargerOpen'       : "[++"           ,
        'fontLargerClose'      : "++]"           ,
        'fontSmallOpen'        : "[-"            ,
        'fontSmallClose'       : "-]"            ,
        'fontLargerOpen'       : "[--"           ,
        'fontLargerClose'      : "--]"           ,
        'fontMonoOpen'         : "@@"            ,
        'fontMonoClose'        : "@@"            ,
        'fontBoldOpen'         : "'''"           ,
        'fontBoldClose'        : "'''"           ,
        'fontItalicOpen'       : "''"            ,
        'fontItalicClose'      : "''"            ,
        'fontUnderlineOpen'    : "{+"            ,
        'fontUnderlineClose'   : "+}"            ,
        'fontStrikeOpen'       : '{-'            ,
        'fontStrikeClose'      : '-}'            ,
        # Lists
        'listItemLine'          : '*'            ,
        'numlistItemLine'       : '#'            ,
        'deflistItem1Open'      : ': '           ,
        'deflistItem1Close'     : ':'            ,
        'deflistItem2LineOpen'  : '::'           ,
        'deflistItem2LineClose' : ':'            ,
        # Verbatim block
        'blockVerbOpen'        : '[@'            ,
        'blockVerbClose'       : '@]'            ,
        'bar1'                 : '----'          ,
        # URL, email and anchor
        'url'                   : '\a'           ,
        'urlMark'               : '[[\a -> \a]]' ,
        'email'                 : '\a'           ,
        'emailMark'             : '[[\a -> mailto:\a]]',
        'anchor'                : '[[#\a]]\n'    ,
        # Image markup
        'img'                   : '\a'           ,
        #'imgAlignLeft'         : '{{\a }}'       ,
        #'imgAlignRight'        : '{{ \a}}'       ,
        #'imgAlignCenter'       : '{{ \a }}'      ,
        # Table attributes
        'tableTitleRowOpen'    : '||! '          ,
        'tableTitleRowClose'   : '||'            ,
        'tableTitleCellSep'    : ' ||!'          ,
        'tableRowOpen'         : '||'            ,
        'tableRowClose'        : '||'            ,
        'tableCellSep'         : ' ||'           ,
    },

    # http://en.wikipedia.org/wiki/Help:Editing
    # http://www.mediawiki.org/wiki/Sandbox
    'wiki': {
        'title1'                : '== \a =='        ,
        'title2'                : '=== \a ==='      ,
        'title3'                : '==== \a ===='    ,
        'title4'                : '===== \a ====='  ,
        'title5'                : '====== \a ======',
        'blockVerbOpen'         : '<pre>'           ,
        'blockVerbClose'        : '</pre>'          ,
        'blockQuoteOpen'        : '<blockquote>'    ,
        'blockQuoteClose'       : '</blockquote>'   ,
        'fontMonoOpen'          : '<tt>'            ,
        'fontMonoClose'         : '</tt>'           ,
        'fontBoldOpen'          : "'''"             ,
        'fontBoldClose'         : "'''"             ,
        'fontItalicOpen'        : "''"              ,
        'fontItalicClose'       : "''"              ,
        'fontUnderlineOpen'     : '<u>'             ,
        'fontUnderlineClose'    : '</u>'            ,
        'fontStrikeOpen'        : '<s>'             ,
        'fontStrikeClose'       : '</s>'            ,
        #XXX Mixed lists not working: *#* list inside numlist inside list
        'listItemLine'          : '*'               ,
        'numlistItemLine'       : '#'               ,
        'deflistItem1Open'      : '; '              ,
        'deflistItem2LinePrefix': ': '              ,
        'bar1'                  : '----'            ,
        'url'                   : '[\a]'            ,
        'urlMark'               : '[\a \a]'         ,
        'urlMarkAnchor'         : '[[\a|\a]]'       ,
        'email'                 : 'mailto:\a'       ,
        'emailMark'             : '[mailto:\a \a]'  ,
        # [[Image:foo.png|right|Optional alt/caption text]] (right, left, center, none)
        'img'                   : '[[Image:\a~A~]]' ,
        '_imgAlignLeft'         : '|left'           ,
        '_imgAlignCenter'       : '|center'         ,
        '_imgAlignRight'        : '|right'          ,
        # {| border="1" cellspacing="0" cellpadding="4" align="center"
        'tableOpen'             : '{|~A~~B~'        ,
        'tableClose'            : '|}'              ,
        'tableRowOpen'          : '|-'              ,
        'tableTitleRowOpen'     : '|-'              ,
        # Note: using one cell per line syntax
        'tableCellOpen'         : '\n|~A~~S~~Z~ '   ,
        'tableTitleCellOpen'    : '\n!~A~~S~~Z~ '   ,
        '_tableBorder'          : ' border="1"'     ,
        '_tableAlignCenter'     : ' align="center"' ,
        '_tableCellAlignRight'  : ' align="right"'  ,
        '_tableCellAlignCenter' : ' align="center"' ,
        '_tableCellColSpan'     : ' colspan="\a"'   ,
        '_tableAttrDelimiter'   : ' |'              ,
        'comment'               : '<!-- \a -->'     ,
        'TOC'                   : '__TOC__'         ,
    },

    # http://demo.redmine.org/help/wiki_syntax.html
    # http://demo.redmine.org/help/wiki_syntax_detailed.html
    # Sandbox: http://demo.redmine.org - create account, add new project
    'red': {
        'title1'                : 'h1. \a'   ,
        'title2'                : 'h2. \a'   ,
        'title3'                : 'h3. \a'   ,
        'title4'                : 'h4. \a'   ,
        'title5'                : 'h5. \a'   ,
        'fontBoldOpen'          : '*'        ,
        'fontBoldClose'         : '*'        ,
        'fontItalicOpen'        : '_'        ,
        'fontItalicClose'       : '_'        ,
        'fontStrikeOpen'        : '-'        ,
        'fontStrikeClose'       : '-'        ,
        'fontUnderlineOpen'     : "+"        ,
        'fontUnderlineClose'    : "+"        ,
        'blockVerbOpen'         : '<pre>'    ,
        'blockVerbClose'        : '</pre>'   ,
        'blockQuoteLine'        : 'bq. '     ,  # XXX It's a *paragraph* prefix. (issues 64, 65)
        'fontMonoOpen'          : '@'        ,
        'fontMonoClose'         : '@'        ,
        'listItemLine'          : '*'        ,
        'numlistItemLine'       : '#'        ,
        'deflistItem1Open'      : '* '       ,
        'url'                   : '\a'       ,
        'urlMark'               : '"\a":\a'  ,  # "Google":http://www.google.com
        'email'                 : '\a'       ,
        'emailMark'             : '"\a":\a'  ,
        'img'                   : '!~A~\a!'  ,
        '_imgAlignLeft'         : ''         ,  # !image.png! (no align == left)
        '_imgAlignCenter'       : '='        ,  # !=image.png!
        '_imgAlignRight'        : '>'        ,  # !>image.png!
        'tableTitleCellOpen'    : '_.'       ,  # Table header is |_.header|
        'tableTitleCellSep'     : '|'        ,
        'tableCellOpen'         : '~S~~A~. ' ,
        'tableCellSep'          : '|'        ,
        'tableRowOpen'          : '|'        ,
        'tableRowClose'         : '|'        ,
        '_tableCellColSpan'     : '\\\a'     ,
        'bar1'                  : '---'      ,
        'bar2'                  : '---'      ,
        'TOC'                   : '{{toc}}'  ,
    },

    # http://www.inference.phy.cam.ac.uk/mackay/mgp/SYNTAX
    # http://en.wikipedia.org/wiki/MagicPoint
    'mgp': {
        'paragraphOpen'         : '%font "normal", size 5'     ,
        'title1'                : '%page\n\n\a\n'              ,
        'title2'                : '%page\n\n\a\n'              ,
        'title3'                : '%page\n\n\a\n'              ,
        'title4'                : '%page\n\n\a\n'              ,
        'title5'                : '%page\n\n\a\n'              ,
        'blockVerbOpen'         : '%font "mono"'               ,
        'blockVerbClose'        : '%font "normal"'             ,
        'blockQuoteOpen'        : '%prefix "       "'          ,
        'blockQuoteClose'       : '%prefix "  "'               ,
        'fontMonoOpen'          : '\n%cont, font "mono"\n'     ,
        'fontMonoClose'         : '\n%cont, font "normal"\n'   ,
        'fontBoldOpen'          : '\n%cont, font "normal-b"\n' ,
        'fontBoldClose'         : '\n%cont, font "normal"\n'   ,
        'fontItalicOpen'        : '\n%cont, font "normal-i"\n' ,
        'fontItalicClose'       : '\n%cont, font "normal"\n'   ,
        'fontUnderlineOpen'     : '\n%cont, fore "cyan"\n'     ,
        'fontUnderlineClose'    : '\n%cont, fore "white"\n'    ,
        'listItemLine'          : '\t'                         ,
        'numlistItemLine'       : '\t'                         ,
        'numlistItemOpen'       : '\a. '                       ,
        'deflistItem1Open'      : '\t\n%cont, font "normal-b"\n',
        'deflistItem1Close'     : '\n%cont, font "normal"\n'   ,
        'bar1'                  : '%bar "white" 5'             ,
        'bar2'                  : '%pause'                     ,
        'url'                   : '\n%cont, fore "cyan"\n\a'    +\
                                  '\n%cont, fore "white"\n'    ,
        'urlMark'               : '\a \n%cont, fore "cyan"\n\a' +\
                                  '\n%cont, fore "white"\n'    ,
        'email'                 : '\n%cont, fore "cyan"\n\a'    +\
                                  '\n%cont, fore "white"\n'    ,
        'emailMark'             : '\a \n%cont, fore "cyan"\n\a' +\
                                  '\n%cont, fore "white"\n'    ,
        'img'                   : '~A~\n%newimage "\a"\n%left\n',
        '_imgAlignLeft'         : '\n%left'                    ,
        '_imgAlignRight'        : '\n%right'                   ,
        '_imgAlignCenter'       : '\n%center'                  ,
        'comment'               : '%% \a'                      ,
        'pageBreak'             : '%page\n\n\n'                ,
        'EOD'                   : '%%EOD'
    },

    # man groff_man ; man 7 groff
    'man': {
        'paragraphOpen'         : '.P'     ,
        'title1'                : '.SH \a' ,
        'title2'                : '.SS \a' ,
        'title3'                : '.SS \a' ,
        'title4'                : '.SS \a' ,
        'title5'                : '.SS \a' ,
        'blockVerbOpen'         : '.nf'    ,
        'blockVerbClose'        : '.fi\n'  ,
        'blockQuoteOpen'        : '.RS'    ,
        'blockQuoteClose'       : '.RE'    ,
        'fontBoldOpen'          : '\\fB'   ,
        'fontBoldClose'         : '\\fR'   ,
        'fontItalicOpen'        : '\\fI'   ,
        'fontItalicClose'       : '\\fR'   ,
        'listOpen'              : '.RS'    ,
        'listItemOpen'          : '.IP \(bu 3\n',
        'listClose'             : '.RE'    ,
        'numlistOpen'           : '.RS'    ,
        'numlistItemOpen'       : '.IP \a. 3\n',
        'numlistClose'          : '.RE'    ,
        'deflistItem1Open'      : '.TP\n'  ,
        'bar1'                  : '\n\n'   ,
        'url'                   : '\a'     ,
        'urlMark'               : '\a (\a)',
        'email'                 : '\a'     ,
        'emailMark'             : '\a (\a)',
        'img'                   : '\a'     ,
        'tableOpen'             : '.TS\n~A~~B~tab(^); ~C~.',
        'tableClose'            : '.TE'     ,
        'tableRowOpen'          : ' '       ,
        'tableCellSep'          : '^'       ,
        '_tableAlignCenter'     : 'center, ',
        '_tableBorder'          : 'allbox, ',
        '_tableColAlignLeft'    : 'l'       ,
        '_tableColAlignRight'   : 'r'       ,
        '_tableColAlignCenter'  : 'c'       ,
        'comment'               : '.\\" \a'
    },

    # http://www.spip-contrib.net/Les-raccourcis-typographiques-en
    # http://www.spip-contrib.net/Carnet-Bac-a-Sable
    # some tags are not implemented by spip tags, but spip accept html tags.
    'spip': {
        'title1'                : '{{{ \a }}}' ,
        'title2'                : '<h4>\a</h4>',
        'title3'                : '<h5>\a</h5>',
        'blockVerbOpen'         : '<cadre>'    ,
        'blockVerbClose'        : '</cadre>'   ,
        'blockQuoteOpen'        : '<quote>'    ,
        'blockQuoteClose'       : '</quote>'   ,
        'fontMonoOpen'          : '<code>'     ,
        'fontMonoClose'         : '</code>'    ,
        'fontBoldOpen'          : '{{'         ,
        'fontBoldClose'         : '}}'         ,
        'fontItalicOpen'        : '{'          ,
        'fontItalicClose'       : '}'          ,
        'fontUnderlineOpen'     : '<u>'        ,
        'fontUnderlineClose'    : '</u>'       ,
        'fontStrikeOpen'        : '<del>'      ,
        'fontStrikeClose'       : '</del>'     ,
        'listItemOpen'          : '-'          ,  # -* list, -** sublist, -*** subsublist
        'listItemLine'          : '*'          ,
        'numlistItemOpen'       : '-'          ,  # -# list, -## sublist, -### subsublist
        'numlistItemLine'       : '#'          ,
        'bar1'                  : '----'       ,
        'url'                   : '[->\a]'     ,
        'urlMark'               : '[\a->\a]'   ,
        'email'                 : '[->\a]'     ,
        'emailMark'             : '[\a->\a]'   ,
        'img'                   : '<img src="\a" />',
        'imgAlignLeft'          : '<img src="\a" align="left" />',
        'imgAlignRight'         : '<img src="\a" align="right" />',
        'imgAlignCenter'        : '<img src="\a" align="center" />',
        'tableTitleRowOpen'     : '| {{'       ,
        'tableTitleRowClose'    : '}} |'       ,
        'tableTitleCellSep'     : '}} | {{'    ,
        'tableRowOpen'          : '| '         ,
        'tableRowClose'         : ' |'         ,
        'tableCellSep'          : ' | '        ,
        # TOC is automatic whith title1 when plugin "couteau suisse" is activate and the option "table des matieres" activate.
    },
    'pm6': {
        'paragraphOpen'         : '<@Normal:>'    ,
        'title1'                : '<@Title1:>\a',
        'title2'                : '<@Title2:>\a',
        'title3'                : '<@Title3:>\a',
        'title4'                : '<@Title4:>\a',
        'title5'                : '<@Title5:>\a',
        'blockVerbOpen'         : '<@PreFormat:>' ,
        'blockQuoteLine'        : '<@Quote:>'     ,
        'fontMonoOpen'          : '<FONT "Lucida Console"><SIZE 9>' ,
        'fontMonoClose'         : '<SIZE$><FONT$>',
        'fontBoldOpen'          : '<B>'           ,
        'fontBoldClose'         : '<P>'           ,
        'fontItalicOpen'        : '<I>'           ,
        'fontItalicClose'       : '<P>'           ,
        'fontUnderlineOpen'     : '<U>'           ,
        'fontUnderlineClose'    : '<P>'           ,
        'listOpen'              : '<@Bullet:>'    ,
        'listItemOpen'          : '\x95\t'        ,  # \x95 == ~U
        'numlistOpen'           : '<@Bullet:>'    ,
        'numlistItemOpen'       : '\x95\t'        ,
        'bar1'                  : '\a'            ,
        'url'                   : '<U>\a<P>'      ,  # underline
        'urlMark'               : '\a <U>\a<P>'   ,
        'email'                 : '\a'            ,
        'emailMark'             : '\a \a'         ,
        'img'                   : '\a'
    },
    # http://www.wikicreole.org/wiki/AllMarkup
    'creole': {
        'title1'               : '= \a ='        ,
        'title2'               : '== \a =='      ,
        'title3'               : '=== \a ==='    ,
        'title4'               : '==== \a ===='  ,
        'title5'               : '===== \a =====',
        'blockVerbOpen'        : '{{{'           ,
        'blockVerbClose'       : '}}}'           ,
        'blockQuoteLine'       : '  '            ,
    #   'fontMonoOpen'         : '##'            ,  # planned for 2.0,
    #   'fontMonoClose'        : '##'            ,  # meanwhile we disable it
        'fontBoldOpen'         : '**'            ,
        'fontBoldClose'        : '**'            ,
        'fontItalicOpen'       : '//'            ,
        'fontItalicClose'      : '//'            ,
        'fontUnderlineOpen'    : '//'            ,  # no underline in 1.0, planned for 2.0,
        'fontUnderlineClose'   : '//'            ,  # meanwhile we can use italic (emphasized)
    #   'fontStrikeOpen'       : '--'            ,  # planned for 2.0,
    #   'fontStrikeClose'      : '--'            ,  # meanwhile we disable it
        'listItemLine'          : '*'            ,
        'numlistItemLine'       : '#'            ,
        'deflistItem2LinePrefix': ':'            ,
        'bar1'                  : '----'         ,
        'url'                  : '[[\a]]'        ,
        'urlMark'              : '[[\a|\a]]'     ,
        'img'                  : '{{\a}}'        ,
        'tableTitleRowOpen'    : '|= '           ,
        'tableTitleRowClose'   : '|'             ,
        'tableTitleCellSep'    : ' |= '          ,
        'tableRowOpen'         : '| '            ,
        'tableRowClose'        : ' |'            ,
        'tableCellSep'         : ' | '           ,
        # TODO: placeholder (mark for unknown syntax)
        # if possible: http://www.wikicreole.org/wiki/Placeholder
    },
        # regular markdown: http://daringfireball.net/projects/markdown/syntax
        # markdown extra:   http://michelf.com/projects/php-markdown/extra/
        # sandbox:
        # http://daringfireball.net/projects/markdown/dingus
        # http://michelf.com/projects/php-markdown/dingus/
    'md': {
        'title1'               : '# \a '         ,
        'title2'               : '## \a '        ,
        'title3'               : '### \a '       ,
        'title4'               : '#### \a '      ,
        'title5'               : '##### \a '     ,
        'blockVerbLine'        : '    '          ,
        'blockQuoteLine'       : '> '            ,
        'fontMonoOpen'         : "`"             ,
        'fontMonoClose'        : "`"             ,
        'fontBoldOpen'         : "**"            ,
        'fontBoldClose'        : "**"            ,
        'fontItalicOpen'       : "*"             ,
        'fontItalicClose'      : "*"             ,
        'fontUnderlineOpen'    : ""              ,
        'fontUnderlineClose'   : ""              ,
        'fontStrikeOpen'       : ""              ,
        'fontStrikeClose'      : ""              ,
        # Lists
        #'listOpenCompact'             : '*'     ,
        'listItemLine'          : ' '            ,
        'listItemOpen'          : '*'            ,
        #'numlistItemLine'       : '1.'          ,
        'numlistItemOpen'       : '1.'           ,
        'deflistItem1Open'      : ': '           ,
        #'deflistItem1Close'     : ':'           ,
        #'deflistItem2LineOpen'  : '::'          ,
        #'deflistItem2LineClose' : ':'           ,
        # Verbatim block
        #'blockVerbOpen'        : ''             ,
        #'blockVerbClose'       : ''             ,
        'bar1'                 : '---'           ,
        'bar2'                 : '---'           ,
        # URL, email and anchor
        'url'                   : '\a'           ,
        'urlMark'               : '[\a](\a)'     ,
        'email'                 : '\a'           ,
        #'emailMark'             : '[[\a -> mailto:\a]]',
        #'anchor'                : '[[#\a]]\n'   ,
        # Image markup
        'img'                   : '![](\a)'      ,
        #'imgAlignLeft'         : '{{\a }}'      ,
        #'imgAlignRight'        : '{{ \a}}'      ,
        #'imgAlignCenter'       : '{{ \a }}'     ,
        # Table attributes
        'tableTitleRowOpen'    : '| '            ,
        'tableTitleRowClose'   : '|\n|---------------|'            ,
        'tableTitleCellSep'    : ' |'            ,
        'tableRowOpen'         : '|'             ,
        'tableRowClose'        : '|'             ,
        'tableCellSep'         : ' |'            ,
    },
        # http://www.phpbb.com/community/faq.php?mode=bbcode
        # http://www.bbcode.org/reference.php (but seldom implemented)
    'bbcode': {
        'title1'               : '[size=200]\a[/size]'             ,
        'title2'               : '[size=170]\a[/size]'             ,
        'title3'               : '[size=150]\a[/size]'             ,
        'title4'               : '[size=130]\a[/size]'             ,
        'title5'               : '[size=120]\a[/size]'             ,
        'blockQuoteOpen'       : '[quote]'         ,
        'blockQuoteClose'      : '[/quote]'        ,
        'fontMonoOpen'         : '[code]'          ,
        'fontMonoClose'        : '[/code]'         ,
        'fontBoldOpen'         : '[b]'             ,
        'fontBoldClose'        : '[/b]'            ,
        'fontItalicOpen'       : '[i]'             ,
        'fontItalicClose'      : '[/i]'            ,
        'fontUnderlineOpen'    : '[u]'             ,
        'fontUnderlineClose'   : '[/u]'            ,
        #'fontStrikeOpen'       : '[s]'            , (not supported by phpBB)
        #'fontStrikeClose'      : '[/s]'           ,
        'listOpen'             : '[list]'          ,
        'listClose'            : '[/list]'         ,
        'listItemOpen'         : '[*]'             ,
        #'listItemClose'        : '[/li]'          ,
        'numlistOpen'          : '[list=1]'        ,
        'numlistClose'         : '[/list]'         ,
        'numlistItemOpen'      : '[*]'             ,
        'url'                  : '[url]\a[/url]'   ,
        'urlMark'              : '[url=\a]\a[/url]',
        #'urlMark'              : '[url]\a[/url]',
        'img'                  : '[img]\a[/img]'   ,
        #'tableOpen'            : '[table]',
        #'tableClose'           : '[/table]'       ,
        #'tableRowOpen'         : '[tr]'           ,
        #'tableRowClose'        : '[/tr]'          ,
        #'tableCellOpen'        : '[td]'           ,
        #'tableCellClose'       : '[/td]'          ,
        #'tableTitleCellOpen'   : '[th]'           ,
        #'tableTitleCellClose'  : '[/th]'          ,
    },
    # http://en.wikipedia.org/wiki/Rich_Text_Format
    # Based on RTF Version 1.5 specification
    # Should be compatible with MS Word 97 and newer
    # ~D~ and ~L~ are used to encode depth and nesting level formatting
    'rtf': {
        'title1'                : '~A~{\\pard\\plain\\s11\\keepn{\\*\\txttags title1}\\f1\\fs24\\qc\\sb240\\sa240\\sl480\\slmult1\\li0\\ri0\\fi0{\\b{\a}}\\par}',
        'title2'                : '~A~{\\pard\\plain\\s12\\keepn{\\*\\txttags title2}\\f1\\fs24\\ql\\sb240\\sa240\\sl480\\slmult1\\li0\\ri0\\fi0{\\b{\a}}\\par}',
        'title3'                : '~A~{\\pard\\plain\\s13\\keepn{\\*\\txttags title3}\\f1\\fs24\\ql\\sb240\\sa240\\sl480\\slmult1\\li360\\ri0\\fi0{\\b{\a}}\\par}',
        'title4'                : '~A~{\\pard\\plain\\s14\\keepn{\\*\\txttags title4}\\f1\\fs24\\ql\\sb240\\sa240\\sl480\\slmult1\\li360\\ri0\\fi0{\\b\\i{\a}}\\par}',
        'title5'                : '~A~{\\pard\\plain\\s15\\keepn{\\*\\txttags title5}\\f1\\fs24\\ql\\sb240\\sa240\\sl480\\slmult1\\li360\\ri0\\fi0{\\i{\a}}\\par}',
        'numtitle1'             : '~A~{\\pard\\plain\\s11\\keepn{\\*\\txttags title1}\\f1\\fs24\\qc\\sb240\\sa240\\sl480\\slmult1\\li0\\ri0\\fi0\\ls3\\ilvl0{\\b{\a}}\\par}',
        'numtitle2'             : '~A~{\\pard\\plain\\s12\\keepn{\\*\\txttags title2}\\f1\\fs24\\ql\\sb240\\sa240\\sl480\\slmult1\\li0\\ri0\\fi0\\ls3\\ilvl1{\\b{\a}}\\par}',
        'numtitle3'             : '~A~{\\pard\\plain\\s13\\keepn{\\*\\txttags title3}\\f1\\fs24\\ql\\sb240\\sa240\\sl480\\slmult1\\li360\\ri0\\fi0\\ls3\\ilvl2{\\b{\a}}\\par}',
        'numtitle4'             : '~A~{\\pard\\plain\\s14\\keepn{\\*\\txttags title4}\\f1\\fs24\\ql\\sb240\\sa240\\sl480\\slmult1\\li360\\ri0\\fi0\\ls3\\ilvl3{\\b\\i{\a}}\\par}',
        'numtitle5'             : '~A~{\\pard\\plain\\s15\\keepn{\\*\\txttags title5}\\f1\\fs24\\ql\\sb240\\sa240\\sl480\\slmult1\\li360\\ri0\\fi0\\ls3\\ilvl4{\\i{\a}}\\par}',
        'paragraphOpen'         : '{\\pard\\plain\\s2{\\*\\txttags paragraph}\\f0\\fs24\\qj\\sb0\\sa0\\sl480\\slmult1\\li~D~\\ri0\\fi360',
        'paragraphClose'        : '\\par}',
        'blockVerbOpen'         : '{\\pard\\plain\\s3{\\*\\txttags verbatim}\\f2\\fs20\\ql\\sb0\\sa240\\sl240\\slmult1\\li720\\ri720\\fi0',
        'blockVerbSep'          : '\\line',
        'blockVerbClose'        : '\\par}',
        'blockQuoteOpen'        : '{\\pard\\plain\\s4{\\*\\txttags quote}\\f0\\fs24\\qj\\sb0\\sa0\\sl480\\slmult1\\li~D~\\ri720\\fi0',
        'blockQuoteClose'       : '\\par}',
        'fontMonoOpen'          : '{\\f2\\fs20{',
        'fontMonoClose'         : '}}',
        'fontBoldOpen'          : '{\\b{',
        'fontBoldClose'         : '}}',
        'fontItalicOpen'        : '{\\i{',
        'fontItalicClose'       : '}}',
        'fontUnderlineOpen'     : '{\\ul{',
        'fontUnderlineClose'    : '}}',
        'fontStrikeOpen'        : '{\\strike{',
        'fontStrikeClose'       : '}}',
        'anchor'                : '{\\*\\bkmkstart \a}{\\*\\bkmkend \a}',
        # 'comment'               : '{\\v \a }',  # doesn't hide text in all readers
        'pageBreak'             : '\\page\n',
        'EOD'                   : '}',
        'url'                   : '{\\field{\\*\\fldinst{HYPERLINK "\a"}}{\\fldrslt{\\ul\\cf1 \a}}}',
        'urlMark'               : '{\\field{\\*\\fldinst{HYPERLINK "\a"}}{\\fldrslt{\\ul\\cf1 \a}}}',
        'email'                 : '{\\field{\\*\\fldinst{HYPERLINK "mailto:\a"}}{\\fldrslt{\\ul\\cf1 \a}}}',
        'emailMark'             : '{\\field{\\*\\fldinst{HYPERLINK "mailto:\a"}}{\\fldrslt{\\ul\\cf1 \a}}}',
        'img'                   : '{\\field{\\*\\fldinst{INCLUDEPICTURE "\a" \\\\* MERGEFORMAT \\\\d}}{\\fldrslt{(\a)}}}',
        'imgEmbed'              : '{\*\shppict{\pict\a}}',
        'listOpen'              : '{\\pard\\plain\\s21{\\*\\txttags list}\\f0\\fs24\\qj\\sb0\\sa0\\sl480\\slmult1',
        'listClose'             : '}',
        'listItemOpen'          : '{\\*\\listtext{\\*\\txttags list indent}\\li~D~\\ri0\\fi-360\\\'95\\tab}\\ls1\\ilvl~L~{\\*\\txttags list indent}\\li~D~\\ri0\\fi-360\n',
        'listItemClose'         : '\\par',
        'numlistOpen'           : '{\\pard\\plain\\s21{\\*\\txttags list}\\f0\\fs24\\qj\\sb0\\sa0\\sl480\\slmult1',
        'numlistClose'          : '}',
        'numlistItemOpen'       : '{\\*\\listtext{\\*\\txttags list indent}\\li~D~\\ri0\\fi-360 \a.\\tab}\\ls2\\ilvl~L~{\\*\\txttags list indent}\\li~D~\\ri0\\fi-360\n',
        'numlistItemClose'      : '\\par',
        'deflistOpen'           : '{\\pard\\plain\\s21{\\*\\txttags list}\\f0\\fs24\\qj\\sb0\\sa0\\sl480\\slmult1',
        'deflistClose'          : '}',
        'deflistItem1Open'      : '{\\*\\txttags list indent}\\li~D~\\ri0\\fi-360{\\b\n',
        'deflistItem1Close'     : ':}\\tab',
        'deflistItem2Open'      : '',
        'deflistItem2Close'     : '\\par',
        'tableOpen'             : '{\\pard\\plain',
        'tableClose'            : '\\par}',
        'tableRowOpen'          : '{\\trowd\\trgaph60~A~~B~',
        'tableRowClose'         : '\\row}',
        'tableRowSep'           : '',
        'tableTitleRowOpen'     : '{\\trowd\\trgaph60\\trhdr~A~~B~\\trbrdrt\\brdrs\\brdrw20\\trbrdrb\\brdrs\\brdrw20',
        'tableTitleRowClose'    : '',
        'tableCellOpen'         : '{\\intbl\\itap1\\f0\\fs20~A~ ',
        'tableCellClose'        : '\\cell}',
        'tableCellHead'         : '~B~~S~',
        'tableTitleCellOpen'    : '{\\intbl\\itap1\\f0\\fs20~A~\\b ',
        'tableTitleCellClose'   : '\\cell}',
        'tableTitleCellHead'    : '~B~\\clbrdrt\\brdrs\\brdrw20\\clbrdrb\\brdrs\\brdrw20~S~',
        '_tableCellColSpan'     : '\\cellx\a',
        '_tableAlignLeft'       : '\\trql',
        '_tableAlignCenter'     : '\\trqc',
        '_tableBorder'          : '\\trbrdrt\\brdrs\\brdrw10\\trbrdrb\\brdrs\\brdrw10\\trbrdrl\\brdrs\\brdrw10\\trbrdrr\\brdrs\\brdrw10',
        '_tableCellAlignLeft'   : '\\ql',
        '_tableCellAlignRight'  : '\\qr',
        '_tableCellAlignCenter' : '\\qc',
        '_tableCellBorder'      : '\\clbrdrt\\brdrs\\brdrw10\\clbrdrb\\brdrs\\brdrw10\\clbrdrl\\brdrs\\brdrw10\\clbrdrr\\brdrs\\brdrw10',
        'bar1'                  : '{\\pard\\plain\\s1\\brdrt\\brdrs\\brdrw10\\li1400\\sb120\\sa120\\ri1400\\fs12\\par}',
        'bar2'                  : '{\\pard\\plain\\s1\\brdrt\\brdrs\\brdrdb\\brdrw10\\sb120\\sa120\\li1400\\ri1400\\fs12\\par}'
    },
    }

    # Exceptions for --css-sugar
    if config['css-sugar'] and config['target'] in ('html', 'xhtml', 'xhtmls'):
        # Change just HTML because XHTML inherits it
        htmltags = alltags['html']
        # Table with no cellpadding
        htmltags['tableOpen'] = htmltags['tableOpen'].replace(' CELLPADDING="4"', '')
        # DIVs
        htmltags['tocOpen'] = '<DIV CLASS="toc">'
        htmltags['tocClose'] = '</DIV>'
        htmltags['bodyOpen'] = '<DIV CLASS="body" ID="body">'
        htmltags['bodyClose'] = '</DIV>'

    # Make the HTML -> XHTML inheritance
    xhtml = alltags['html'].copy()
    for key in list(xhtml.keys()):
        xhtml[key] = xhtml[key].lower()
    # Some like HTML tags as lowercase, some don't... (headers out)
    if HTML_LOWER:
        alltags['html'] = xhtml.copy()
    if config['target'] in ('xhtml', 'xhtmls', 'html5'):
        xhtml.update(alltags[config['target']])
        alltags[config['target']] = xhtml.copy()

    if config['target'] == 'aat' and config['slides']:
        alltags['aat']['urlMark'] = alltags['aat']['emailMark'] = '\a (\a)'
        alltags['aat']['bar1'] = aa_line(AA['bar1'], config['width'] - 2)
        alltags['aat']['bar2'] = aa_line(AA['bar2'], config['width'] - 2)
        if not config['chars']:
            alltags['aat']['listItemOpen'] = '* '
    if config['target'] == 'aat' and config['web']:
        alltags['aat']['url'] = alltags['aat']['urlMark'] = '<a href="\a">\a</a>'
        alltags['aat']['email'] = alltags['aat']['emailMark'] = '<a href="mailto:\a">\a</a>'
        alltags['aat']['img'] = '<img src="\a" alt=""/>'
        alltags['aat']['anchor'] = '<a id="\a">'
        for beautifier  in ['Bold', 'Italic', 'Underline', 'Strike']:
            open, close = 'font' + beautifier + 'Open', 'font' + beautifier + 'Close'
            alltags['aat'][open], alltags['aat'][close] = alltags['html'][open].lower(), alltags['html'][close].lower()

    # Compose the target tags dictionary
    tags = {}
    target_tags = alltags[config['target']].copy()

    for key in keys:
        tags[key] = ''  # create empty keys
    for key in list(target_tags.keys()):
        tags[key] = maskEscapeChar(target_tags[key])  # populate

    # Map strong line to pagebreak
    if rules['mapbar2pagebreak'] and tags['pageBreak']:
        tags['bar2'] = tags['pageBreak']

    # Change img tag if embedding images in RTF
    if config['embed-images']:
        if tags.get('imgEmbed'):
            tags['img'] = tags['imgEmbed']
        else:
            Error(_("Invalid --embed-images option with target '%s'." % config['target']))

    # Map strong line to separator if not defined
    if not tags['bar2'] and tags['bar1']:
        tags['bar2'] = tags['bar1']

    return tags


##############################################################################


def getRules(config):
    "Returns all the target-specific syntax rules"

    ret = {}
    allrules = [

        # target rules (ON/OFF)
        'linkable',               # target supports external links
        'tableable',              # target supports tables
        'imglinkable',            # target supports images as links
        'imgalignable',           # target supports image alignment
        'imgasdefterm',           # target supports image as definition term
        'autonumberlist',         # target supports numbered lists natively
        'autonumbertitle',        # target supports numbered titles natively
        'stylable',               # target supports external style files
        'parainsidelist',         # lists items supports paragraph
        'compactlist',            # separate enclosing tags for compact lists
        'spacedlistitem',         # lists support blank lines between items
        'listnotnested',          # lists cannot be nested
        'listitemnotnested',      # list items must be closed before nesting lists
        'quotenotnested',         # quotes cannot be nested
        'verbblocknotescaped',    # don't escape specials in verb block
        'verbblockfinalescape',   # do final escapes in verb block
        'escapeurl',              # escape special in link URL
        'labelbeforelink',        # label comes before the link on the tag
        'onelinepara',            # dump paragraph as a single long line
        'tabletitlerowinbold',    # manually bold any cell on table titles
        'tablecellstrip',         # strip extra spaces from each table cell
        'tablecellspannable',     # the table cells can have span attribute
        'tablecellmulticol',      # separate open+close tags for multicol cells
        'barinsidequote',         # bars are allowed inside quote blocks
        'finalescapetitle',       # perform final escapes on title lines
        'autotocnewpagebefore',   # break page before automatic TOC
        'autotocnewpageafter',    # break page after automatic TOC
        'autotocwithbars',        # automatic TOC surrounded by bars
        'mapbar2pagebreak',       # map the strong bar to a page break
        'titleblocks',            # titles must be on open/close section blocks
        'listlineafteropen',      # put listItemLine after listItemOpen
        'escapexmlchars',         # escape the XML special chars: < > &
        'listlevelzerobased',     # list levels start at 0 when encoding into tags
        'zerodepthparagraph',     # non-nested paras have block depth of 0 instead of 1
        'cellspancumulative',     # cell span value adds up for each cell of a row
        'keepblankheaderline',    # template lines are not removed if headers are blank

        # Target code beautify (ON/OFF)
        'indentverbblock',        # add leading spaces to verb block lines
        'breaktablecell',         # break lines after any table cell
        'breaktablelineopen',     # break line after opening table line
        'notbreaklistopen',       # don't break line after opening a new list
        'keepquoteindent',        # don't remove the leading TABs on quotes
        'keeplistindent',         # don't remove the leading spaces on lists
        'blankendautotoc',        # append a blank line at the auto TOC end
        'tagnotindentable',       # tags must be placed at the line beginning
        'spacedlistitemopen',     # append a space after the list item open tag
        'spacednumlistitemopen',  # append a space after the numlist item open tag
        'deflisttextstrip',       # strip the contents of the deflist text
        'blanksaroundpara',       # put a blank line before and after paragraphs
        'blanksaroundverb',       # put a blank line before and after verb blocks
        'blanksaroundquote',      # put a blank line before and after quotes
        'blanksaroundlist',       # put a blank line before and after lists
        'blanksaroundnumlist',    # put a blank line before and after numlists
        'blanksarounddeflist',    # put a blank line before and after deflists
        'blanksaroundnestedlist', # put a blank line before and after all type of nested lists
        'blanksaroundtable',      # put a blank line before and after tables
        'blanksaroundbar',        # put a blank line before and after bars
        'blanksaroundtitle',      # put a blank line before and after titles
        'blanksaroundnumtitle',   # put a blank line before and after numtitles

        # Value settings
        'listmaxdepth',           # maximum depth for lists
        'quotemaxdepth',          # maximum depth for quotes
        'tablecellaligntype',     # type of table cell align: cell, column
        'blockdepthmultiply',     # block depth multiple for encoding
        'depthmultiplyplus',      # add to block depth before multiplying
        'cellspanmultiplier',     # cell span is multiplied by this value
    ]

    rules_bank = {
        'txt': {
            'indentverbblock': 1,
            'spacedlistitem': 1,
            'parainsidelist': 1,
            'keeplistindent': 1,
            'barinsidequote': 1,
            'autotocwithbars': 1,

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'txt2t': {
            'linkable': 1,
            'tableable': 1,
            'imglinkable': 1,
            # 'imgalignable',
            'imgasdefterm': 1,
            'autonumberlist': 1,
            'autonumbertitle': 1,
            'stylable': 1,
            'spacedlistitem': 1,
            'labelbeforelink': 1,
            'tablecellstrip': 1,
            'tablecellspannable': 1,
            'keepblankheaderline': 1,
            'barinsidequote': 1,
            'keeplistindent': 1,
            'blankendautotoc': 1,
            'blanksaroundpara': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
            'tablecellaligntype': 'cell',
        },
        'rst': {
            'indentverbblock': 1,
            'spacedlistitem': 1,
            'parainsidelist': 1,
            'keeplistindent': 1,
            'barinsidequote': 1,
            'imgalignable': 1,
            'imglinkable': 1,
            'tableable': 1,

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
            'blanksaroundnestedlist': 1,
        },
        'aat': {
            #TIP art inherits all TXT rules
        },
        'csv': {
            'tableable': 1,
        },
        'ods': {
            'escapexmlchars': 1,
            'tableable': 1,
            'tablecellstrip': 1,
        },
        'html': {
            'escapexmlchars': 1,
            'indentverbblock': 1,
            'linkable': 1,
            'stylable': 1,
            'escapeurl': 1,
            'imglinkable': 1,
            'imgalignable': 1,
            'imgasdefterm': 1,
            'autonumberlist': 1,
            'spacedlistitem': 1,
            'parainsidelist': 1,
            'tableable': 1,
            'tablecellstrip': 1,
            'breaktablecell': 1,
            'breaktablelineopen': 1,
            'keeplistindent': 1,
            'keepquoteindent': 1,
            'barinsidequote': 1,
            'autotocwithbars': 1,
            'tablecellspannable': 1,
            'tablecellaligntype': 'cell',

            # 'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            # 'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'xhtml': {
            #TIP xhtml inherits all HTML rules
        },

        'xhtmls': {
            #TIP xhtmls inherits all HTML rules
        },
        'html5': {
            #TIP html5 inherits all HTML rules
        },

        'sgml': {
            'escapexmlchars': 1,
            'linkable': 1,
            'escapeurl': 1,
            'autonumberlist': 1,
            'spacedlistitem': 1,
            'tableable': 1,
            'tablecellstrip': 1,
            'blankendautotoc': 1,
            'keeplistindent': 1,
            'keepquoteindent': 1,
            'barinsidequote': 1,
            'finalescapetitle': 1,
            'tablecellaligntype': 'column',

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
            'quotemaxdepth': 1,
        },
        'dbk': {
            'escapexmlchars': 1,
            'linkable': 1,
            'tableable': 1,  # activate when table tags are ready
            'imglinkable': 1,
            'imgalignable': 1,
            'imgasdefterm': 1,
            'autonumberlist': 1,
            'autonumbertitle': 1,
            'parainsidelist': 1,
            'spacedlistitem': 1,
            'titleblocks': 1,
        },
        'mgp': {
            'tagnotindentable': 1,
            'spacedlistitem': 1,
            'imgalignable': 1,
            'autotocnewpagebefore': 1,

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            # 'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'tableable': 1,
            # 'blanksaroundtitle': 1,
            # 'blanksaroundnumtitle': 1,
        },
        'tex': {
            'stylable': 1,
            'escapeurl': 1,
            'autonumberlist': 1,
            'autonumbertitle': 1,
            'spacedlistitem': 1,
            'compactlist': 1,
            'parainsidelist': 1,
            'tableable': 1,
            'tablecellstrip': 1,
            'tabletitlerowinbold': 1,
            'verbblocknotescaped': 1,
            'keeplistindent': 1,
            'listmaxdepth': 4,  # deflist is 6
            'quotemaxdepth': 6,
            'barinsidequote': 1,
            'finalescapetitle': 1,
            'autotocnewpageafter': 1,
            'mapbar2pagebreak': 1,
            'tablecellaligntype': 'column',
            'tablecellmulticol': 1,

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            # 'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'lout': {
            'keepquoteindent': 1,
            'deflisttextstrip': 1,
            'escapeurl': 1,
            'verbblocknotescaped': 1,
            'imgalignable': 1,
            'mapbar2pagebreak': 1,
            'titleblocks': 1,
            'autonumberlist': 1,
            'parainsidelist': 1,

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            # 'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'moin': {
            'spacedlistitem': 1,
            'linkable': 1,
            'keeplistindent': 1,
            'tableable': 1,
            'barinsidequote': 1,
            'tabletitlerowinbold': 1,
            'tablecellstrip': 1,
            'autotocwithbars': 1,
            'tablecellspannable': 1,
            'tablecellaligntype': 'cell',
            'deflisttextstrip': 1,

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            # 'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            # 'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'gwiki': {
            'spacedlistitem': 1,
            'linkable': 1,
            'keeplistindent': 1,
            'tableable': 1,
            'tabletitlerowinbold': 1,
            'tablecellstrip': 1,
            'autonumberlist': 1,

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            # 'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            # 'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'adoc': {
            'spacedlistitem': 1,
            'linkable': 1,
            'keeplistindent': 1,
            'autonumberlist': 1,
            'autonumbertitle': 1,
            'listnotnested': 1,
            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'doku': {
            'indentverbblock': 1,  # DokuWiki uses '  ' to mark verb blocks
            'spacedlistitem': 1,
            'linkable': 1,
            'keeplistindent': 1,
            'tableable': 1,
            'barinsidequote': 1,
            'tablecellstrip': 1,
            'autotocwithbars': 1,
            'autonumberlist': 1,
            'imgalignable': 1,
            'tablecellaligntype': 'cell',

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            # 'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'pmw': {
            'indentverbblock': 1,
            'spacedlistitem': 1,
            'linkable': 1,
            'labelbeforelink': 1,
            # 'keeplistindent': 1,
            'tableable': 1,
            'barinsidequote': 1,
            'tablecellstrip': 1,
            'autotocwithbars': 1,
            'autonumberlist': 1,
            'spacedlistitemopen': 1,
            'spacednumlistitemopen': 1,
            'imgalignable': 1,
            'tabletitlerowinbold': 1,
            'tablecellaligntype': 'cell',

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'wiki': {
            'escapexmlchars': 1,
            'linkable': 1,
            'tableable': 1,
            'tablecellstrip': 1,
            'autotocwithbars': 1,
            'spacedlistitemopen': 1,
            'spacednumlistitemopen': 1,
            'deflisttextstrip': 1,
            'autonumberlist': 1,
            'imgalignable': 1,
            'tablecellspannable': 1,
            'tablecellaligntype': 'cell',

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            # 'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'red': {
            'linkable': 1,
            'tableable': 1,
            'tablecellstrip': 1,
            'tablecellspannable': 1,
            'tablecellaligntype': 'cell',
            'autotocwithbars': 1,
            'spacedlistitemopen': 1,
            'spacednumlistitemopen': 1,
            'deflisttextstrip': 1,
            'autonumberlist': 1,
            'imgalignable': 1,
            'labelbeforelink': 1,
            'quotemaxdepth': 1,
            'autonumbertitle': 1,
            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            # 'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'man': {
            'spacedlistitem': 1,
            'tagnotindentable': 1,
            'tableable': 1,
            'tablecellaligntype': 'column',
            'tabletitlerowinbold': 1,
            'tablecellstrip': 1,
            'barinsidequote': 1,
            'parainsidelist': 0,

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            # 'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            # 'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'pm6': {
            'keeplistindent': 1,
            'verbblockfinalescape': 1,
            #TODO add support for these
            # maybe set a JOINNEXT char and do it on addLineBreaks()
            'notbreaklistopen': 1,
            'barinsidequote': 1,
            'autotocwithbars': 1,
            'onelinepara': 1,

            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            # 'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            # 'blanksaroundtable': 1,
            # 'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'creole': {
            'linkable': 1,
            'tableable': 1,
            'imglinkable': 1,
            'tablecellstrip': 1,
            'autotocwithbars': 1,
            'spacedlistitemopen': 1,
            'spacednumlistitemopen': 1,
            'deflisttextstrip': 1,
            'verbblocknotescaped': 1,
            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
        },
        'md': {
            #'keeplistindent': 1,
            'linkable': 1,
            'labelbeforelink': 1,
            'tableable': 1,
            'imglinkable': 1,
            'tablecellstrip': 1,
            'autonumberlist': 1,
            'spacedlistitemopen': 1,
            'spacednumlistitemopen': 1,
            'deflisttextstrip': 1,
            'blanksaroundpara': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            #'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
        },
        'bbcode': {
            #'keeplistindent': 1,
            'keepquoteindent': 1,
            #'indentverbblock': 1,
            'linkable': 1,
            #'labelbeforelink': 1,
            #'tableable': 1,
            'imglinkable': 1,
            'tablecellstrip': 1,
            #'autotocwithbars': 1,
            'autonumberlist': 1,
            'spacedlistitemopen': 1,
            'spacednumlistitemopen': 1,
            'deflisttextstrip': 1,
            #'verbblocknotescaped': 1,
            'blanksaroundpara': 1,
            #'blanksaroundverb': 1,
            #'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            #'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
        },
        'spip': {
            'spacedlistitem': 1,
            'spacedlistitemopen': 1,
            'linkable': 1,
            'blankendmotherlist': 1,
            'tableable': 1,
            'barinsidequote': 1,
            'keepquoteindent': 1,
            'blankendtable': 1,
            'tablecellstrip': 1,
            'imgalignable': 1,
            'tablecellaligntype': 'cell',
            'listlineafteropen': 1,
            'labelbeforelink': 1,
            'blanksaroundpara': 1,
            'blanksaroundverb': 1,
            'blanksaroundquote': 1,
            'blanksaroundlist': 1,
            'blanksaroundnumlist': 1,
            'blanksarounddeflist': 1,
            'blanksaroundtable': 1,
            'blanksaroundbar': 1,
            'blanksaroundtitle': 1,
            'blanksaroundnumtitle': 1,
        },
        'rtf': {
            'linkable': 1,
            'tableable': 1,
            'autonumbertitle': 1,
            'parainsidelist': 1,
            'listnotnested': 1,
            'listitemnotnested': 1,
            'quotenotnested': 1,
            'onelinepara': 1,
            'tablecellstrip': 1,
            'tablecellspannable': 1,
            'tagnotindentable': 1,
            'deflisttextstrip': 1,
            'encodeblockdepth': 1,
            'zerodepthparagraph': 1,
            'cellspancumulative': 1,
            'blockdepthmultiply': 360,
            'depthmultiplyplus': 1,
            'cellspanmultiplier': 1080,
            'listmaxdepth': 9,
            'tablecellaligntype': 'cell',
        },
    }

    # Exceptions for --css-sugar
    if config['css-sugar'] and config['target'] in ('html', 'xhtml', 'xhtmls', 'html5'):
        rules_bank['html']['indentverbblock'] = 0
        rules_bank['html']['autotocwithbars'] = 0
    # Get the target specific rules
    if config['target'] in ('xhtml', 'xhtmls', 'html5'):
        myrules = rules_bank['html'].copy()   # inheritance
        myrules.update(rules_bank[config['target']])   # get specific
    elif config['target'] == 'aat':
        myrules = rules_bank['txt'].copy()    # inheritance
        myrules['tableable'] = 1
        if config['slides']:
            myrules['blanksaroundtitle'] = 0
            myrules['blanksaroundnumtitle'] = 0
            myrules['blanksaroundlist'] = 0
            myrules['blanksaroundnumlist'] = 0
            myrules['blanksarounddeflist'] = 0
        if config['web']:
            myrules['linkable'] = 1
            myrules['imglinkable'] = 1
            myrules['escapexmlchars'] = 1
    else:
        myrules = rules_bank[config['target']].copy()

    # Populate return dictionary
    for key in allrules:
        ret[key] = 0                         # reset all
    ret.update(myrules)                      # get rules

    return ret


##############################################################################

def getRegexes():
    "Returns all the regexes used to find the t2t marks"

    bank = {
    'blockVerbOpen':
        re.compile(r'^```\s*$'),
    'blockVerbClose':
        re.compile(r'^```\s*$'),
    'blockRawOpen':
        re.compile(r'^"""\s*$'),
    'blockRawClose':
        re.compile(r'^"""\s*$'),
    'blockTaggedOpen':
        re.compile(r"^'''\s*$"),
    'blockTaggedClose':
        re.compile(r"^'''\s*$"),
    'blockCommentOpen':
        re.compile(r'^%%%\s*$'),
    'blockCommentClose':
        re.compile(r'^%%%\s*$'),
    'quote':
        re.compile(r'^\t+'),
    '1lineVerb':
        re.compile(r'^``` (?=.)'),
    '1lineRaw':
        re.compile(r'^""" (?=.)'),
    '1lineTagged':
        re.compile(r"^''' (?=.)"),
    # mono, raw, bold, italic, underline:
    # - marks must be glued with the contents, no boundary spaces
    # - they are greedy, so in ****bold****, turns to <b>**bold**</b>
    'fontMono':
        re.compile(r'``([^\s](|.*?[^\s])`*)``'),
    'raw':
        re.compile(r'""([^\s](|.*?[^\s])"*)""'),
    'tagged':
        re.compile(r"''([^\s](|.*?[^\s])'*)''"),
    'fontBold':
        re.compile(r'\*\*([^\s](|.*?[^\s])\**)\*\*'),
    'fontItalic':
        re.compile(r'//([^\s](|.*?[^\s])/*)//'),
    'fontUnderline':
        re.compile(r'__([^\s](|.*?[^\s])_*)__'),
    'fontStrike':
        re.compile(r'--([^\s](|.*?[^\s])-*)--'),
    'list':
        re.compile(r'^( *)(-) (?=[^ ])'),
    'numlist':
        re.compile(r'^( *)(\+) (?=[^ ])'),
    'deflist':
        re.compile(r'^( *)(:) (.*)$'),
    'listclose':
        re.compile(r'^( *)([-+:])\s*$'),
    'bar':
        re.compile(r'^(\s*)([_=-]{20,})\s*$'),
    'table':
        re.compile(r'^ *\|\|? '),
    'blankline':
        re.compile(r'^\s*$'),
    'comment':
        re.compile(r'^%'),

    # Auxiliary tag regexes
    '_imgAlign'          : re.compile(r'~A~', re.I),
    '_tableAlign'        : re.compile(r'~A~', re.I),
    '_anchor'            : re.compile(r'~A~', re.I),
    '_tableBorder'       : re.compile(r'~B~', re.I),
    '_tableColAlign'     : re.compile(r'~C~', re.I),
    '_tableCellColSpan'  : re.compile(r'~S~', re.I),
    '_tableCellAlign'    : re.compile(r'~A~', re.I),
    '_tableAttrDelimiter': re.compile(r'~Z~', re.I),
    '_blockDepth'        : re.compile(r'~D~', re.I),
    '_listLevel'         : re.compile(r'~L~', re.I),
    }

    # Special char to place data on TAGs contents  (\a == bell)
    bank['x'] = re.compile('\a')

    # %%macroname [ (formatting) ]
    bank['macros'] = re.compile(r'%%%%(?P<name>%s)\b(\((?P<fmt>.*?)\))?' % (
        '|'.join(list(MACROS.keys()))), re.I)

    # %%TOC special macro for TOC positioning
    bank['toc'] = re.compile(r'^ *%%toc\s*$', re.I)

    # Almost complicated title regexes ;)
    titskel = r'^ *(?P<id>%s)(?P<txt>%s)\1(\[(?P<label>[\w-]*)\])?\s*$'
    bank['title']    = re.compile(titskel % ('[=]{1,5}', '[^=](|.*[^=])'))
    bank['numtitle'] = re.compile(titskel % ('[+]{1,5}', '[^+](|.*[^+])'))

    ### Complicated regexes begin here ;)
    #
    # Textual descriptions on --help's style: [...] is optional, | is OR

    ### First, some auxiliary variables
    #

    # [image.EXT]
    patt_img = r'\[([\w_,.+%$#@!?+~/-]+\.(png|jpe?g|gif|eps|bmp))\]'

    # Link things
    # http://www.gbiv.com/protocols/uri/rfc/rfc3986.html
    # pchar: A-Za-z._~- / %FF / !$&'()*+,;= / :@
    # Recomended order: scheme://user:pass@domain/path?query=foo#anchor
    # Also works      : scheme://user:pass@domain/path#anchor?query=foo
    # TODO form: !'():
    urlskel = {
        'proto' : r'(https?|ftp|news|telnet|gopher|wais)://',
        'guess' : r'(www[23]?|ftp)\.',         # w/out proto, try to guess
        'login' : r'A-Za-z0-9_.-',             # for ftp://login@domain.com
        'pass'  : r'[^ @]*',                   # for ftp://login:pass@dom.com
        'chars' : r'A-Za-z0-9%._/~:,=$@&+-',   # %20(space), :80(port), D&D
        'anchor': r'A-Za-z0-9%._-',            # %nn(encoded)
        'form'  : r'A-Za-z0-9/%&=+:;.,$@*_-',  # .,@*_-(as is)
        'punct' : r'.,;:!?'
    }

    # username [ :password ] @
    patt_url_login = r'([%s]+(:%s)?@)?' % (urlskel['login'], urlskel['pass'])

    # [ http:// ] [ username:password@ ] domain.com [ / ]
    #     [ #anchor | ?form=data ]
    retxt_url = r'\b(%s%s|%s)[%s]+\b/*(\?[%s]+)?(#[%s]*)?' % (
        urlskel['proto'], patt_url_login, urlskel['guess'],
        urlskel['chars'], urlskel['form'], urlskel['anchor'])

    # filename | [ filename ] #anchor
    retxt_url_local = r'[%s]+|[%s]*(#[%s]*)' % (
        urlskel['chars'], urlskel['chars'], urlskel['anchor'])

    # user@domain [ ?form=data ]
    patt_email = r'\b[%s]+@([A-Za-z0-9_-]+\.)+[A-Za-z]{2,4}\b(\?[%s]+)?' % (
        urlskel['login'], urlskel['form'])

    # Saving for future use
    bank['_urlskel'] = urlskel

    ### And now the real regexes
    #

    bank['email'] = re.compile(patt_email, re.I)

    # email | url
    bank['link'] = re.compile(r'%s|%s' % (retxt_url, patt_email), re.I)

    # \[ label | imagetag    url | email | filename \]
    bank['linkmark'] = re.compile(
        r'\[(?P<label>%s|[^]]+) (?P<link>%s|%s|%s)\]' % (
            patt_img, retxt_url, patt_email, retxt_url_local),
        re.L + re.I)

    # Image
    bank['img'] = re.compile(patt_img, re.L + re.I)

    # Special things
    bank['special'] = re.compile(r'^%!\s*')
    return bank
### END OF regex nightmares

################# functions for the ASCII Art backend ########################


def aa_line(char, width):
    return char * width


def aa_under(txt, char, width, over):
    ret = []
    if over:
        ret.append(aa_line(char, aa_len_cjk(txt)))
    for line in textwrap.wrap(txt, width):
        ret.extend([line, aa_line(char, aa_len_cjk(line))])
    return ret


def aa_box(txt, chars, width, centred=True):
    wrap_txt = []
    for line in txt:
        wrap_txt.extend(el for el in textwrap.wrap(line, width - 4))
    len_cjk = max([aa_len_cjk(line) for line in wrap_txt])
    line_box = aa_center(chars['corner'] + chars['border'] * (len_cjk + 2) + chars['corner'], width)
    line_txt = []
    for line in wrap_txt:
        if centred:
            line_txt.append(aa_center(chars['side'] + ' ' + aa_center(line, len_cjk) + ' ' + chars['side'], width))
        else:
            line_txt.append(aa_center(chars['side'] + ' ' + line + ' ' * (len_cjk - aa_len_cjk(line) + 1) + chars['side'], width))
    return [line_box] + line_txt + [line_box]


def aa_header(header_data, chars, width, n, end, web):
    header = [aa_line(chars['bar2'], width)]
    header.extend([''] * n)
    for h in 'HEADER1', 'HEADER2', 'HEADER3':
        if header_data[h]:
            header.extend(aa_box([header_data[h]], chars, width))
            header.extend([''] * n)
    header.extend([''] * end)
    header.append(aa_line(chars['bar2'], width))
    if web:
        header = ['<section><pre>' + header[0]] + header[1:-1] + [header[-1] + '</pre></section>']
    return header


def aa_slide(title, char, width, web):
    res = [aa_line(char, width)]
    res.append('')
    res.append(aa_center(title, width)[:width])
    res.append('')
    res.append(aa_line(char, width))
    if web:
        res = ['<section><pre>' + res[0]] + res[1:]
    return res


# Raymond Hettinger's recipe
class SpreadSheet:
    _cells = {}
    def __setitem__(self, key, formula):
        self._cells[key] = formula
    def getformula(self, key):
        return self._cells[key]
    def __getitem__(self, key):
        if self._cells[key].strip()[0] == '=':
            try:
                return eval(self._cells[key].strip()[1:], globals(), self)
            except:
                return 'Error'
        else:
            return self._cells[key].strip()


def aa_table(table, chars, width, border, h_header, v_header, align, spread, web):
    if spread:
        s = SpreadSheet()
        for j, row in enumerate(table):
            for i, el in enumerate(row['cells']):
                ind = string.ascii_uppercase[i/26 - 1].replace('Z', '') + string.ascii_uppercase[i%26] + str(j+1)
                if el and el.strip():
                    s[ind] = el
        for j, row in enumerate(table):
            for i, el in enumerate(row['cells']):
                ind = string.ascii_uppercase[i/26 - 1].replace('Z', '') + string.ascii_uppercase[i%26] + str(j+1)
                if el and el.strip() and el.strip()[0] == '=':
                    if web:
                        row['cells'][i] = '<a title="' + el.strip() + '">' + str(s[ind]) + '</a>'
                    else:
                        row['cells'][i] = str(s[ind])
    data = [[row['cells'], row['cellspan']] for row in table]
    n = max([len(line[0]) for line in data])
    data2 = []
    for line in data:
        if not line[1]:
            data2.append([n * [''], n * [1]])
        else:
            data2.append([line[0] + (n - sum(line[1])) * [''], line[1] + (n - sum(line[1])) * [1]])
    data3 = []
    for line in data2:
        if  max(line[1]) == 1:
            data3.append(line[0])
        else:
            newline = []
            for i, el in enumerate(line[0]):
                if line[1][i] == 1:
                    newline.append(el)
                else:
                    newline.extend(line[1][i] * [''])
            data3.append(newline)
    tab = []
    for i in range(n):
        tab.append([line[i] for line in data3])
    if web:
        length = [max([aa_len_cjk(re.sub('<a.*">|</a>', '', el)) for el in line]) for line in tab]
    else:
        length = [max([aa_len_cjk(el) for el in line]) for line in tab]
    if spread:
        if n > 676:
            Error(_("ASCII Art Spreadsheet tables are limited to 676 columns, and your table has %i columns.") % n)        
        h = [(string.ascii_uppercase[i/26 - 1].replace('Z', '') + string.ascii_uppercase[i%26]).center(length[i]) for i in range(n)]
        data2 = [[h, [1] * n]] + data2
        data2 = [[[str(i)] + line[0], [1] + line[1]] for i, line in enumerate(data2)]
        data2[0][0][0] = ''
        length, n = [max([len(line[0][0]) for line in data2])] + length, n + 1
    bord, side, corner, vhead = chars['border'], chars['side'], chars['corner'], chars['vhead']
    if border:
        hhead = chars['hhead']
    else:
        hhead = chars['border']
    resh = res = corner
    for i in range(n):
        res = res + (length[i] + 2) * bord + corner
        resh = resh + (length[i] + 2) * hhead + corner
    ret = []
    for i, line in enumerate(data2):
        aff = side
        if i == 1 and h_header:
            ret.append(resh)
        else:
            if i == 0 or border:
                ret.append(res)
        for j, el in enumerate(line[0]):
            if web:
                aff = aff + " " + el + (sum(length[j:(j + line[1][j])]) + line[1][j] * 3 - aa_len_cjk(re.sub('<a.*">|</a>', '',el)) - 2) * " " + side
            else:
                aff = aff + " " + el + (sum(length[j:(j + line[1][j])]) + line[1][j] * 3 - aa_len_cjk(el) - 2) * " " + side
            if j == 0 and v_header:
                aff = aff[:-1] + vhead
        ret.append(aff)
    ret.append(res)
    if align == 'Left':
        ret = [' ' * 2  + line for line in ret]
    elif align == 'Center' and not (web and spread):
        ret = [aa_center(line, width) for line in ret]
    return ret


def aa_image(image):
    art_table = '#$!;:,. '
    art_image = []
    for line in image:
        art_line = ''
        for pixel in line:
            art_line = art_line + art_table[pixel/32]
        art_image.append(art_line)
    return art_image


def aa_webwrap(txt, width):
    txt = re.split('(<a href=.*?>)|(</a>)|(<img src=.*?>)', txt)
    line, length, ret = '', 0, []
    for el in txt:
        if el:
            if el[0] != '<':
                if len(el) > width:
                    line = line + el
                    multi = textwrap.wrap(line, width)
                    ret.extend(multi[:-1])
                    line = multi[-1]
                elif length + len(el) <= width:
                    length = length + len(el)
                    line = line + el
                else:
                    ret.append(line)
                    line, length = el, len(el)
            else:
                    line = line + el
    ret.append(line)
    return ret


def aa_len_cjk(txt):
    if isinstance(txt, str):
        return len(txt)
    l = 0
    for char in txt:
        if unicodedata.east_asian_width(str(char)) in ('F', 'W'):
            l = l + 2
        else:
            l = l + 1
    return l


def aa_center(txt, width):
    n_before = (width - aa_len_cjk(txt)) / 2
    n_after = width - aa_len_cjk(txt) - n_before
    return ' ' * n_before + txt + ' ' * n_after


##############################################################################

class error(Exception):
    pass


def echo(msg):   # for quick debug
    print('\033[32;1m%s\033[m' % msg)


def Quit(msg=''):
    if msg:
        print(msg)
    sys.exit(0)


def Error(msg):
    msg = _("%s: Error: ") % my_name + msg
    raise error(msg)


def getTraceback():
    try:
        from traceback import format_exception
        etype, value, tb = sys.exc_info()
        return ''.join(format_exception(etype, value, tb))
    except:
        pass


def getUnknownErrorMessage():
    msg = '%s\n%s (%s):\n\n%s' % (
        _('Sorry! Txt2tags aborted by an unknown error.'),
        _('Please send the following Error Traceback to the author'),
        my_email, getTraceback())
    return msg


def Message(msg, level):
    if level <= VERBOSE and not QUIET:
        prefix = '-' * 5
        print("%s %s" % (prefix * level, msg))


def Debug(msg, id_=0, linenr=None):
    "Show debug messages, categorized (colored or not)"
    if QUIET or not DEBUG:
        return
    if int(id_) not in list(range(8)):
        id_ = 0
    # 0:black 1:red 2:green 3:yellow 4:blue 5:pink 6:cyan 7:white ;1:light
    ids            = ['INI', 'CFG', 'SRC', 'BLK', 'HLD', 'GUI', 'OUT', 'DET']
    colors_bgdark  = ['7;1', '1;1', '3;1', '6;1', '4;1', '5;1', '2;1', '7;1']
    colors_bglight = ['0'  , '1'  , '3'  , '6'  , '4'  , '5'  , '2'  , '0'  ]
    if linenr is not None:
        msg = "LINE %04d: %s" % (linenr, msg)
    if COLOR_DEBUG:
        if BG_LIGHT:
            color = colors_bglight[id_]
        else:
            color = colors_bgdark[id_]
        msg = '\033[3%sm%s\033[m' % (color, msg)
    print("++ %s: %s" % (ids[id_], msg))


def Readfile(file_path, remove_linebreaks=0, ignore_error=0):
    data = []

    # STDIN
    if file_path == '-':
        try:
            data = sys.stdin.readlines()
        except:
            if not ignore_error:
                Error(_('You must feed me with data on STDIN!'))

    # URL
    elif PathMaster().is_url(file_path):
        try:
            from urllib.request import urlopen
            f = urlopen(file_path)
            if f.getcode() == 404:  # URL not found
                raise
            data = f.readlines()
            f.close()
        except:
            if not ignore_error:
                Error(_("Cannot read file:") + ' ' + file_path)

    # local file
    else:
        try:
            f = open(file_path)
            data = f.readlines()
            f.close()
        except:
            if not ignore_error:
                Error(_("Cannot read file:") + ' ' + file_path)

    if remove_linebreaks:
        data = [re.sub('[\n\r]+$', '', x) for x in data]

    Message(_("File read (%d lines): %s") % (len(data), file_path), 2)
    return data


def Savefile(file_path, contents):
    try:
        f = open(file_path, 'wb')
    except:
        Error(_("Cannot open file for writing:") + ' ' + file_path)
    if type(contents) == type([]):
        doit = f.writelines
    else:
        doit = f.write
    cont = []
    if CONF['target'] in ('aat', 'rst', 'txt'):
        for line in contents:
            if isinstance(line, str):
                cont.append(line.encode('utf-8'))
            else:
                cont.append(line)
    elif CONF['target'] == 'mgp':
        for line in contents:
            if isinstance(line, str):
                cont.append(line.encode('latin1', 'replace'))
            else:
                cont.append(line)
    else:
        cont = contents
    doit(cont)
    f.close()


def showdic(dic):
    for k in list(dic.keys()):
        print("%15s : %s" % (k, dic[k]))


def dotted_spaces(txt=''):
    return txt.replace(' ', '.')


# TIP: win env vars http://www.winnetmag.com/Article/ArticleID/23873/23873.html
def get_rc_path():
    "Return the full path for the users' RC file"
    # Try to get the path from an env var. if yes, we're done
    user_defined = os.environ.get('T2TCONFIG')
    if user_defined:
        return user_defined
    # Env var not found, so perform automatic path composing
    # Set default filename according system platform
    rc_names = {'default': '.txt2tagsrc', 'win': '_t2trc'}
    rc_file = rc_names.get(sys.platform[:3]) or rc_names['default']
    # The file must be on the user directory, but where is this dir?
    rc_dir_search = ['HOME', 'HOMEPATH']
    for var in rc_dir_search:
        rc_dir = os.environ.get(var)
        if rc_dir:
            break
    # rc dir found, now we must join dir+file to compose the full path
    if rc_dir:
        # Compose path and return it if the file exists
        rc_path = os.path.join(rc_dir, rc_file)
        # On windows, prefix with the drive (%homedrive%: 2k/XP/NT)
        if sys.platform.startswith('win'):
            rc_drive = os.environ.get('HOMEDRIVE')
            rc_path = os.path.join(rc_drive, rc_path)
        return rc_path
    # Sorry, not found
    return ''


##############################################################################

class PathMaster:
    """Handle paths. See issues: 27, 62, 63, 71, 85."""

    def __init__(self):
        pass

    def is_url(self, text):
        return text.startswith('http://') or text.startswith('https://')

    def join(self, dirname, filename):
        """Join paths, unless filename is STDOUT, absolute or URL."""

        if not dirname \
            or not filename \
            or filename in (STDOUT, MODULEOUT) \
            or os.path.isabs(filename) \
            or self.is_url(filename):
            return filename
        else:
            return os.path.join(dirname, filename)

    def relpath(self, path, start):
        """Unlike os.path.relpath(), never touch URLs"""
        if not path or self.is_url(path):
            return path
        else:
            return os.path.relpath(path, start)


class CommandLine:
    """
    Command Line class - Masters command line

    This class checks and extract data from the provided command line.
    The --long options and flags are taken from the global OPTIONS,
    FLAGS and ACTIONS dictionaries. The short options are registered
    here, and also their equivalence to the long ones.

    _compose_short_opts() -> str
    _compose_long_opts() -> list
        Compose the valid short and long options list, on the
        'getopt' format.

    parse() -> (opts, args)
        Call getopt to check and parse the command line.
        It expects to receive the command line as a list, and
        without the program name (sys.argv[1:]).

    get_raw_config() -> [RAW config]
        Scans command line and convert the data to the RAW config
        format. See ConfigMaster class to the RAW format description.
        Optional 'ignore' and 'filter_' arguments are used to filter
        in or out specified keys.

    compose_cmdline(dict) -> [Command line]
        Compose a command line list from an already parsed config
        dictionary, generated from RAW by ConfigMaster(). Use
        this to compose an optimal command line for a group of
        options.

    The get_raw_config() calls parse(), so the typical use of this
    class is:

        raw = CommandLine().get_raw_config(sys.argv[1:])
    """
    def __init__(self):
        self.all_options = list(OPTIONS.keys())
        self.all_flags   = list(FLAGS.keys())
        self.all_actions = list(ACTIONS.keys())

        # short:long options equivalence
        self.short_long = {
            'C': 'config-file',
            'h': 'help',
            'H': 'no-headers',
            'i': 'infile',
            'n': 'enum-title',
            'o': 'outfile',
            'q': 'quiet',
            't': 'target',
            'T': 'template',
            'v': 'verbose',
            'V': 'version',
        }

        # Compose valid short and long options data for getopt
        self.short_opts = self._compose_short_opts()
        self.long_opts  = self._compose_long_opts()

    def _compose_short_opts(self):
        "Returns a string like 'hVt:o' with all short options/flags"
        ret = []
        for opt in list(self.short_long.keys()):
            long_ = self.short_long[opt]
            if long_ in self.all_options:   # is flag or option?
                opt = opt + ':'             # option: have param
            ret.append(opt)
        #Debug('Valid SHORT options: %s' % ret)
        return ''.join(ret)

    def _compose_long_opts(self):
        "Returns a list with all the valid long options/flags"
        ret = [x + '=' for x in self.all_options]        # add =
        ret.extend(self.all_flags)                            # flag ON
        ret.extend(self.all_actions)                          # actions
        ret.extend(['no-' + x for x in self.all_flags])  # add no-*
        ret.extend(['no-style', 'no-encoding'])               # turn OFF
        ret.extend(['no-outfile', 'no-infile'])               # turn OFF
        ret.extend(['no-dump-config', 'no-dump-source'])      # turn OFF
        ret.extend(['no-targets'])                            # turn OFF
        #Debug('Valid LONG options: %s' % ret)
        return ret

    def _tokenize(self, cmd_string=''):
        "Convert a command line string to a list"
        #TODO protect quotes contents -- Don't use it, pass cmdline as list
        return cmd_string.split()

    def parse(self, cmdline=[]):
        "Check/Parse a command line list     TIP: no program name!"
        # Get the valid options
        short, long_ = self.short_opts, self.long_opts
        # Parse it!
        try:
            opts, args = getopt.getopt(cmdline, short, long_)
        except getopt.error as errmsg:
            Error(_("%s (try --help)") % errmsg)
        return (opts, args)

    def get_raw_config(self, cmdline=[], ignore=[], filter_=[], relative=0):
        "Returns the options/arguments found as RAW config"

        if not cmdline:
            return []
        ret = []

        # We need lists, not strings (such as from %!options)
        if type(cmdline) in (type(''), type('')):
            cmdline = self._tokenize(cmdline)

        # Extract name/value pair of all configs, check for invalid names
        options, arguments = self.parse(cmdline[:])

        # Needed when expanding %!options inside remote %!includeconf
        dirname = ''

        # Some cleanup on the raw config
        for name, value in options:

            # Remove leading - and --
            name = re.sub('^--?', '', name)

            # Fix old misspelled --suGGar, --no-suGGar
            name = name.replace('suggar', 'sugar')

            # Translate short option to long
            if len(name) == 1:
                name = self.short_long[name]

            if name == 'dirname':
                dirname = value
                continue

            # Outfile exception: path relative to PWD
            if name == 'outfile' and value not in [STDOUT, MODULEOUT]:
                if relative:
                    value = os.path.abspath(value)
                else:
                    value = PathMaster().join(dirname, value)

            # -C, --config-file inclusion, path relative to PWD
            if name == 'config-file':
                value = PathMaster().join(dirname, value)
                ret.extend(ConfigLines().include_config_file(value))
                continue

            # --style: path relative to PWD
            # Already OK, when comming from the command line
            # Needs fix when coming from %!options: --style foo.css
            if name == 'style':
                ret.append(['all', 'stylepath', PathMaster().join(dirname, value)])

            # Save this config
            ret.append(['all', name, value])

        # All configuration was read and saved

        # Get infile, if any
        while arguments:
            infile = arguments.pop(0)
            ret.append(['all', 'infile', infile])

        # Apply 'ignore' and 'filter_' rules (filter_ is stronger)
        if (ignore or filter_):
            filtered = []
            for target, name, value in ret:
                if (filter_ and name in filter_) or \
                   (ignore and name not in ignore):
                    filtered.append([target, name, value])
                else:
                    fancykey = dotted_spaces("%12s" % name)
                    Message(_("Ignored config") + (" %s : %s" % (fancykey, value)), 3)
            ret = filtered[:]

        # Add the original command line string as 'realcmdline'
        ret.append(['all', 'realcmdline', cmdline])

        return ret

    def compose_cmdline(self, conf={}, no_check=0):
        "compose a full (and diet) command line from CONF dict"
        if not conf:
            return []
        args = []
        dft_options = OPTIONS.copy()
        cfg = conf.copy()
        valid_opts = self.all_options + self.all_flags
        use_short = {'no-headers': 'H', 'enum-title': 'n'}
        # Remove useless options
        if not no_check and cfg.get('toc-only'):
            if 'no-headers' in cfg:
                del cfg['no-headers']
            if 'outfile' in cfg:
                del cfg['outfile']      # defaults to STDOUT
            if cfg.get('target') == 'txt':
                del cfg['target']       # already default
            args.append('--toc-only')  # must be the first
            del cfg['toc-only']
        # Add target type
        if 'target' in cfg:
            args.append('-t ' + cfg['target'])
            del cfg['target']
        # Add other options
        for key in list(cfg.keys()):
            if key not in valid_opts:
                continue  # may be a %!setting
            if key == 'outfile' or key == 'infile':
                continue  # later
            val = cfg[key]
            if not val:
                continue
            # Default values are useless on cmdline
            if val == dft_options.get(key):
                continue
            # -short format
            if key in use_short:
                args.append('-' + use_short[key])
                continue
            # --long format
            if key in self.all_flags:   # add --option
                args.append('--' + key)
            else:                       # add --option=value
                args.append('--%s=%s' % (key, val))
        # The outfile using -o
        if 'outfile' in cfg and \
           cfg['outfile'] != dft_options.get('outfile'):
            args.append('-o ' + cfg['outfile'])
        # Place input file(s) always at the end
        if 'infile' in cfg:
            args.append(' '.join(cfg['infile']))
        # Return as a nice list
        Debug("Diet command line: %s" % ' '.join(args), 1)
        return args


##############################################################################

class SourceDocument:
    """
    SourceDocument class - scan document structure, extract data

    It knows about full files. It reads a file and identify all
    the areas beginning (Head,Conf,Body). With this info it can
    extract each area contents.
    Note: the original line break is removed.

    DATA:
      self.arearef - Save Head, Conf, Body init line number
      self.areas   - Store the area names which are not empty
      self.buffer  - The full file contents (with NO \\r, \\n)

    METHODS:
      get()   - Access the contents of an Area. Example:
                config = SourceDocument(file).get('conf')

      split() - Get all the document Areas at once. Example:
                head, conf, body = SourceDocument(file).split()

    RULES:
        * The document parts are sequential: Head, Conf and Body.
        * One ends when the next begins.
        * The Conf Area is optional, so a document can have just
          Head and Body Areas.

        These are the Areas limits:
          - Head Area: the first three lines
          - Body Area: from the first valid text line to the end
          - Conf Area: the comments between Head and Body Areas

        Exception: If the first line is blank, this means no
        header info, so the Head Area is just the first line.
    """
    def __init__(self, filename='', contents=[]):
        self.areas = ['head', 'conf', 'body']
        self.arearef = []
        self.areas_fancy = ''
        self.filename = filename
        self.buffer = []
        if filename:
            self.scan_file(filename)
        elif contents:
            self.scan(contents)

    def split(self):
        "Returns all document parts, splitted into lists."
        return self.get('head'), self.get('conf'), self.get('body')

    def get(self, areaname):
        "Returns head|conf|body contents from self.buffer"
        # Sanity
        if areaname not in self.areas:
            return []
        if not self.buffer:
            return []
        # Go get it
        bufini = 1
        bufend = len(self.buffer)
        if   areaname == 'head':
            ini = bufini
            end = self.arearef[1] or self.arearef[2] or bufend
        elif areaname == 'conf':
            ini = self.arearef[1]
            end = self.arearef[2] or bufend
        elif areaname == 'body':
            ini = self.arearef[2]
            end = bufend
        else:
            Error("Unknown Area name '%s'" % areaname)
        lines = self.buffer[ini:end]
        # Make sure head will always have 3 lines
        while areaname == 'head' and len(lines) < 3:
            lines.append('')
        return lines

    def scan_file(self, filename):
        Debug("source file: %s" % filename)
        Message(_("Loading source document"), 1)
        buf = Readfile(filename, remove_linebreaks=1)
        self.scan(buf)

    def scan(self, lines):
        "Run through source file and identify head/conf/body areas"
        buf = lines
        if len(buf) == 0:
            Error(_('The input file is empty: %s') % self.filename)
        cfg_parser = ConfigLines().parse_line
        buf.insert(0, '')                         # text start at pos 1
        ref = [1, 4, 0]
        if not buf[1].strip():                    # no header
            ref[0] = 0
            ref[1] = 2
        rgx = getRegexes()
        on_comment_block = 0
        for i in range(ref[1], len(buf)):         # find body init:
            # Handle comment blocks inside config area
            if not on_comment_block \
               and rgx['blockCommentOpen'].search(buf[i]):
                on_comment_block = 1
                continue
            if on_comment_block \
               and rgx['blockCommentOpen'].search(buf[i]):
                on_comment_block = 0
                continue
            if on_comment_block:
                continue

            if buf[i].strip() and (            # ... not blank and
               buf[i][0] != '%' or             # ... not comment or
               rgx['macros'].match(buf[i]) or  # ... %%macro
               rgx['toc'].match(buf[i])    or  # ... %%toc
               cfg_parser(buf[i], 'include')[1] or  # ... %!include
               cfg_parser(buf[i], 'csv')[1] or      # ... %!csv
               cfg_parser(buf[i], 'csvheader')[1]   # ... %!csvheader
            ):
                ref[2] = i
                break
        if ref[1] == ref[2]:
            ref[1] = 0                          # no conf area
        for i in 0, 1, 2:                       # del !existent
            if ref[i] >= len(buf):
                ref[i] = 0                      # title-only
            if not ref[i]:
                self.areas[i] = ''
        Debug('Head,Conf,Body start line: %s' % ref)
        self.arearef = ref                      # save results
        self.buffer  = buf
        # Fancyness sample: head conf body (1 4 8)
        self.areas_fancy = "%s (%s)" % (
            ' '.join(self.areas),
            ' '.join(map(str, [x or '' for x in ref])))
        Message(_("Areas found: %s") % self.areas_fancy, 2)

    def get_raw_config(self):
        "Handy method to get the CONF area RAW config (if any)"
        if not self.areas.count('conf'):
            return []
        Message(_("Scanning source document CONF area"), 1)
        raw = ConfigLines(
            file_=self.filename, lines=self.get('conf'),
            first_line=self.arearef[1]).get_raw_config()
        Debug("document raw config: %s" % raw, 1)
        return raw


##############################################################################

class ConfigMaster:
    """
    ConfigMaster class - the configuration wizard

    This class is the configuration master. It knows how to handle
    the RAW and PARSED config format. It also performs the sanity
    checking for a given configuration.

    DATA:
      self.raw         - Stores the config on the RAW format
      self.parsed      - Stores the config on the PARSED format
      self.defaults    - Stores the default values for all keys
      self.off         - Stores the OFF values for all keys
      self.multi       - List of keys which can have multiple values
      self.numeric     - List of keys which value must be a number
      self.incremental - List of keys which are incremental

    RAW FORMAT:
      The RAW format is a list of lists, being each mother list item
      a full configuration entry. Any entry is a 3 item list, on
      the following format: [ TARGET, KEY, VALUE ]
      Being a list, the order is preserved, so it's easy to use
      different kinds of configs, as CONF area and command line,
      respecting the precedence.
      The special target 'all' is used when no specific target was
      defined on the original config.

    PARSED FORMAT:
      The PARSED format is a dictionary, with all the 'key : value'
      found by reading the RAW config. The self.target contents
      matters, so this dictionary only contains the target's
      config. The configs of other targets are ignored.

    The CommandLine and ConfigLines classes have the get_raw_config()
    method which convert the configuration found to the RAW format.
    Just feed it to parse() and get a brand-new ready-to-use config
    dictionary. Example:

        >>> raw = CommandLine().get_raw_config(['-n', '-H'])
        >>> print raw
        [['all', 'enum-title', ''], ['all', 'no-headers', '']]
        >>> parsed = ConfigMaster(raw).parse()
        >>> print parsed
        {'enum-title': 1, 'headers': 0}
    """
    def __init__(self, raw=[], target=''):
        self.raw          = raw
        self.target       = target
        self.parsed       = {}
        self.dft_options  = OPTIONS.copy()
        self.dft_flags    = FLAGS.copy()
        self.dft_actions  = ACTIONS.copy()
        self.dft_settings = SETTINGS.copy()
        self.defaults     = self._get_defaults()
        self.off          = self._get_off()
        self.incremental  = ['verbose']
        self.numeric      = ['toc-level', 'split', 'width', 'height']
        self.multi        = ['infile', 'preproc', 'postproc', 'postvoodoo', 'options', 'style', 'stylepath']

    def _get_defaults(self):
        "Get the default values for all config/options/flags"
        empty = {}
        for kw in CONFIG_KEYWORDS:
            empty[kw] = ''
        empty.update(self.dft_options)
        empty.update(self.dft_flags)
        empty.update(self.dft_actions)
        empty.update(self.dft_settings)
        empty['realcmdline'] = ''  # internal use only
        empty['sourcefile']  = ''  # internal use only
        empty['currentsourcefile']  = ''  # internal use only
        return empty

    def _get_off(self):
        "Turns OFF all the config/options/flags"
        off = {}
        for key in list(self.defaults.keys()):
            kind = type(self.defaults[key])
            if kind == type(9):
                off[key] = 0
            elif kind == type('') or kind == type(''):
                off[key] = ''
            elif kind == type([]):
                off[key] = []
            else:
                Error('ConfigMaster: %s: Unknown type' % key)
        return off

    def _check_target(self):
        "Checks if the target is already defined. If not, do it"
        if not self.target:
            self.target = self.find_value('target')

    def get_target_raw(self):
        "Returns the raw config for self.target or 'all'"
        ret = []
        self._check_target()
        for entry in self.raw:
            if entry[0] == self.target or entry[0] == 'all':
                ret.append(entry)
        return ret

    def add(self, key, val):
        "Adds the key:value pair to the config dictionary (if needed)"
        # %!options
        if key == 'options':
            # Actions are not valid inside %!options
            ignoreme = list(self.dft_actions.keys())
            # --target inside %!options is not allowed (use %!target)
            ignoreme.append('target')
            # But there are some exceptions that are allowed (XXX why?)
            ignoreme.remove('dump-config')
            ignoreme.remove('dump-source')
            ignoreme.remove('targets')
            raw_opts = CommandLine().get_raw_config(
                val, ignore=ignoreme)
            for target, key, val in raw_opts:
                self.add(key, val)
            return
        # The no- prefix turns OFF this key
        if key.startswith('no-'):
            key = key[3:]              # remove prefix
            val = self.off.get(key)    # turn key OFF
        # Is this key valid?
        if key not in self.defaults:
            Debug('Bogus Config %s:%s' % (key, val), 1)
            return
        # Is this value the default one?
        if val == self.defaults.get(key):
            # If default value, remove previous key:val
            if key in self.parsed:
                del self.parsed[key]
            # Nothing more to do
            return
        # Flags ON comes empty. we'll add the 1 value now
        if val == '' and (
           key in self.dft_flags or
           key in self.dft_actions):
            val = 1
        # Multi value or single?
        if key in self.multi:
            # First one? start new list
            if key not in self.parsed:
                self.parsed[key] = []
            self.parsed[key].append(val)
        # Incremental value? so let's add it
        elif key in self.incremental:
            self.parsed[key] = (self.parsed.get(key) or 0) + val
        else:
            self.parsed[key] = val
        fancykey = dotted_spaces("%12s" % key)
        Message(_("Added config") + (" %s : %s" % (fancykey, val)), 3)

    def get_outfile_name(self, config={}):
        "Dirname is the same for {in,out}file"

        infile, outfile = config['sourcefile'], config['outfile']

        # Set output to STDOUT/MODULEOUT when no real inputfile
        if infile == STDIN and not outfile:
            outfile = STDOUT
        if infile == MODULEIN and not outfile:
            outfile = MODULEOUT

        # Automatic outfile name: infile.target
        if not outfile and (infile and config.get('target')):
            # .t2t and .txt are the only "official" source extensions
            basename = re.sub('\.t[2x]t$', '', infile)
            outfile = "%s.%s" % (basename, config['target'])
            if config['target'] == 'aat' and config['slides']:
                outfile = "%s.%s" % (basename, 'aap')
            if config['target'] == 'aat' and config['spread']:
                outfile = "%s.%s" % (basename, 'aas')
            if config['target'] == 'aat' and config['web']:
                outfile = "%s.%s" % (basename, 'aatw')
            if config['target'] == 'aat' and config['slides'] and config['web']:
                outfile = "%s.%s" % (basename, 'aapw')
            if config['target'] == 'aat' and config['spread'] and config['web']:
                outfile = "%s.%s" % (basename, 'aasw')

        Debug(" infile: '%s'" % infile , 1)
        Debug("outfile: '%s'" % outfile, 1)
        return outfile

    def sanity(self, config, gui=0):
        "Basic config sanity checking"
        global AA
        global RST
        if not config:
            return {}
        target = config.get('target')
        # Some actions don't require target specification
        if not target:
            for action in NO_TARGET:
                if config.get(action):
                    target = 'txt'
                    break
        # On GUI, some checking are skipped
        if not gui:
            # We *need* a target
            if not target:
                Error(_('No target specified (try --help)') + '\n\n' +
                _('Please inform a target using the -t option or the %!target command.') + '\n' +
                _('Example:') + ' %s -t html %s' % (my_name, _('file.t2t')) + '\n\n' +
                _("Run 'txt2tags --targets' to see all the available targets."))
            # And of course, an infile also
            # TODO#1: It seems that this checking is never reached
            if not config.get('infile'):
                Error(_('Missing input file (try --help)'))
            # Is the target valid?
            if not TARGETS.count(target):
                Error(_("Invalid target '%s'") % target + '\n\n' +
                _("Run 'txt2tags --targets' to see all the available targets."))
        # Ensure all keys are present
        empty = self.defaults.copy()
        empty.update(config)
        config = empty.copy()
        # Check integers options
        for key in list(config.keys()):
            if key in self.numeric:
                try:
                    config[key] = int(config[key])
                except ValueError:
                    Error(_('--%s value must be a number') % key)
        # Check split level value
        if config['split'] not in (0, 1, 2):
            Error(_('Option --split must be 0, 1 or 2'))
        if target in ['csv', 'ods']:
            config['spread'] = True
        if target == 'aap':
            target, config['slides'] = 'aat', True
        if target == 'aas':
            target, config['spread'] = 'aat', True
            exec('from math import *', globals())
        if target == 'aatw':
            target, config['web'] = 'aat', True
        if target == 'aapw':
            target, config['slides'], config['web'] = 'aat', True, True
        if target == 'aasw':
            target, config['spread'], config['web'] = 'aat', True, True
            exec('from math import *', globals())
        # Slides needs width and height
        if config['slides'] and target == 'aat':
            if config['web']:
                config['height'], config['width'] = 28, 80
            if not config['width'] and  not config['height'] and os.name == 'posix':
                import fcntl, termios
                data = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, 4*'00') 
                config['height'], config['width'] = struct.unpack('4H',data)[:2]
            if not config['width']:
                config['width'] = DFT_SLIDE_WIDTH
            if not config['height']:
                config['height'] = DFT_SLIDE_HEIGHT
        # ASCII Art needs a width
        if target == 'aat' and not config['width']:
            config['width'] = DFT_TEXT_WIDTH
        if target == 'aat' and config['width'] < 5:
            Error(_("--width: Expected width > 4, got %i") % config['width'])
        # Check/set user ASCII Art formatting characters
        if config['chars']:
            try:
                # Peace for ASCII 7-bits only
                config['chars'] = config['chars'].encode()
            except:
                if config['encoding'].lower() == 'utf-8' and locale.getpreferredencoding() != 'UTF-8':
                    Error(_("--chars: Expected chars from an UTF-8 terminal for your UTF-8 file"))
                if config['encoding'].lower() != 'utf-8' and locale.getpreferredencoding() == 'UTF-8':
                    if not config['encoding']:
                        Error(_("--chars: Expected an UTF-8 file for your chars from an UTF-8 terminal, you could set %!encoding: UTF-8"))
                    else:
                        Error(_("--chars: Expected an UTF-8 file for your chars from an UTF-8 terminal"))
            if target == 'aat':
                if len(config['chars']) != len(AA_VALUES):
                    Error(_("--chars: Expected %i chars, got %i") % (
                        len(AA_VALUES), len(config['chars'])))
                if isinstance(config['chars'], str): 
                    for char in config['chars']:
                        if unicodedata.east_asian_width(char) in ('F', 'W'):
                            Error(_("--chars: Expected no CJK double width chars, but got %s") % char.encode('utf-8'))
                AA = dict(list(zip(AA_KEYS, config['chars'])))
            elif target == 'rst':
                if len(config['chars']) != len(RST_VALUES):
                    Error(_("--chars: Expected %i chars, got %i") % (
                        len(RST_VALUES), len(config['chars'])))
                else:
                    # http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#sections
                    chars_section = '!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~'
                    for char in config['chars'][:7]:
                        if char not in chars_section:
                            if locale.getpreferredencoding() == 'UTF-8':
                                char = char.encode('utf-8')
                            Error(_("--chars: Expected chars in : %s but got %s") % (chars_section, char))
                    # http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#bullet-lists
                    chars_bullet, char_8  = '*+-', config['chars'][7]
                    if char_8 not in chars_bullet:
                        if locale.getpreferredencoding() == 'UTF-8':
                            char_8 = char_8.encode('utf-8') 
                        Error(_("--chars: Expected chars in : %s but got %s") % (chars_bullet, char_8))
                    RST = dict(list(zip(RST_KEYS, config['chars'])))

        # --toc-only is stronger than others
        if config['toc-only']:
            config['headers'] = 0
            config['toc']     = 0
            config['split']   = 0
            config['gui']     = 0
            config['outfile'] = config['outfile'] or STDOUT
        # Splitting is disable for now (future: HTML only, no STDOUT)
        config['split'] = 0
        # Restore target
        config['target'] = target
        # Set output file name
        config['outfile'] = self.get_outfile_name(config)
        # Checking suicide
        if os.path.abspath(config['sourcefile']) == os.path.abspath(config['outfile']) and \
           config['outfile'] not in [STDOUT, MODULEOUT] and not gui:
            Error(_("Input and Output files are the same: %s") % config['outfile'])
        return config

    def parse(self):
        "Returns the parsed config for the current target"
        raw = self.get_target_raw()
        for target, key, value in raw:
            if key == 'chars' and locale.getpreferredencoding() == 'UTF-8':
                self.add(key, value.decode('utf-8'))
            else:
                self.add(key, value)
        Message(_("Added the following keys: %s") % ', '.join(list(self.parsed.keys())), 2)
        return self.parsed.copy()

    def find_value(self, key='', target=''):
        "Scans ALL raw config to find the desired key"
        ret = []
        # Scan and save all values found
        for targ, k, val in self.raw:
            if k == key and (targ == target or targ == 'all'):
                ret.append(val)
        if not ret:
            return ''
        # If not multi value, return only the last found
        if key in self.multi:
            return ret
        else:
            return ret[-1]


########################################################################

class ConfigLines:
    """
    ConfigLines class - the config file data extractor

    This class reads and parse the config lines on the %!key:val
    format, converting it to RAW config. It deals with user
    config file (RC file), source document CONF area and
    %!includeconf directives.

    Call it passing a file name or feed the desired config lines.
    Then just call the get_raw_config() method and wait to
    receive the full config data on the RAW format. This method
    also follows the possible %!includeconf directives found on
    the config lines. Example:

        raw = ConfigLines(file=".txt2tagsrc").get_raw_config()

    The parse_line() method is also useful to be used alone,
    to identify and tokenize a single config line. For example,
    to get the %!include command components, on the source
    document BODY:

        target, key, value = ConfigLines().parse_line(body_line)
    """
    # parse_line regexes, moved here to avoid recompilation
    _parse_cfg = re.compile("""
        ^%!\s*                # leading id with opt spaces
        (?P<name>\w+)\s*       # config name
        (\((?P<target>\w*)\))? # optional target spec inside ()
        \s*:\s*               # key:value delimiter with opt spaces
        (?P<value>\S.+?)      # config value
        \s*$                  # rstrip() spaces and hit EOL
        """, re.I + re.VERBOSE)
    _parse_prepost = re.compile("""
                                      # ---[ PATTERN ]---
        ^( "([^"]*)"          # "double quoted" or
        | '([^']*)'           # 'single quoted' or
        | ([^\s]+)            # single_word
        )
        \s+                   # separated by spaces
                                  # ---[ REPLACE ]---
        ( "([^"]*)"           # "double quoted" or
        | '([^']*)'           # 'single quoted' or
        | (.*)                # anything
        )
        \s*$
        """, re.VERBOSE)
    _parse_guicolors = re.compile("^([^\s]+\s+){3}[^\s]+")  # 4 tokens

    def __init__(self, file_='', lines=[], first_line=1):
        self.file = file_ or 'NOFILE'
        self.lines = lines
        self.first_line = first_line
        if file_:
            self.folder = os.path.dirname(self.file)
        else:
            self.folder = ''

    def load_lines(self):
        "Make sure we've loaded the file contents into buffer"
        if not self.lines and not self.file:
            Error("ConfigLines: No file or lines provided")
        if not self.lines:
            self.lines = self.read_config_file(self.file)

    def read_config_file(self, filename=''):
        "Read a Config File contents, aborting on invalid line"
        if not filename:
            return []
        errormsg = _("Invalid CONFIG line on %s") + "\n%03d:%s"
        lines = Readfile(filename, remove_linebreaks=1)
        # Sanity: try to find invalid config lines
        for i in range(len(lines)):
            line = lines[i].rstrip()
            if not line:  # empty
                continue
            if line[0] != '%':
                Error(errormsg % (filename, i + 1, line))
        return lines

    def include_config_file(self, file_=''):
        "Perform the %!includeconf action, returning RAW config"
        if not file_:
            return []

        # Fix config file path
        file_ = self.fix_config_relative_path(file_)

        # Read and parse included config file contents
        return ConfigLines(file_=file_).get_raw_config()

    def fix_config_relative_path(self, path_):
        """
        The path for external files must be relative to the config file path.
        External files appear in: %!includeconf, %!style, %!template.
        See issue 71.
        """
        return PathMaster().join(self.folder, path_)

    def get_raw_config(self):
        "Scan buffer and extract all config as RAW (including includes)"
        ret = []
        self.load_lines()
        first = self.first_line

        def add(target, key, val):
            "Save the RAW config"
            ret.append([target, key, val])
            Message(_("Added %s") % key, 3)

        for i in range(len(self.lines)):
            line = self.lines[i]
            Message(_("Processing line %03d: %s") % (first + i, line), 2)
            target, key, val = self.parse_line(line)

            if not key:  # no config on this line
                continue

            # %!style
            # We need to fix the CSS files path. See issue 71.
            #
            # This stylepath config holds the fixed path for each CSS file.
            # This path is used when composing headers, inside doHeader().
            #
            if key == 'style':
                stylepath = self.fix_config_relative_path(val)
                add(target, 'stylepath', stylepath)
                # Note: the normal 'style' config will be added later

            # %!options
            if key == 'options':
                # Prepend --dirname option to track config file original folder
                if self.folder:
                    val = '--dirname %s %s' % (self.folder, val)

            # %!includeconf
            if key == 'includeconf':

                # Sanity
                err = _('A file cannot include itself (loop!)')
                if val == self.file:
                    Error("%s: %%!includeconf: %s" % (err, self.file))

                more_raw = self.include_config_file(val)
                ret.extend(more_raw)

                Message(_("Finished Config file inclusion: %s") % val, 2)

            # Normal config, except %!includeconf
            else:
                add(target, key, val)
        return ret

    def parse_line(self, line='', keyname='', target=''):
        "Detects %!key:val config lines and extract data from it"
        empty = ['', '', '']
        if not line:
            return empty
        no_target = ['target', 'includeconf']
        re_name   = keyname or '[a-z]+'
        re_target = target  or '[a-z]*'
        # XXX TODO <value>\S.+?  requires TWO chars, breaks %!include:a
        cfgregex  = ConfigLines._parse_cfg
        prepostregex = ConfigLines._parse_prepost
        guicolors = ConfigLines._parse_guicolors

        # Give me a match or get out
        match = cfgregex.match(line)
        if not match:
            return empty

        if keyname and keyname != match.group('name'):
            return empty
        if target and match.group('target') not in (None, '', target):
            return empty

        # Save information about this config
        name   = (match.group('name') or '').lower()
        target = (match.group('target') or 'all').lower()
        value  = match.group('value')

        # %!keyword(target) not allowed for these
        if name in no_target and match.group('target'):
            Error(
                _("You can't use (target) with %s") % ('%!' + name)
                + "\n%s" % line)

        # Force no_target keywords to be valid for all targets
        if name in no_target:
            target = 'all'

        # Special config for GUI colors
        if name == 'guicolors':
            valmatch = guicolors.search(value)
            if not valmatch:
                return empty
            value = re.split('\s+', value)

        # Special config with two quoted values (%!preproc: "foo" 'bar')
        if name in ['preproc', 'postproc', 'postvoodoo']:
            valmatch = prepostregex.search(value)
            if not valmatch:
                return empty
            getval = valmatch.group
            patt   = getval(2) or getval(3) or getval(4) or ''
            repl   = getval(6) or getval(7) or getval(8) or ''
            value  = (patt, repl)
        return [target, name, value]


##############################################################################

class MaskMaster:
    "(Un)Protect important structures from escaping and formatting"
    def __init__(self):
        self.linkmask   = 'vvvLINKvvv'
        self.monomask   = 'vvvMONOvvv'
        self.macromask  = 'vvvMACROvvv'
        self.rawmask    = 'vvvRAWvvv'
        self.taggedmask = 'vvvTAGGEDvvv'
        self.tocmask    = 'vvvTOCvvv'
        self.macroman   = MacroMaster()
        self.reset()

    def reset(self):
        self.linkbank = []
        self.monobank = []
        self.macrobank = []
        self.rawbank = []
        self.taggedbank = []

    def mask(self, line=''):
        global AUTOTOC

        # The verbatim, raw and tagged inline marks are mutually exclusive.
        # This means that one can't appear inside the other.
        # If found, the inner marks must be ignored.
        # Example: ``foo ""bar"" ''baz''``
        # In HTML: <code>foo ""bar"" ''baz''</code>
        #
        # The trick here is to protect the mark who appears first on the line.
        # The three regexes are tried and the one with the lowest index wins.
        # If none is found (else), we get out of the loop.
        #
        while True:

            # Try to match the line for the three marks
            # Note: 'z' > 999999
            #
            t = r = v = 'z'
            try:
                t = regex['tagged'].search(line).start()
            except:
                pass
            try:
                r = regex['raw'].search(line).start()
            except:
                pass
            try:
                v = regex['fontMono'].search(line).start()
            except:
                pass

            # Protect tagged text
            if t >= 0 and t < r and t < v:
                txt = regex['tagged'].search(line).group(1)
                self.taggedbank.append(txt)
                line = regex['tagged'].sub(self.taggedmask, line, 1)

            # Protect raw text
            elif r >= 0 and r < t and r < v:
                txt = regex['raw'].search(line).group(1)
                txt = doEscape(TARGET, txt)
                self.rawbank.append(txt)
                line = regex['raw'].sub(self.rawmask, line, 1)

            # Protect verbatim text
            elif v >= 0 and v < t and v < r:
                txt = regex['fontMono'].search(line).group(1)
                txt = doEscape(TARGET, txt)
                self.monobank.append(txt)
                line = regex['fontMono'].sub(self.monomask, line, 1)
            else:
                break

        # Protect macros
        while regex['macros'].search(line):
            txt = regex['macros'].search(line).group()
            self.macrobank.append(txt)
            line = regex['macros'].sub(self.macromask, line, 1)

        # Protect TOC location
        while regex['toc'].search(line):
            line = regex['toc'].sub(self.tocmask, line)
            AUTOTOC = 0

        # Protect URLs and emails
        while regex['linkmark'].search(line) or \
              regex['link'].search(line):

            # Try to match plain or named links
            match_link  = regex['link'].search(line)
            match_named = regex['linkmark'].search(line)

            # Define the current match
            if match_link and match_named:
                # Both types found, which is the first?
                m = match_link
                if match_named.start() < match_link.start():
                    m = match_named
            else:
                # Just one type found, we're fine
                m = match_link or match_named

            # Extract link data and apply mask
            if m == match_link:              # plain link
                link = m.group()
                label = ''
                link_re = regex['link']
            else:                            # named link
                link = fix_relative_path(m.group('link'))
                label = m.group('label').rstrip()
                link_re = regex['linkmark']
            line = link_re.sub(self.linkmask, line, 1)

            # Save link data to the link bank
            self.linkbank.append((label, link))
        return line

    def undo(self, line):

        # url & email
        for label, url in self.linkbank:
            link = get_tagged_link(label, url)
            line = line.replace(self.linkmask, link, 1)

        # Expand macros
        for macro in self.macrobank:
            macro = self.macroman.expand(macro)
            line = line.replace(self.macromask, macro, 1)

        # Expand verb
        for mono in self.monobank:
            open_, close = TAGS['fontMonoOpen'], TAGS['fontMonoClose']
            line = line.replace(self.monomask, open_ + mono + close, 1)

        # Expand raw
        for raw in self.rawbank:
            line = line.replace(self.rawmask, raw, 1)

        # Expand tagged
        for tagged in self.taggedbank:
            line = line.replace(self.taggedmask, tagged, 1)

        return line


##############################################################################


class TitleMaster:
    "Title things"
    def __init__(self):
        self.count = ['', 0, 0, 0, 0, 0]
        self.toc   = []
        self.level = 0
        self.kind  = ''
        self.txt   = ''
        self.label = ''
        self.tag   = ''
        self.tag_hold = []
        self.last_level = 0
        self.count_id = ''
        self.user_labels = {}
        self.anchor_count = 0
        self.anchor_prefix = 'toc'

    def _open_close_blocks(self):
        "Open new title blocks, closing the previous (if any)"
        if not rules['titleblocks']:
            return
        tag = ''
        last = self.last_level
        curr = self.level

        # Same level, just close the previous
        if curr == last:
            tag = TAGS.get('title%dClose' % last)
            if tag:
                self.tag_hold.append(tag)

        # Section -> subsection, more depth
        while curr > last:
            last += 1

            # Open the new block of subsections
            tag = TAGS.get('blockTitle%dOpen' % last)
            if tag:
                self.tag_hold.append(tag)

            # Jump from title1 to title3 or more
            # Fill the gap with an empty section
            if curr - last > 0:
                tag = TAGS.get('title%dOpen' % last)
                tag = regex['x'].sub('', tag)      # del \a
                if tag:
                    self.tag_hold.append(tag)

        # Section <- subsection, less depth
        while curr < last:
            # Close the current opened subsection
            tag = TAGS.get('title%dClose' % last)
            if tag:
                self.tag_hold.append(tag)

            # Close the current opened block of subsections
            tag = TAGS.get('blockTitle%dClose' % last)
            if tag:
                self.tag_hold.append(tag)

            last -= 1

            # Close the previous section of the same level
            # The subsections were under it
            if curr == last:
                tag = TAGS.get('title%dClose' % last)
                if tag:
                    self.tag_hold.append(tag)

    def add(self, line):
        "Parses a new title line."
        if not line:
            return
        self._set_prop(line)
        self._open_close_blocks()
        self._set_count_id()
        self._set_label()
        self._save_toc_info()

    def close_all(self):
        "Closes all opened title blocks"
        ret = []
        ret.extend(self.tag_hold)
        while self.level:
            tag = TAGS.get('title%dClose' % self.level)
            if tag:
                ret.append(tag)
            tag = TAGS.get('blockTitle%dClose' % self.level)
            if tag:
                ret.append(tag)
            self.level -= 1
        return ret

    def _save_toc_info(self):
        "Save TOC info, used by self.dump_marked_toc()"
        self.toc.append((self.level, self.count_id, self.txt, self.label))

    def _set_prop(self, line=''):
        "Extract info from original line and set data holders."
        # Detect title type (numbered or not)
        id_ = line.lstrip()[0]
        if   id_ == '=':
            kind = 'title'
        elif id_ == '+':
            kind = 'numtitle'
        else:
            Error("Unknown Title ID '%s'" % id_)
        # Extract line info
        match = regex[kind].search(line)
        level = len(match.group('id'))
        txt   = match.group('txt').strip()
        label = match.group('label')
        # Parse info & save
        if CONF['enum-title']:
            kind = 'numtitle'  # force
        if rules['titleblocks']:
            self.tag = TAGS.get('%s%dOpen' % (kind, level)) or \
                       TAGS.get('title%dOpen' % level)
        else:
            self.tag = TAGS.get(kind + str(level)) or \
                       TAGS.get('title' + str(level))
        self.last_level = self.level
        self.kind  = kind
        self.level = level
        self.txt   = txt
        self.label = label

    def _set_count_id(self):
        "Compose and save the title count identifier (if needed)."
        count_id = ''
        if self.kind == 'numtitle' and not rules['autonumbertitle']:
            # Manually increase title count
            self.count[self.level] += 1
            # Reset sublevels count (if any)
            max_levels = len(self.count)
            if self.level < max_levels - 1:
                for i in range(self.level + 1, max_levels):
                    self.count[i] = 0
            # Compose count id from hierarchy
            for i in range(self.level):
                count_id = "%s%d." % (count_id, self.count[i + 1])
        self.count_id = count_id

    def _set_label(self):
        "Compose and save title label, used by anchors."
        # Remove invalid chars from label set by user
        self.label = re.sub('[^A-Za-z0-9_-]', '', self.label or '')
        # Generate name as 15 first :alnum: chars
        #TODO how to translate safely accented chars to plain?
        #self.label = re.sub('[^A-Za-z0-9]', '', self.txt)[:15]
        # 'tocN' label - sequential count, ignoring 'toc-level'
        #self.label = self.anchor_prefix + str(len(self.toc) + 1)

    def _get_tagged_anchor(self):
        "Return anchor if user defined a label, or TOC is on."
        ret = ''
        label = self.label
        if CONF['toc'] and self.level <= CONF['toc-level']:
            # This count is needed bcos self.toc stores all
            # titles, regardless of the 'toc-level' setting,
            # so we can't use self.toc length to number anchors
            self.anchor_count += 1
            # Autonumber label (if needed)
            label = label or '%s%s' % (self.anchor_prefix, self.anchor_count)
        if label and TAGS['anchor']:
            ret = regex['x'].sub(label, TAGS['anchor'])
        return ret

    def _get_full_title_text(self):
        "Returns the full title contents, already escaped."
        ret = self.txt
        # Insert count_id (if any) before text
        if self.count_id:
            ret = '%s %s' % (self.count_id, ret)
        # Escape specials
        ret = doEscape(TARGET, ret)
        # Same targets needs final escapes on title lines
        # It's here because there is a 'continue' after title
        if rules['finalescapetitle']:
            ret = doFinalEscape(TARGET, ret)
        return ret

    def get(self):
        "Returns the tagged title as a list."
        global AA_TITLE
        ret = []

        # Maybe some anchoring before?
        anchor = self._get_tagged_anchor()
        self.tag = regex['_anchor'].sub(anchor, self.tag)

        ### Compose & escape title text (TOC uses unescaped)
        full_title = self._get_full_title_text()

        # Close previous section area
        ret.extend(self.tag_hold)
        self.tag_hold = []

        tagged = regex['x'].sub(full_title, self.tag)

        # Adds "underline" on TXT target
        if TARGET == 'txt':
            if BLOCK.count > 1:
                ret.append('')  # blank line before
            ret.append(tagged)
            i = aa_len_cjk(full_title)
            ret.append(regex['x'].sub('=' * i, self.tag))
        elif TARGET == 'aat' and self.level == 1:
            if CONF['slides'] :
                AA_TITLE = tagged
            else :
                if BLOCK.count > 1:
                    ret.append('')  # blank line before
                box = aa_box([tagged], AA, CONF['width'])
                if CONF['web'] and CONF['toc']:
                    ret.extend([anchor] + box + ['</a>'])
                else:
                    ret.extend(box)
        elif TARGET == 'aat':
            level = 'level' + str(self.level)
            if BLOCK.count > 1:
                ret.append('')  # blank line before
            if CONF['slides']:
                under = aa_under(tagged, AA[level], CONF['width'] - 2, False)
            else:
                under = aa_under(tagged, AA[level], CONF['width'], False)
            if CONF['web'] and CONF['toc']:
                ret.extend([anchor] + under + ['</a>']) 
            else:
                ret.extend(under)
        elif TARGET == 'rst' and self.level == 1:
            if BLOCK.count > 1:
                ret.append('')  # blank line before
            ret.extend(aa_under(tagged, RST['level1'], 10000, True))
        elif TARGET == 'rst':
            level = 'level' + str(self.level)
            if BLOCK.count > 1:
                ret.append('')  # blank line before
            ret.extend(aa_under(tagged, RST[level], 10000, False))
        else:
            ret.append(tagged)
        return ret

    def dump_marked_toc(self, max_level=99):
        "Dumps all toc itens as a valid t2t-marked list"
        ret = []
        toc_count = 1
        for level, count_id, txt, label in self.toc:
            if level > max_level:  # ignore
                continue
            indent = '  ' * level
            id_txt = ('%s %s' % (count_id, txt)).lstrip()
            label = label or self.anchor_prefix + str(toc_count)
            toc_count += 1

            # TOC will have crosslinks to anchors
            if TAGS['anchor']:
                if CONF['enum-title'] and level == 1:
                    # 1. [Foo #anchor] is more readable than [1. Foo #anchor] in level 1.
                    # This is a stoled idea from Windows .CHM help files.
                    tocitem = '%s+ [""%s"" #%s]' % (indent, txt, label)
                else:
                    tocitem = '%s- [""%s"" #%s]' % (indent, id_txt, label)

            # TOC will be plain text (no links)
            else:
                if TARGET in ['txt', 'man', 'aat']:
                    # For these, the list is not necessary, just dump the text
                    tocitem = '%s""%s""' % (indent, id_txt)
                else:
                    tocitem = '%s- ""%s""' % (indent, id_txt)
            ret.append(tocitem)
        return ret


##############################################################################

# Table syntax reference for targets:
# http://www.mediawiki.org/wiki/Help:Tables
# http://moinmo.in/HelpOnMoinWikiSyntax#Tables
# http://moinmo.in/HelpOnTables
# http://www.wikicreole.org/wiki/Creole1.0#section-Creole1.0-Tables
# http://www.wikicreole.org/wiki/Tables
# http://www.pmwiki.org/wiki/PmWiki/Tables
# http://www.dokuwiki.org/syntax#tables
# http://michelf.com/projects/php-markdown/extra/#table
# http://code.google.com/p/support/wiki/WikiSyntax#Tables
# http://www.biblioscape.com/rtf15_spec.htm
# http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#tables
#
# Good reading:
# http://www.wikicreole.org/wiki/ListOfTableMarkups
#
# See also:
# test/marks/table.t2t
# test/target/table.t2t

#TODO check all this table mess
# It uses parse_row properties for table lines
# BLOCK.table() replaces the cells by the parsed content
#
class TableMaster:
    def __init__(self, line=''):
        self.rows      = []
        self.border    = 0
        self.align     = 'Left'
        self.cellalign = []
        self.colalign  = []
        self.cellspan  = []
        if line:
            prop = self.parse_row(line)
            self.border    = prop['border']
            self.title     = prop['title']
            self.align     = prop['align']
            self.cellalign = prop['cellalign']
            self.cellspan  = prop['cellspan']
            self.n_cols    = str(sum(self.cellspan))
            self.colalign  = self._get_col_align()

    def _get_col_align(self):
        colalign = []
        for cell in range(0, len(self.cellalign)):
            align = self.cellalign[cell]
            span  = self.cellspan[cell]
            colalign.extend([align] * span)
        return colalign

    def _get_full_tag(self, topen):
        # topen     = TAGS['tableOpen']
        tborder   = TAGS['_tableBorder']
        talign    = TAGS['_tableAlign' + self.align]
        calignsep = TAGS['tableColAlignSep']
        calign    = ''

        # The first line defines if table has border or not
        if not self.border:
            tborder = ''
        # Set the columns alignment
        if rules['tablecellaligntype'] == 'column':
            calign = [TAGS['_tableColAlign%s' % x] for x in self.colalign]
            calign = calignsep.join(calign)
        # Align full table, set border and Column align (if any)
        topen = regex['_tableAlign'].sub(talign , topen)
        topen = regex['_tableBorder'].sub(tborder, topen)
        topen = regex['_tableColAlign'].sub(calign , topen)
        # Tex table spec, border or not: {|l|c|r|} , {lcr}
        if calignsep and not self.border:
            # Remove cell align separator
            topen = topen.replace(calignsep, '')
        return topen

    def _get_cell_align(self, cells):
        ret = []
        for cell in cells:
            align = 'Left'
            if cell.strip():
                if cell[0] == ' ' and cell[-1] == ' ':
                    align = 'Center'
                elif cell[0] == ' ':
                    align = 'Right'
            ret.append(align)
        return ret

    def _get_cell_span(self, cells):
        ret = []
        for cell in cells:
            span = 1
            m = re.search('\a(\|+)$', cell)
            if m:
                span = len(m.group(1)) + 1
            ret.append(span)
        return ret

    def _tag_cells(self, rowdata):
        cells = rowdata['cells']
        open_ = TAGS['tableCellOpen']
        close = TAGS['tableCellClose']
        sep = TAGS['tableCellSep']
        head = TAGS['tableCellHead']
        calign = [TAGS['_tableCellAlign' + x] for x in rowdata['cellalign']]
        caligntag = [TAGS['tableCellAlign' + x] for x in rowdata['cellalign']]
        calignsep = TAGS['tableColAlignSep']
        ncolumns = len(self.colalign)

        # Populate the span and multicol open tags
        cspan = []
        multicol = []
        colindex = 0

        thisspan = 0
        spanmultiplier = rules['cellspanmultiplier'] or 1

        cellhead = []
        cellbody = []

        for cellindex in range(0, len(rowdata['cellspan'])):

            span = rowdata['cellspan'][cellindex]
            align = rowdata['cellalign'][cellindex]

            # hack to get cell size/span into rtf, in twips
            if rules['cellspancumulative']:
                thisspan += span
            else:
                thisspan = span
            span = thisspan * spanmultiplier

            if span > 1:

                if TAGS['_tableCellColSpanChar']:
                    # spanchar * n
                    cspan.append(TAGS['_tableCellColSpanChar'] * (span - 1))
                    # Note: using -1 for moin, where spanchar == cell delimiter
                else:
                    # \a replaced by n
                    cspan.append(regex['x'].sub(str(span), TAGS['_tableCellColSpan']))

                mcopen = regex['x'].sub(str(span), TAGS['_tableCellMulticolOpen'])
                multicol.append(mcopen)
            else:
                cspan.append('')

                if colindex < ncolumns and align != self.colalign[colindex]:
                    mcopen = regex['x'].sub('1', TAGS['_tableCellMulticolOpen'])
                    multicol.append(mcopen)
                else:
                    multicol.append('')

            if not self.border:
                multicol[-1] = multicol[-1].replace(calignsep, '')

            colindex += span

        # Maybe is it a title row?
        if rowdata['title']:
            # Defaults to normal cell tag if not found
            open_ = TAGS['tableTitleCellOpen']  or open_
            close = TAGS['tableTitleCellClose'] or close
            sep   = TAGS['tableTitleCellSep']   or sep
            head  = TAGS['tableTitleCellHead']  or head

        # Should we break the line on *each* table cell?
        if rules['breaktablecell']:
            close = close + '\n'

        # Cells pre processing
        if rules['tablecellstrip']:
            cells = [x.strip() for x in cells]
        if rowdata['title'] and rules['tabletitlerowinbold']:
            cells = [enclose_me('fontBold', x) for x in cells]

        # Add cell BEGIN/END tags
        for cell in cells:
            copen = open_
            cclose = close
            chead = head

            # Make sure we will pop from some filled lists
            # Fixes empty line bug '| |'
            this_align = this_cell = this_span = this_mcopen = ''
            if calign:
                this_align = calign.pop(0)
            if caligntag:
                this_cell = caligntag.pop(0)
            if cspan:
                this_span = cspan.pop(0)
            if multicol:
                this_mcopen = multicol.pop(0)

            # Insert cell align into open tag (if cell is alignable)
            if rules['tablecellaligntype'] == 'cell':
                copen = regex['_tableCellAlign'].sub(this_align, copen)
                cclose = regex['_tableCellAlign'].sub(this_align, cclose)
                chead = regex['_tableCellAlign'].sub(this_align, chead)

                # Insert cell data into cellAlign tags
                if this_cell:
                    cell = regex['x'].sub(cell, this_cell)

            # Insert cell span into open tag (if cell is spannable)
            if rules['tablecellspannable']:
                copen = regex['_tableCellColSpan'].sub(this_span, copen)
                cclose = regex['_tableCellColSpan'].sub(this_span, cclose)
                chead = regex['_tableCellColSpan'].sub(this_span, chead)

            # Use multicol tags instead (if multicol supported, and if
            # cell has a span or is aligned differently to column)
            if rules['tablecellmulticol']:
                if this_mcopen:
                    copen = regex['_tableColAlign'].sub(this_align, this_mcopen)
                    cclose = TAGS['_tableCellMulticolClose']

            # RTF target requires the border in each cell
            border = ''
            if self.border:
                border = TAGS['_tableCellBorder']
            copen = regex['_tableBorder'].sub(border, copen)
            cclose = regex['_tableBorder'].sub(border, cclose)
            chead = regex['_tableBorder'].sub(border, chead)

            # Attribute delimiter, added when align/span attributes were used
            # Example: Wikipedia table cell, without and with attributes:
            # | cell contents
            # | align="right" colspan="2" | cell contents
            #
            if regex['_tableAttrDelimiter'].search(copen):
                if this_align or this_span:
                    copen = regex['_tableAttrDelimiter'].sub(TAGS['_tableAttrDelimiter'], copen)
                else:
                    copen = regex['_tableAttrDelimiter'].sub('', copen)  # remove marker

            if chead:
                cellhead.append(chead)
            cellbody.append(copen + cell + cclose)

        # Maybe there are cell separators?
        return ''.join(cellhead) + sep.join(cellbody)

    def add_row(self, cells):
        self.rows.append(cells)

    def parse_row(self, line):
        # Default table properties
        ret = {
            'border': 0, 'title': 0, 'align': 'Left',
            'cells': [], 'cellalign': [], 'cellspan': []
        }
        # Detect table align (and remove spaces mark)
        if line[0] == ' ':
            ret['align'] = 'Center'
        line = line.lstrip()
        # Detect title mark
        if line[1] == '|':
            ret['title'] = 1
        # Detect border mark and normalize the EOL
        m = re.search(' (\|+) *$', line)
        if m:
            line = line + ' '
            ret['border'] = 1
        else:
            line = line + ' | '
        # Delete table mark
        line = regex['table'].sub('', line)
        # Detect colspan  | foo | bar baz |||
        line = re.sub(' (\|+)\| ', '\a\\1 | ', line)
        # Split cells (the last is fake)
        ret['cells'] = line.split(' | ')[:-1]
        # Find cells span
        ret['cellspan'] = self._get_cell_span(ret['cells'])
        # Remove span ID
        ret['cells'] = [re.sub('\a\|+$', '', x) for x in ret['cells']]
        # Find cells align
        ret['cellalign'] = self._get_cell_align(ret['cells'])
        # Hooray!
        Debug('Table Prop: %s' % ret, 7)
        return ret

    def dump(self):
        open_ = self._get_full_tag(TAGS['tableOpen'])
        rows  = self.rows
        close = self._get_full_tag(TAGS['tableClose'])

        rowopen     = self._get_full_tag(TAGS['tableRowOpen'])
        rowclose    = self._get_full_tag(TAGS['tableRowClose'])
        rowsep      = self._get_full_tag(TAGS['tableRowSep'])
        titrowopen  = self._get_full_tag(TAGS['tableTitleRowOpen'])  or rowopen
        titrowclose = self._get_full_tag(TAGS['tableTitleRowClose']) or rowclose

        if rules['breaktablelineopen']:
            rowopen = rowopen + '\n'
            titrowopen = titrowopen + '\n'

        # Tex gotchas
        if TARGET == 'tex':
            if not self.border:
                rowopen = titrowopen = ''
            else:
                close = rowopen + close

        # Now we tag all the table cells on each row
        #tagged_cells = map(lambda x: self._tag_cells(x), rows)  #!py15
        tagged_cells = []
        for cell in rows:
            tagged_cells.append(self._tag_cells(cell))

        # Add row separator tags between lines
        tagged_rows = []
        if rowsep:
            #!py15
            #tagged_rows = map(lambda x: x + rowsep, tagged_cells)
            for cell in tagged_cells:
                tagged_rows.append(cell + rowsep)
            # Remove last rowsep, because the table is over
            tagged_rows[-1] = tagged_rows[-1].replace(rowsep, '')
        # Add row BEGIN/END tags for each line
        else:
            for rowdata in rows:
                if rowdata['title']:
                    o, c = titrowopen, titrowclose
                else:
                    o, c = rowopen, rowclose
                row = tagged_cells.pop(0)
                tagged_rows.append(o + row + c)

        # Join the pieces together
        fulltable = []
        if open_:
            fulltable.append(open_)
        fulltable.extend(tagged_rows)
        if close:
            fulltable.append(close)

        return fulltable


##############################################################################


class BlockMaster:
    "TIP: use blockin/out to add/del holders"
    def __init__(self):
        self.BLK = []
        self.HLD = []
        self.PRP = []
        self.depth = 0
        self.count = 0
        self.last = ''
        self.tableparser = None
        self.tablecount = 0
        self.contains = {
            'para'    : ['comment', 'raw', 'tagged'],
            'verb'    : [],
            'table'   : ['comment'],
            'raw'     : [],
            'tagged'  : [],
            'comment' : [],
            'quote'   : ['quote', 'comment', 'raw', 'tagged'],
            'list'    : ['list', 'numlist', 'deflist', 'para', 'verb', 'comment', 'raw', 'tagged'],
            'numlist' : ['list', 'numlist', 'deflist', 'para', 'verb', 'comment', 'raw', 'tagged'],
            'deflist' : ['list', 'numlist', 'deflist', 'para', 'verb', 'comment', 'raw', 'tagged'],
            'bar'     : [],
            'title'   : [],
            'numtitle': [],
        }
        self.allblocks = list(self.contains.keys())

        # If one is found inside another, ignore the marks
        self.exclusive = ['comment', 'verb', 'raw', 'tagged']

        # May we include bars inside quotes?
        if rules['barinsidequote']:
            self.contains['quote'].append('bar')

    def block(self):
        if not self.BLK:
            return ''
        return self.BLK[-1]

    def isblock(self, name=''):
        return self.block() == name

    def prop(self, key):
        if not self.PRP:
            return ''
        return self.PRP[-1].get(key) or ''

    def propset(self, key, val):
        self.PRP[-1][key] = val
        #Debug('BLOCK prop ++: %s->%s' % (key, repr(val)), 1)
        #Debug('BLOCK props: %s' % (repr(self.PRP)), 1)

    def hold(self):
        if not self.HLD:
            return []
        return self.HLD[-1]

    def holdadd(self, line):
        if self.block().endswith('list'):
            line = [line]
        self.HLD[-1].append(line)
        Debug('HOLD add: %s' % repr(line), 4)
        Debug('FULL HOLD: %s' % self.HLD, 4)

    def holdaddsub(self, line):
        self.HLD[-1][-1].append(line)
        Debug('HOLD addsub: %s' % repr(line), 4)
        Debug('FULL HOLD: %s' % self.HLD, 4)

    def holdextend(self, lines):
        if self.block().endswith('list'):
            lines = [lines]
        self.HLD[-1].extend(lines)
        Debug('HOLD extend: %s' % repr(lines), 4)
        Debug('FULL HOLD: %s' % self.HLD, 4)

    def blockin(self, block):
        ret = []
        if block not in self.allblocks:
            Error("Invalid block '%s'" % block)

        # First, let's close other possible open blocks
        while self.block() and block not in self.contains[self.block()]:
            ret.extend(self.blockout())

        # Now we can gladly add this new one
        self.BLK.append(block)
        self.HLD.append([])
        self.PRP.append({})
        self.count += 1
        if block == 'table':
            self.tableparser = TableMaster()
        # Deeper and deeper
        self.depth = len(self.BLK)
        Debug('block ++ (%s): %s' % (block, self.BLK), 3)
        return ret

    def blockout(self):
        global AA_COUNT

        if not self.BLK:
            Error('No block to pop')
        blockname = self.BLK.pop()
        result = getattr(self, blockname)()
        parsed = self.HLD.pop()
        self.PRP.pop()
        self.depth = len(self.BLK)

        if CONF['spread'] and blockname != 'table':
            return []

        if blockname == 'table':
            del self.tableparser

        # Inserting a nested block into mother
        if self.block():
            if blockname != 'comment':  # ignore comment blocks
                if self.block().endswith('list'):
                    self.HLD[-1][-1].append(result)
                else:
                    self.HLD[-1].append(result)
            # Reset now. Mother block will have it all
            result = []

        Debug('block -- (%s): %s' % (blockname, self.BLK), 3)
        Debug('RELEASED (%s): %s' % (blockname, parsed), 3)

        # Save this top level block name (produced output)
        # The next block will use it
        if result:
            self.last = blockname
            if TARGET == 'aat':
                final = []
                if CONF['slides'] and blockname in ('list', 'numlist', 'deflist'):
                    li = []
                    for el in result:
                        li.append(el)
                    final.extend(' ' + line for line in aa_box(li, AA, CONF['width'] - 2, False))
                else:
                    for line in result:
                        if not line or (blockname == 'table' and not CONF['slides']): 
                            final.append(line)
                        else:
                            if CONF['slides'] and blockname == 'table':
                                final.append(line[:CONF['width']])
                            elif CONF['slides']:
                                final.extend(' ' + line for line in textwrap.wrap(line, CONF['width'] - 2))
                            elif CONF['web'] and '<' in line:
                                final.extend(aa_webwrap(line, CONF['width']))
                            else:
                                final.extend(textwrap.wrap(line, CONF['width']))
                result = final[:]

            Debug('BLOCK: %s' % result, 6)

        # ASCII Art processing
        global AA_TITLE
        if TARGET == 'aat' and CONF['slides'] and not CONF['toc-only'] and not CONF.get('art-no-title'):
            n = (CONF['height'] - 1) - (AA_COUNT % (CONF['height'] - 1) + 1)
            if n < len(result) and not (TITLE.level == 1 and blockname in ["title", "numtitle"]):
                if CONF['web']:
                    result = ([''] * n) + [aa_line(AA['bar1'], CONF['width']) + '</pre></section>'] + aa_slide(AA_TITLE, AA['bar2'], CONF['width'], True) + [''] + result
                else:
                    result = ([''] * n) + [aa_line(AA['bar1'], CONF['width'])] + aa_slide(AA_TITLE, AA['bar2'], CONF['width'], False) + [''] + result
            if (blockname in ["title", "numtitle"] and TITLE.level == 1) or not AA_TITLE:
                if not AA_TITLE:
                    if CONF['headers']:
                        AA_TITLE = CONF['header1'] or ' '
                    else:
                        AA_TITLE = ' '
                aa_title = aa_slide(AA_TITLE, AA['bar2'], CONF['width'], CONF['web']) + ['']
                if AA_COUNT:
                    if CONF['web']:
                        aa_title = ([''] * n) + [aa_line(AA['bar2'], CONF['width']) + '</pre></section>'] + aa_title
                    else:
                        aa_title = ([''] * n) + [aa_line(AA['bar2'], CONF['width'])] + aa_title
                result = aa_title + result
            AA_COUNT += len(result)

        return result

    def _last_escapes(self, line):
        return doFinalEscape(TARGET, line)

    def _get_escaped_hold(self):
        ret = []
        for line in self.hold():
            linetype = type(line)
            if linetype == type('') or linetype == type(''):
                ret.append(self._last_escapes(line))
            elif linetype == type([]):
                ret.extend(line)
            else:
                Error("BlockMaster: Unknown HOLD item type: %s" % linetype)
        return ret

    def _remove_twoblanks(self, lastitem):
        if len(lastitem) > 1 and lastitem[-2:] == ['', '']:
            return lastitem[:-2]
        return lastitem

    def _should_add_blank_line(self, where, blockname):
        "Validates the blanksaround* rules"

        # Nestable blocks: only mother blocks (level 1) are spaced
        if blockname.endswith('list') and self.depth > 1:
            return False

        # The blank line after the block is always added
        if where == 'after' \
            and rules['blanksaround' + blockname]:
            return True

        # # No blank before if it's the first block of the body
        # elif where == 'before' \
        #   and BLOCK.count == 1:
        #   return False

        # # No blank before if it's the first block of this level (nested)
        # elif where == 'before' \
        #   and self.count == 1:
        #   return False

        # The blank line before the block is only added if
        # the previous block haven't added a blank line
        # (to avoid consecutive blanks)
        elif where == 'before' \
            and rules['blanksaround' + blockname] \
            and not rules.get('blanksaround' + self.last):
            return True

        # Nested quotes are handled here,
        # because the mother quote isn't closed yet
        elif where == 'before' \
            and blockname == 'quote' \
            and rules['blanksaround' + blockname] \
            and self.depth > 1:
            return True

        return False

    # functions to help encode block depth into RTF formatting
    def _apply_depth(self, line, level):
        # convert block depth into an indent in twips
        depth = level
        multiply = rules['blockdepthmultiply']
        if depth > 0 and rules['depthmultiplyplus']:
            depth = depth + rules['depthmultiplyplus']
        if multiply:
            depth = depth * multiply
        return regex['_blockDepth'].sub(str(depth), line)

    def _apply_list_level(self, line, level):
        mylevel = level
        if rules['listlevelzerobased']:
            mylevel = mylevel - 1
        return regex['_listLevel'].sub(str(mylevel), line)

    def comment(self):
        return ''

    def raw(self):
        lines = self.hold()
        return [doEscape(TARGET, x) for x in lines]

    def tagged(self):
        return self.hold()

    def para(self):
        result = []
        open_ = TAGS['paragraphOpen']
        close = TAGS['paragraphClose']
        lines = self._get_escaped_hold()

        # Blank line before?
        if self._should_add_blank_line('before', 'para'):
            result.append('')

        # RTF needs depth level encoded into nested paragraphs
        mydepth = self.depth
        if rules['zerodepthparagraph']:
            mydepth = 0
        open_ = self._apply_depth(open_, mydepth)

        # Open tag
        if open_:
            result.append(open_)

        # Pagemaker likes a paragraph as a single long line
        if rules['onelinepara']:
            result.append(' '.join(lines))
        # Others are normal :)
        else:
            result.extend(lines)

        # Close tag
        if close:
            result.append(close)

        # Blank line after?
        if self._should_add_blank_line('after', 'para'):
            result.append('')

        # Very very very very very very very very very UGLY fix
        # Needed because <center> can't appear inside <p>
        try:
            if len(lines) == 1 and \
               TARGET in ('html', 'xhtml', 'xhtmls') and \
               re.match('^\s*<center>.*</center>\s*$', lines[0]):
                result = [lines[0]]
        except:
            pass

        return result

    def verb(self):
        "Verbatim lines are not masked, so there's no need to unmask"
        result = []
        open_ = TAGS['blockVerbOpen']
        close = TAGS['blockVerbClose']
        sep = TAGS['blockVerbSep']

        # Blank line before?
        if self._should_add_blank_line('before', 'verb'):
            result.append('')

        # Open tag
        if open_:
            result.append(open_)

        # Get contents
        for line in self.hold():
            if self.prop('mapped') == 'table':
                line = MacroMaster().expand(line)
            if not rules['verbblocknotescaped']:
                line = doEscape(TARGET, line)
            if TAGS['blockVerbLine']:
                line = TAGS['blockVerbLine'] + line
            if rules['indentverbblock']:
                line = '  ' + line
            if rules['verbblockfinalescape']:
                line = doFinalEscape(TARGET, line)
            result.append(line)
            if sep:
                result.append(sep)

        if sep:
            result.pop()

        # Close tag
        if close:
            result.append(close)

        # Blank line after?
        if self._should_add_blank_line('after', 'verb'):
            result.append('')

        return result

    def numtitle(self):
        return self.title('numtitle')

    def title(self, name='title'):
        result = []

        # Blank line before?
        if self._should_add_blank_line('before', name):
            result.append('')

        # Get contents
        result.extend(TITLE.get())

        # Blank line after?
        if self._should_add_blank_line('after', name):
            result.append('')

        return result

    def table(self):
        self.tablecount += 1 
        result = []

        if TARGET == 'aat':
            if CONF['spread']:
                return aa_table(self.tableparser.rows, AA, CONF['width'], True, True, True, 'Center', True, CONF['web']) + ['']
            else:
                return aa_table(self.tableparser.rows, AA, CONF['width'], self.tableparser.border, self.tableparser.title, False, self.tableparser.align, False, False) + ['']

        if TARGET == 'rst':
            chars = AA.copy()
            if not self.tableparser.border:
                chars['border'], chars['corner'], chars['side'] = '=', ' ', ' '
            return aa_table(self.tableparser.rows, chars, CONF['width'], self.tableparser.border, self.tableparser.title, False, 'Left', False, False) + ['']

        if TARGET == 'mgp':
            aa_t = aa_table(self.tableparser.rows, AA, CONF['width'], True, self.tableparser.title, False, 'Left', False, False)
            try:
                import aafigure
                t_name = 'table_' + str(self.tablecount) + '.png'
                aafigure.render(str('\n'.join(aa_t)), t_name, {'format':'png', 'background':'#000000', 'foreground':'#FFFFFF', 'textual':True})  
                return ['%center', '%newimage "' + t_name + '"']
            except:
                return ['%font "mono"'] + aa_t + ['']

        if TARGET == 'csv':
            return [','.join([cell.strip() for cell in row['cells']]) for row in self.tableparser.rows] + ['']

        # Blank line before?
        if self._should_add_blank_line('before', 'table'):
            result.append('')

        # DocBook needs to know the number of columns
        if TARGET == 'dbk':
            result.append(re.sub('n_cols', self.tableparser.n_cols, TAGS['tableOpenDbk']))

        # Rewrite all table cells by the unmasked and escaped data
        lines = self._get_escaped_hold()
        for i in range(len(lines)):
            cells = lines[i].split(SEPARATOR)
            self.tableparser.rows[i]['cells'] = cells
        result.extend(self.tableparser.dump())

        # Blank line after?
        if self._should_add_blank_line('after', 'table'):
            result.append('')

        if TARGET == 'ods':
            result[0] = result[0][:-2] + ' ' + str(self.tablecount) + '">'

        return result

    def quote(self):
        result = []
        open_  = TAGS['blockQuoteOpen']            # block based
        close  = TAGS['blockQuoteClose']
        qline  = TAGS['blockQuoteLine']            # line based
        indent = tagindent = '\t' * self.depth

        # Apply rules
        if rules['tagnotindentable']:
            tagindent = ''
        if not rules['keepquoteindent']:
            indent = ''

        # Blank line before?
        if self._should_add_blank_line('before', 'quote'):
            result.append('')

        # RTF needs depth level encoded into almost everything
        open_ = self._apply_depth(open_, self.depth)

        # Open tag
        if open_:
            result.append(tagindent + open_)

        itemisclosed = False

        # Get contents
        for item in self.hold():
            if type(item) == type([]):
                if close and rules['quotenotnested']:
                    result.append(tagindent + close)
                    itemisclosed = True
                result.extend(item)        # subquotes
            else:
                if open_ and itemisclosed:
                    result.append(tagindent + open_)
                item = regex['quote'].sub('', item)  # del TABs
                item = self._last_escapes(item)
                if CONF['target'] == 'aat' and CONF['slides']:
                    result.extend(aa_box([item], AA, CONF['width'] - 2))
                else:
                    item = qline * self.depth + item
                    result.append(indent + item)  # quote line

        # Close tag
        if close and not itemisclosed:
            result.append(tagindent + close)

        # Blank line after?
        if self._should_add_blank_line('after', 'quote'):
            result.append('')

        return result

    def bar(self):
        result = []
        bar_tag = ''

        # Blank line before?
        if self._should_add_blank_line('before', 'bar'):
            result.append('')

        # Get the original bar chars
        bar_chars = self.hold()[0].strip()

        # Set bar type
        if bar_chars.startswith('='):
            bar_tag = TAGS['bar2']
        else:
            bar_tag = TAGS['bar1']

        # To avoid comment tag confusion like <!-- ------ --> (sgml)
        if TAGS['comment'].count('--'):
            bar_chars = bar_chars.replace('--', '__')

        # Get the bar tag (may contain \a)
        result.append(regex['x'].sub(bar_chars, bar_tag))

        # Blank line after?
        if self._should_add_blank_line('after', 'bar'):
            result.append('')

        return result

    def deflist(self):
        return self.list('deflist')

    def numlist(self):
        return self.list('numlist')

    def list(self, name='list'):
        result    = []
        items     = self.hold()
        indent    = self.prop('indent')
        tagindent = indent
        listline  = TAGS.get(name + 'ItemLine')
        itemcount = 0

        if name == 'deflist':
            itemopen  = TAGS[name + 'Item1Open']
            itemclose = TAGS[name + 'Item2Close']
            itemsep   = TAGS[name + 'Item1Close'] +\
                        TAGS[name + 'Item2Open']
        else:
            itemopen  = TAGS[name + 'ItemOpen']
            itemclose = TAGS[name + 'ItemClose']
            itemsep   = ''

        # Apply rules
        if rules['tagnotindentable']:
            tagindent = ''
        if not rules['keeplistindent']:
            indent = tagindent = ''

        # RTF encoding depth
        itemopen = self._apply_depth(itemopen, self.depth)
        itemopen = self._apply_list_level(itemopen, self.depth)

        # ItemLine: number of leading chars identifies list depth
        if listline:
            if rules['listlineafteropen']:
                itemopen  = itemopen + listline * self.depth
            else:
                itemopen  = listline * self.depth + itemopen

        # Adds trailing space on opening tags
        if (name == 'list'    and rules['spacedlistitemopen']) or \
           (name == 'numlist' and rules['spacednumlistitemopen']):
            itemopen = itemopen + ' '

        # Remove two-blanks from list ending mark, to avoid <p>
        items[-1] = self._remove_twoblanks(items[-1])

        # Blank line before?
        if self._should_add_blank_line('before', name):
            result.append('')

        if rules['blanksaroundnestedlist']:
            result.append('')

        # Tag each list item (multiline items), store in listbody
        itemopenorig = itemopen
        listbody = []
        widelist = 0
        for item in items:

            # Add "manual" item count for noautonum targets
            itemcount += 1
            if name == 'numlist' and not rules['autonumberlist']:
                n = str(itemcount)
                itemopen = regex['x'].sub(n, itemopenorig)
                del n

            # Tag it
            item[0] = self._last_escapes(item[0])
            if name == 'deflist':
                z, term, rest = item[0].split(SEPARATOR, 2)
                item[0] = rest
                if not item[0]:
                    del item[0]      # to avoid <p>
                listbody.append(tagindent + itemopen + term + itemsep)
            else:
                fullitem = tagindent + itemopen
                listbody.append(item[0].replace(SEPARATOR, fullitem))
                del item[0]

            itemisclosed = False

            # Process next lines for this item (if any)
            for line in item:
                if type(line) == type([]):  # sublist inside
                    if rules['listitemnotnested'] and itemclose:
                        listbody.append(tagindent + itemclose)
                        itemisclosed = True
                    if TARGET == 'rst' and name == 'deflist':
                        del line[0]
                    listbody.extend(line)
                else:
                    line = self._last_escapes(line)

                    # Blank lines turns to <p>
                    if not line and rules['parainsidelist']:
                        line = indent + TAGS['paragraphOpen'] + TAGS['paragraphClose']
                        line = line.rstrip()
                        widelist = 1
                    elif not line and TARGET == 'rtf':
                        listbody.append(TAGS['paragraphClose'])
                        line = TAGS['paragraphOpen']
                        line = self._apply_depth(line, self.depth)

                    # Some targets don't like identation here (wiki)
                    if not rules['keeplistindent'] or (name == 'deflist' and rules['deflisttextstrip']):
                        line = line.lstrip()

                    # Maybe we have a line prefix to add? (wiki)
                    if name == 'deflist' and TAGS['deflistItem2LinePrefix']:
                        line = TAGS['deflistItem2LinePrefix'] + line

                    listbody.append(line)

            # Close item (if needed)
            if itemclose and not itemisclosed:
                listbody.append(tagindent + itemclose)

        if not widelist and rules['compactlist']:
            listopen = TAGS.get(name + 'OpenCompact')
            listclose = TAGS.get(name + 'CloseCompact')
        else:
            listopen  = TAGS.get(name + 'Open')
            listclose = TAGS.get(name + 'Close')

        # Open list (not nestable lists are only opened at mother)
        if listopen and not \
           (rules['listnotnested'] and BLOCK.depth != 1):
            result.append(tagindent + listopen)

        result.extend(listbody)

        # Close list (not nestable lists are only closed at mother)
        if listclose and not \
           (rules['listnotnested'] and self.depth != 1):
            result.append(tagindent + listclose)

        # Blank line after?
        if self._should_add_blank_line('after', name):
            result.append('')

        if rules['blanksaroundnestedlist']:
            if result[-1]:
                result.append('')

        return result


##############################################################################


class MacroMaster:
    def __init__(self, config={}):
        self.name     = ''
        self.config   = config or CONF
        self.infile   = self.config['sourcefile']
        self.outfile  = self.config['outfile']
        self.currentfile = self.config['currentsourcefile']
        self.currdate = time.localtime(time.time())
        self.rgx      = regex.get('macros') or getRegexes()['macros']
        self.fileinfo = {'infile': None, 'outfile': None}
        self.dft_fmt  = MACROS

    def walk_file_format(self, fmt):
        "Walks the %%{in/out}file format string, expanding the % flags"
        i = 0
        ret = ''
        while i < len(fmt):                     # char by char
            c = fmt[i]
            i += 1
            if c == '%':                        # hot char!
                if i == len(fmt):               # % at the end
                    ret = ret + c
                    break
                c = fmt[i]                      # read next
                i += 1
                ret = ret + self.expand_file_flag(c)
            else:
                ret = ret + c                   # common char
        return ret

    def expand_file_flag(self, flag):
        "%f: filename          %F: filename (w/o extension)"
        "%d: dirname           %D: dirname (only parent dir)"
        "%p: file path         %e: extension"
        info = self.fileinfo[self.name]         # get dict
        if   flag == '%':
            x = '%'                             # %% -> %
        elif flag == 'f':
            x = info['name']
        elif flag == 'F':
            x = os.path.splitext(info['name'])[0]
        elif flag == 'd':
            x = info['dir']
        elif flag == 'D':
            x = os.path.split(info['dir'])[-1]
        elif flag == 'p':
            x = info['path']
        elif flag == 'e':
            x = os.path.splitext(info['name'])[1].replace('.', '')
        else:
            x = '%' + flag                      # false alarm
        return x

    def set_file_info(self, macroname):
        if (macroname == 'currentfile'):
            self.currentfile = self.config['currentsourcefile']
        else:
            if self.fileinfo.get(macroname):    # already done
                return
        file_ = getattr(self, self.name)        # self.infile
        if file_ == STDOUT or file_ == MODULEOUT:
            dir_ = ''
            path = name = file_
        else:
            path = os.path.abspath(file_)
            dir_ = os.path.dirname(path)
            name = os.path.basename(path)
        self.fileinfo[macroname] = {'path': path, 'dir': dir_, 'name': name}

    def expand(self, line=''):
        "Expand all macros found on the line"
        while self.rgx.search(line):
            m = self.rgx.search(line)
            name = self.name = m.group('name').lower()
            fmt = m.group('fmt') or self.dft_fmt.get(name)
            if name == 'date':
                txt = time.strftime(fmt, self.currdate)
            elif name == 'mtime':
                if self.infile in (STDIN, MODULEIN):
                    fdate = self.currdate
                elif PathMaster().is_url(self.infile):
                    try:
                        # Doing it the easy way: fetching the URL again.
                        # The right way would be doing it in Readfile().
                        # But I'm trying to avoid yet another global var
                        # or fake 'sourcefile_mtime' config.
                        #
                        # >>> f= urllib.urlopen('http://txt2tags.org/index.t2t')
                        # >>> f.info().get('last-modified')
                        # 'Thu, 18 Nov 2010 22:42:11 GMT'
                        # >>>
                        #
                        from urllib.request import urlopen
                        from email.Utils import parsedate

                        f = urlopen(self.infile)
                        mtime_rfc2822 = f.info().get('last-modified')
                        fdate = parsedate(mtime_rfc2822)
                    except:
                        # If mtime cannot be found, defaults to current date
                        fdate = self.currdate
                else:
                    mtime = os.path.getmtime(self.infile)
                    fdate = time.localtime(mtime)
                txt = time.strftime(fmt, fdate)
            elif name in ('infile', 'outfile', 'currentfile'):
                self.set_file_info(name)
                txt = self.walk_file_format(fmt)
            elif name == 'appurl':
                txt = my_url
            elif name == 'appname':
                txt = my_name
            elif name == 'appversion':
                txt = my_version
            elif name == 'target':
                txt = TARGET
            elif name == 'encoding':
                txt = self.config['encoding']
            elif name == 'cmdline':
                txt = '%s %s' % (my_name, ' '.join(self.config['realcmdline']))
            elif name in ('header1', 'header2', 'header3'):
                txt = self.config[name]
            elif name == 'cc':
                txt = cc_formatter(self.config, fmt)
            else:
                # Never reached because the macro regex list the valid keys
                Error("Unknown macro name '%s'" % name)
            line = self.rgx.sub(txt, line, 1)
        return line


##############################################################################

def cc_formatter(conf, size):
    cc, target = conf['cc'].lower(), conf['target']
    licenses = 'by, by-sa, by-nc-sa, by-nd, by-nc-nd, by-nc'
    if cc not in licenses.split(', '):
        Error(_('Please, choose one of the six valid Creative Commons licenses : %s.') % licenses)
    if target in ('html', 'xhtml', 'xhtmls', 'html5') or (target == 'aat' and conf['web']):
        if size == 'small':
            end_img = '/3.0/80x15.png'
        else:
            end_img = '/3.0/88x31.png'
        url = 'http://creativecommons.org/licenses/' + cc + '/3.0'
        img = 'http://i.creativecommons.org/l/' + cc + end_img
        alt = 'Creative Commons ' + cc
        ret = '<a href="' + url + '"><img src="' + img + '" alt="' + alt + '"></a>' 
    else:
        if size == 'small':
            ret = 'Creative Commons %s' % cc
        else:
            ret = 'Creative Commons %s' % cc.upper()
    return ret


def listTargets():
    """list all available targets"""
    for typ in TARGET_TYPES:
        targets = list(TARGET_TYPES[typ][1])
        targets.sort()
        print()
        print(TARGET_TYPES[typ][0] + ':')
        for target in targets:
            print("\t%s\t%s" % (target, TARGET_NAMES.get(target)))
    print()


def dumpConfig(source_raw, parsed_config):
    onoff = {1: _('ON'), 0: _('OFF')}
    data = [
        (_('RC file')        , RC_RAW     ),
        (_('source document'), source_raw ),
        (_('command line')   , CMDLINE_RAW)
    ]
    # First show all RAW data found
    for label, cfg in data:
        print(_('RAW config for %s') % label)
        for target, key, val in cfg:
            target = '(%s)' % target
            key    = dotted_spaces("%-14s" % key)
            val    = val or _('ON')
            print('  %-8s %s: %s' % (target, key, val))
        print()
    # Then the parsed results of all of them
    print(_('Full PARSED config'))
    keys = list(parsed_config.keys())
    keys.sort()  # sorted
    for key in keys:
        val = parsed_config[key]
        # Filters are the last
        if key in ['preproc', 'postproc', 'postvoodoo']:
            continue
        # Flag beautifier
        if key in FLAGS or key in ACTIONS:
            val = onoff.get(val) or val
        # List beautifier
        if type(val) == type([]):
            if key == 'options':
                sep = ' '
            else:
                sep = ', '
            val = sep.join(val)
        print("%25s: %s" % (dotted_spaces("%-14s" % key), val))
    print()
    print(_('Active filters'))
    for filter_ in ['preproc', 'postproc', 'postvoodoo']:
        for rule in parsed_config.get(filter_) or []:
            print("%25s: %s  ->  %s" % (
                dotted_spaces("%-14s" % filter_), rule[0], rule[1]))


def get_file_body(file_):
    "Returns all the document BODY lines"
    return process_source_file(file_, noconf=1)[1][2]


def post_voodoo(lines, config):
    r'''
    %!postvoodoo handler - Beware! Voodoo here. For advanced users only.

    Your entire output document will be put in a single string, to your
    search/replace pleasure. Line breaks are single \n's in all platforms.
    You can change multiple lines at once, or even delete them. This is the
    last txt2tags processing in your file. All %!postproc's were already
    applied. It's the same as:

        $ txt2tags myfile.t2t | postvoodoo

    Your regex will be compiled with no modifiers. The default behavior is:

        ^ and $ match begin/end of entire string
        . doesn't match \n
        \w is not locale aware
        \w is not Unicode aware

    You can use (?...) in the beginning of your regex to change behavior:

        (?s)    the dot . will match \n, so .* will get everything
        (?m)    the ^ and $ match begin/end of EACH inner line
        (?u)    the \w, \d, \s and friends will be Unicode aware

    You can also use (?smu) or any combination of those.
    Learn more in http://docs.python.org/library/re.html
    '''

    loser1 = _('No, no. Your PostVoodoo regex is wrong. Maybe you should call mommy?')
    loser2 = _('Dear PostVoodoo apprentice: You got the regex right, but messed the replacement')

    subject = '\n'.join(lines)
    spells = compile_filters(config['postvoodoo'], loser1)

    for (magic, words) in spells:
        try:
            subject = magic.sub(words, subject)
        except:
            Error("%s: '%s'" % (loser2, words))

    return subject.split('\n')


def finish_him(outlist, config):
    "Writing output to screen or file"
    outfile = config['outfile']
    outlist = unmaskEscapeChar(outlist)
    outlist = expandLineBreaks(outlist)

    # Apply PostProc filters
    if config['postproc']:
        filters = compile_filters(config['postproc'],
            _('Invalid PostProc filter regex'))
        postoutlist = []
        errmsg = _('Invalid PostProc filter replacement')
        for line in outlist:
            for rgx, repl in filters:
                try:
                    line = rgx.sub(repl, line)
                except:
                    Error("%s: '%s'" % (errmsg, repl))
            postoutlist.append(line)
        outlist = postoutlist[:]

    if config['postvoodoo']:
        outlist = post_voodoo(outlist, config)

    if outfile == MODULEOUT:
        return outlist
    elif outfile == STDOUT:
        if GUI:
            return outlist, config
        else:
            for line in outlist:
                print(line)
    else:
        Savefile(outfile, addLineBreaks(outlist))
        if not GUI and not QUIET:
            print(_('%s wrote %s') % (my_name, outfile))

    if config['split']:
        if not QUIET:
            print("--- html...")
        sgml2html = 'sgml2html -s %s -l %s %s' % (
            config['split'], config['lang'] or lang, outfile)
        if not QUIET:
            print("Running system command:", sgml2html)
        os.system(sgml2html)


def toc_inside_body(body, toc, config):
    ret = []
    if AUTOTOC:
        return body                     # nothing to expand
    toc_mark = MaskMaster().tocmask
    # Expand toc mark with TOC contents
    flag, n = False, 0
    for i,line in enumerate(body):
        if line.count(toc_mark):            # toc mark found
            if config['toc']:
                if config['target'] == 'aat' and config['slides']:
                    j = i % (config['height'] - 1)
                    title = body[i - j + 2 + n]
                    ret.extend([''] * (config['height'] - j - 2 + n))
                    ret.extend([aa_line(AA['bar1'], config['width'])] + toc + aa_slide(title, AA['bar2'], config['width'], CONF['web']) + [''])
                    flag = True
                else:
                    ret.extend(toc)     # include if --toc
            else:
                pass                # or remove %%toc line
        else:
            if flag and config['target'] == 'aat' and config['slides'] and body[i] == body[i + 4] == aa_line(AA['bar2'], config['width']):
                end = [ret[-1]]
                del ret[-1]
                ret.extend([''] * (j - 6 - n) + end)
                flag, n = False, n + 1
                ret.append(line)            # common line
            else:
                ret.append(line)            # common line
    return ret


def toc_tagger(toc, config):
    "Returns the tagged TOC, as a single tag or a tagged list"
    ret = []
    # Convert the TOC list (t2t-marked) to the target's list format
    if config['toc-only'] or (config['toc'] and not TAGS['TOC']):
        fakeconf = config.copy()
        fakeconf['headers']    = 0
        fakeconf['toc-only']   = 0
        fakeconf['mask-email'] = 0
        fakeconf['preproc']    = []
        fakeconf['postproc']   = []
        fakeconf['postvoodoo'] = []
        fakeconf['css-sugar']  = 0
        fakeconf['fix-path']   = 0
        fakeconf['art-no-title']  = 1  # needed for --toc and --slides together, avoids slide title before TOC
        ret, foo = convert(toc, fakeconf)
        set_global_config(config)   # restore config
    # Our TOC list is not needed, the target already knows how to do a TOC
    elif config['toc'] and TAGS['TOC']:
        ret = [TAGS['TOC']]
    return ret


def toc_formatter(toc, config):
    "Formats TOC for automatic placement between headers and body"

    if config['toc-only']:
        return toc              # no formatting needed
    if not config['toc']:
        return []               # TOC disabled
    ret = toc

    # Art: An automatic "Table of Contents" header is added to the TOC slide
    if config['target'] == 'aat' and config['slides']:
        n = (config['height'] - 1) - (len(toc) + 6) % (config['height'] - 1)
        toc = aa_slide(config['toc-title'] or _("Table of Contents"), AA['bar2'], config['width'], CONF['web']) + toc + ([''] * n)
        toc.append(aa_line(AA['bar2'], config['width']))
        return toc
    if config['target'] == 'aat' and not config['slides']:
        ret = aa_box([config['toc-title'] or _("Table of Contents")], AA, config['width']) + toc

    # TOC open/close tags (if any)
    if TAGS['tocOpen']:
        ret.insert(0, TAGS['tocOpen'])
    if TAGS['tocClose']:
        ret.append(TAGS['tocClose'])

    # Autotoc specific formatting
    if AUTOTOC:
        if rules['autotocwithbars']:           # TOC between bars
            para = TAGS['paragraphOpen'] + TAGS['paragraphClose']
            bar  = regex['x'].sub('-' * DFT_TEXT_WIDTH, TAGS['bar1'])
            tocbar = [para, bar, para]
            if config['target'] == 'aat' and config['headers']:
                # exception: header already printed a bar
                ret = [para] + ret + tocbar
            else:
                ret = tocbar + ret + tocbar
        if rules['blankendautotoc']:           # blank line after TOC
            ret.append('')
        if rules['autotocnewpagebefore']:      # page break before TOC
            ret.insert(0, TAGS['pageBreak'])
        if rules['autotocnewpageafter']:       # page break after TOC
            ret.append(TAGS['pageBreak'])
    return ret


# XXX change function name. Now it's called at the end of the execution, dumping the full template.
def doHeader(headers, config):
    if not config['headers']:
        return config['fullBody']
    if not headers:
        headers = ['', '', '']
    target = config['target']
    if target not in HEADER_TEMPLATE:
        Error("doHeader: Unknown target '%s'" % target)

    # Use default templates
    if config['template'] == '' :
        if target in ('html', 'xhtml', 'xhtmls', 'html5') and config.get('css-sugar'):
            template = HEADER_TEMPLATE[target + 'css'].split('\n')
        else:
            template = HEADER_TEMPLATE[target].split('\n')

        template.append('%(BODY)s')

        if TAGS['EOD']:
            template.append(TAGS['EOD'].replace('%', '%%'))  # escape % chars

    # Read user's template file
    else:
        if PathMaster().is_url(config['template']):
            template = Readfile(config['template'], remove_linebreaks=1)
        else:
            templatefile = ''
            names = [config['template'] + '.' + target, config['template']]
            for filename in names:
                if os.path.isfile(filename):
                    templatefile = filename
                    break
            if not templatefile:
                Error(_("Cannot find template file:") + ' ' + config['template'])
            template = Readfile(templatefile, remove_linebreaks=1)

    head_data = {'STYLE': [], 'ENCODING': ''}

    # Fix CSS files path
    config['stylepath_out'] = fix_css_out_path(config)

    # Populate head_data with config info
    for key in list(head_data.keys()):
        val = config.get(key.lower())
        if key == 'STYLE' and 'html' in target:
            val = config.get('stylepath_out') or []
        # Remove .sty extension from each style filename (freaking tex)
        # XXX Can't handle --style foo.sty, bar.sty
        if target == 'tex' and key == 'STYLE':
            val = [re.sub('(?i)\.sty$', '', x) for x in val]
        if key == 'ENCODING':
            val = get_encoding_string(val, target)
        head_data[key] = val

    # Parse header contents
    for i in 0, 1, 2:
        # Expand macros
        contents = MacroMaster(config=config).expand(headers[i])
        # Escapes - on tex, just do it if any \tag{} present
        if target != 'tex' or \
          (target == 'tex' and re.search(r'\\\w+{', contents)):
            contents = doEscape(target, contents)
        if target == 'lout':
            contents = doFinalEscape(target, contents)

        head_data['HEADER%d' % (i + 1)] = contents

    # When using --css-inside, the template's <STYLE> line must be removed.
    # Template line removal for empty header keys is made some lines above.
    # That's why we will clean STYLE now.
    if target in ('html', 'xhtml', 'xhtmls', 'html5') and config.get('css-inside') and config.get('style'):
        head_data['STYLE'] = []

    Debug("Header Data: %s" % head_data, 1)

    # ASCII Art and rst don't use a header template, aa_header() formats the header
    if target == 'aat' and not (config['spread'] and not config['web']):
        n_h = len([v for v in head_data if v.startswith("HEADER") and head_data[v]])
        template = []
        if n_h:
            if config['slides']:
                x = config['height'] - 3 - (n_h * 3)
                n = x / (n_h + 1)
                end = x % (n_h + 1)
                template = aa_header(head_data, AA, config['width'], n, end, CONF['web'])
            else:
                template = [''] + aa_header(head_data, AA, config['width'], 2, 0, False)
        if config['slides']:
            total = len(config['fullBody']) / (config['height'] - 1) 
            l = aa_len_cjk(head_data['HEADER2']) + aa_len_cjk(head_data['HEADER3']) + 2
            bar2 = aa_line(AA['bar2'], config['width'])
            for i, line in enumerate(config['fullBody']):
                if i % (config['height'] -1 ) == 1 and config['fullBody'][i - 1] == config['fullBody'][i + 3] == bar2:
                    config['fullBody'][i] = (str(i / (config['height'] - 1) + 1) + '/' + str(total)).rjust(config['width'] - 1)
                if i % (config['height'] -1 ) == 3 and config['fullBody'][i - 3] == config['fullBody'][i + 1] == bar2:
                    if l < config['width']:
                        config['fullBody'][i] = ' ' + head_data['HEADER2'] + ' ' * (config['width'] - l) + head_data['HEADER3'] + ' '
        # Header done, let's get out
        if config['web']:
            encoding = ''
            if CONF['encoding'] and CONF['encoding'] != 'not_utf-8':
                encoding = '<meta charset=' + CONF['encoding'] + '>'
            if config['spread']:
                pre = '<pre style="text-align:center">'
            elif config['slides']:
                pre = ''
            else:
                pre = '<pre>'
            head_web = ['<!doctype html><html>' + encoding + '<title>' + config['header1'] + '</title>' + pre]
            foot_web = ['</pre></html>']
            if config['slides']:
                foot_web = ['</html>'] + Readfile('templates/dzslides-aapw.html', remove_linebreaks=1)
            if config['spread']:
                return head_web + config['fullBody'] + foot_web
            else:
                return head_web + template + config['fullBody'] + foot_web
        else:
            return template + config['fullBody']

    if target =='rst':
        template =[]
        if head_data['HEADER1']:
            template.extend(aa_under(head_data['HEADER1'], RST['title'], 10000, True))
        if head_data['HEADER2']:
            template.append(':Author: ' + head_data['HEADER2'])
        if head_data['HEADER3']:
            template.append(':Date: ' + head_data['HEADER3'])
        return template + config['fullBody']

    # Scan for empty dictionary keys
    # If found, scan template lines for that key reference
    # If found, remove the reference
    # If there isn't any other key reference on the same line, remove it
    #TODO loop by template line > key
    for key in list(head_data.keys()):
        if head_data.get(key):
            continue
        for line in template:
            if line.count('%%(%s)s' % key):
                sline = line.replace('%%(%s)s' % key, '')
                if not re.search(r'%\([A-Z0-9]+\)s', sline) and not rules['keepblankheaderline']:
                    template.remove(line)

    # Style is a multiple tag.
    # - If none or just one, use default template
    # - If two or more, insert extra lines in a loop (and remove original)
    styles = head_data['STYLE']
    if len(styles) == 1:
        head_data['STYLE'] = styles[0]
    elif len(styles) > 1:
        style_mark = '%(STYLE)s'
        for i in range(len(template)):
            if template[i].count(style_mark):
                while styles:
                    template.insert(i + 1, template[i].replace(style_mark, styles.pop()))
                del template[i]
                break

    # Expand macros on *all* lines of the template
    template = list(map(MacroMaster(config=config).expand, template))
    # Add Body contents to template data
    head_data['BODY'] = '\n'.join(config['fullBody'])
    # Populate template with data (dict expansion)
    template = '\n'.join(template) % head_data

    # Adding CSS contents into template (for --css-inside)
    # This code sux. Dirty++
    if target in ('html', 'xhtml', 'xhtmls', 'html5') and config.get('css-inside') and \
       config.get('stylepath'):
        set_global_config(config)  # usually on convert(), needed here
        for i in range(len(config['stylepath'])):
            cssfile = config['stylepath'][i]
            try:
                contents = Readfile(cssfile, remove_linebreaks=1)
                css = "\n%s\n%s\n%s\n%s\n" % (
                    doCommentLine("Included %s" % cssfile),
                    TAGS['cssOpen'],
                    '\n'.join(contents),
                    TAGS['cssClose'])
                # Style now is content, needs escaping (tex)
                #css = maskEscapeChar(css)
            except:
                Error(_("CSS include failed for %s") % cssfile)
            # Insert this CSS file contents on the template
            template = re.sub('(?i)(</HEAD>)', css + r'\1', template)
            # template = re.sub(r'(?i)(\\begin{document})',
            #       css + '\n' + r'\1', template)  # tex

        # The last blank line to keep everything separated
        template = re.sub('(?i)(</HEAD>)', '\n' + r'\1', template)

    return template.split('\n')


def doCommentLine(txt):
    # The -- string ends a (h|sg|xht)ml comment :(
    txt = maskEscapeChar(txt)
    if TAGS['comment'].count('--') and txt.count('--'):
        txt = re.sub('-(?=-)', r'-\\', txt)

    if TAGS['comment']:
        return regex['x'].sub(txt, TAGS['comment'])
    return ''


def doFooter(config):
    ret = []

    # No footer. The --no-headers option hides header AND footer
    if not config['headers']:
        return []

    # Only add blank line before footer if last block doesn't added by itself
    if not rules.get('blanksaround' + BLOCK.last):
        ret.append('')

    # Add txt2tags info at footer, if target supports comments
    if TAGS['comment']:

        # Not using TARGET_NAMES because it's i18n'ed.
        # It's best to always present this info in english.
        target = config['target']
        if config['target'] == 'tex':
            target = 'LaTeX2e'

        t2t_version = '%s code generated by %s %s (%s)' % (target, my_name, my_version, my_url)
        cmdline = 'cmdline: %s %s' % (my_name, ' '.join(config['realcmdline']))

        ret.append(doCommentLine(t2t_version))
        ret.append(doCommentLine(cmdline))

    # Maybe we have a specific tag to close the document?
    #if TAGS['EOD']:
    #   ret.append(TAGS['EOD'])

    return ret


#this converts proper \ue37f escapes to RTF \u-7297 escapes
def convertUnicodeRTF(match):
    num = int(match.group(1), 16)
    if num > 32767:
        num = num | -65536
    return ESCCHAR + 'u' + str(num) + '?'


def doEscape(target, txt):
    "Target-specific special escapes. Apply *before* insert any tag."
    tmpmask = 'vvvvThisEscapingSuxvvvv'

    if rules['escapexmlchars']:
        txt = re.sub('&', '&amp;', txt)
        txt = re.sub('<', '&lt;', txt)
        txt = re.sub('>', '&gt;', txt)

    if target == 'sgml':
            txt = re.sub('\xff', '&yuml;', txt)  # "+y
    elif target == 'pm6':
        txt = re.sub('<', '<\#60>', txt)
    elif target == 'mgp':
        txt = re.sub('^%', ' %', txt)  # add leading blank to avoid parse
    elif target == 'man':
        txt = re.sub("^([.'])", '\\&\\1', txt)              # command ID
        txt = txt.replace(ESCCHAR, ESCCHAR + 'e')           # \e
    elif target == 'lout':
        # TIP: / moved to FinalEscape to avoid //italic//
        # TIP: these are also converted by lout:  ...  ---  --
        txt = txt.replace(ESCCHAR, tmpmask)                 # \
        txt = txt.replace('"', '"%s""' % ESCCHAR)           # "\""
        txt = re.sub('([|&{}@#^~])', '"\\1"', txt)          # "@"
        txt = txt.replace(tmpmask, '"%s"' % (ESCCHAR * 2))  # "\\"
    elif target == 'tex':
        # Mark literal \ to be changed to $\backslash$ later
        txt = txt.replace(ESCCHAR, tmpmask)
        txt = re.sub('([#$&%{}])', ESCCHAR + r'\1'  , txt)  # \%
        txt = re.sub('([~^])'    , ESCCHAR + r'\1{}', txt)  # \~{}
        txt = re.sub('([<|>])'   ,           r'$\1$', txt)  # $>$
        txt = txt.replace(tmpmask, maskEscapeChar(r'$\backslash$'))
        # TIP the _ is escaped at the end
    elif target == 'rtf':
        txt = txt.replace(ESCCHAR, ESCCHAR + ESCCHAR)
        txt = re.sub('([{}])', ESCCHAR + r'\1', txt)
        # RTF is ascii only
        # If an encoding is declared, try to convert to RTF unicode
        enc = get_encoding_string(CONF['encoding'], 'rtf')
        if enc:
            try:
                txt = txt.decode(enc)
            except:
                Error('Problem decoding line "' % txt + '"')
            txt = txt.encode('cp1252', 'backslashreplace')
            # escape ANSI codes above ascii range
            for code in range(128, 255):
                txt = re.sub('%c' % code, ESCCHAR + "'" + hex(code)[2:], txt)
            # some code were preescaped by txt.encode
            txt = re.sub(r'\\x([0-9a-f]{2})', r"\\\'\1", txt)
            #finally, convert escaped unicode chars to RTF format
            txt = re.sub(r'\\u([0-9a-f]{4})', convertUnicodeRTF, txt)
    return txt


# TODO man: where - really needs to be escaped?
def doFinalEscape(target, txt):
    "Last escapes of each line"
    if   target == 'pm6' :
        txt = txt.replace(ESCCHAR + '<', r'<\#92><')
    elif target == 'man' :
        txt = txt.replace('-', r'\-')
    elif target == 'sgml':
        txt = txt.replace('[', '&lsqb;')
    elif target == 'lout':
        txt = txt.replace('/', '"/"')
    elif target == 'tex' :
        txt = txt.replace('_', r'\_')
        txt = txt.replace('vvvvTexUndervvvv', '_')  # shame!
    elif target == 'rtf':
        txt = txt.replace('\t', ESCCHAR + 'tab')
    return txt


def EscapeCharHandler(action, data):
    "Mask/Unmask the Escape Char on the given string"
    if not data.strip():
        return data
    if action not in ('mask', 'unmask'):
        Error("EscapeCharHandler: Invalid action '%s'" % action)
    if action == 'mask':
        return data.replace('\\', ESCCHAR)
    else:
        return data.replace(ESCCHAR, '\\')


def maskEscapeChar(data):
    "Replace any Escape Char \ with a text mask (Input: str or list)"
    if type(data) == type([]):
        return [EscapeCharHandler('mask', x) for x in data]
    return EscapeCharHandler('mask', data)


def unmaskEscapeChar(data):
    "Undo the Escape char \ masking (Input: str or list)"
    if type(data) == type([]):
        return [EscapeCharHandler('unmask', x) for x in data]
    return EscapeCharHandler('unmask', data)


def addLineBreaks(mylist):
    "use LB to respect sys.platform"
    ret = []
    for line in mylist:
        line = line.replace('\n', LB)       # embedded \n's
        ret.append(line + LB)               # add final line break
    return ret


# Convert ['foo\nbar'] to ['foo', 'bar']
def expandLineBreaks(mylist):
    ret = []
    for line in mylist:
        ret.extend(line.split('\n'))
    return ret


def compile_filters(filters, errmsg='Filter'):
    if filters:
        for i in range(len(filters)):
            patt, repl = filters[i]
            try:
                rgx = re.compile(patt)
            except:
                Error("%s: '%s'" % (errmsg, patt))
            filters[i] = (rgx, repl)
    return filters


def enclose_me(tagname, txt):
    return TAGS.get(tagname + 'Open') + txt + TAGS.get(tagname + 'Close')


def fix_relative_path(path):
    """
    Fix image/link path to be relative to the source file path (issues 62, 63)

    Leave the path untouched when:
    - not using --fix-path
    - path is an URL (or email)
    - path is an #anchor
    - path is absolute
    - infile is STDIN
    - outfile is STDOUT

    Note: Keep this rules in sync with fix_css_out_path()
    """
    if not CONF['fix-path'] \
        or regex['link'].match(path) \
        or path[0] == '#' \
        or os.path.isabs(path) \
        or CONF['sourcefile'] in [STDIN, MODULEIN] \
        or CONF['outfile'] in [STDOUT, MODULEOUT]:
        return path

    # Make sure the input path is relative to the correct source file.
    # The path may be different from original source file when using %!include
    inputpath = PathMaster().join(os.path.dirname(CONF['currentsourcefile']), path)

    # Now adjust the inputpath to be reachable from the output folder
    return PathMaster().relpath(inputpath, os.path.dirname(CONF['outfile']))


def fix_css_out_path(config):
    """
    Fix CSS files path to be reached from the output folder (issue 71)

    Needed when the output file is in a different folder than the sources.
    This will affect the HTML's <link rel="stylesheet"> header tag.

    Leave the path untouched when:
    - not using --fix-path
    - path is an URL
    - path is absolute
    - infile is STDIN
    - outfile is STDOUT

    Note: Keep this rules in sync with fix_relative_path()
    """

    # No CSS files
    if not config.get('style'):
        return None

    # Defaults to user-typed paths
    default = config['style'][:]

    if not config['fix-path'] \
        or config['sourcefile'] in [STDIN, MODULEIN] \
        or config['outfile'] in [STDOUT, MODULEOUT]:
        return default

    # Sanity
    if len(config['style']) != len(config['stylepath']):
        Error("stylepath corrupted. Sorry, this shouldn't happen :(")

    # The stylepath paths are relative to the INPUT file folder.
    # Now we must make them relative to the OUTPUT file folder.
    stylepath_out = []
    for (userpath, fixedpath) in zip(config['style'], config['stylepath']):
        if os.path.isabs(userpath):
            # Never fix user-typed absolute paths
            path = userpath
        else:
            path = PathMaster().relpath(fixedpath, os.path.dirname(config['outfile']))
        stylepath_out.append(path)
    return stylepath_out


def beautify_me(name, line):
    "where name is: bold, italic, underline or strike"

    # Exception: Doesn't parse an horizontal bar as strike
    if name == 'strike' and regex['bar'].search(line):
        return line

    name  = 'font%s' % name.capitalize()
    open_ = TAGS['%sOpen' % name]
    close = TAGS['%sClose' % name]
    txt = r'%s\1%s' % (open_, close)
    line = regex[name].sub(txt, line)
    return line


def get_tagged_link(label, url):
    ret = ''
    target = CONF['target']
    image_re = regex['img']

    # Set link type
    if regex['email'].match(url):
        linktype = 'email'
    else:
        linktype = 'url'

    # Escape specials from TEXT parts
    label = doEscape(target, label)

    # Escape specials from link URL
    if not rules['linkable'] or rules['escapeurl']:
        url = doEscape(target, url)

    # Adding protocol to guessed link
    guessurl = ''
    if linktype == 'url' and \
       re.match('(?i)' + regex['_urlskel']['guess'], url):
        if url[0] in 'Ww':
            guessurl = 'http://' + url
        else:
            guessurl = 'ftp://' + url

        # Not link aware targets -> protocol is useless
        if not rules['linkable']:
            guessurl = ''

    # Simple link (not guessed)
    if not label and not guessurl:
        if CONF['mask-email'] and linktype == 'email':
            # Do the email mask feature (no TAGs, just text)
            url = url.replace('@', ' (a) ')
            url = url.replace('.', ' ')
            url = "<%s>" % url
            if rules['linkable']:
                url = doEscape(target, url)
            ret = url
        else:
            # Just add link data to tag
            tag = TAGS[linktype]
            ret = regex['x'].sub(url, tag)

    # Named link or guessed simple link
    else:
        # Adjusts for guessed link
        if not label:
            label = url         # no protocol
        if guessurl:
            url = guessurl      # with protocol

        # Image inside link!
        if image_re.match(label):
            if rules['imglinkable']:  # get image tag
                label = parse_images(label)
            else:                     # img@link !supported
                img_path = image_re.match(label).group(1)
                label = "(%s)" % fix_relative_path(img_path)

        if TARGET == 'aat' and not CONF['slides'] and not CONF['web'] and not CONF['spread'] and not CONF['toc-only']:
            for macro in MASK.macrobank:
                macro = MASK.macroman.expand(macro)
                url = url.replace(MASK.macromask, macro, 1)
            if url not in AA_MARKS:
                AA_MARKS.append(url)
            url = str(AA_MARKS.index(url) + 1)

        # Putting data on the right appearance order
        if rules['labelbeforelink'] or not rules['linkable']:
            urlorder = [label, url]   # label before link
        else:
            urlorder = [url, label]   # link before label

        ret = TAGS["%sMark" % linktype]

        # Exception: tag for anchor link is different from the link tag
        if url.startswith('#') and TAGS['urlMarkAnchor']:
            ret = TAGS['urlMarkAnchor']

        # Add link data to tag (replace \a's)
        for data in urlorder:
            ret = regex['x'].sub(data, ret, 1)

        if TARGET == 'rst' and '.. image::' in label:
            ret = label[:-2] + TAGS['urlImg'] + url + label[-2:]

    return ret


def parse_deflist_term(line):
    "Extract and parse definition list term contents"
    img_re = regex['img']
    term   = regex['deflist'].search(line).group(3)

    # Mask image inside term as (image.jpg), where not supported
    if not rules['imgasdefterm'] and img_re.search(term):
        while img_re.search(term):
            imgfile = img_re.search(term).group(1)
            term = img_re.sub('(%s)' % imgfile, term, 1)

    #TODO tex: escape ] on term. \], \rbrack{} and \verb!]! don't work :(
    return term


def get_image_align(line):
    "Return the image (first found) align for the given line"

    # First clear marks that can mess align detection
    line = re.sub(SEPARATOR + '$', '', line)  # remove deflist sep
    line = re.sub('^' + SEPARATOR, '', line)  # remove list sep
    line = re.sub('^[\t]+'       , '', line)  # remove quote mark

    # Get image position on the line
    m = regex['img'].search(line)
    ini = m.start()
    head = 0
    end = m.end()
    tail = len(line)

    # The align detection algorithm
    if   ini == head and end != tail:
        align = 'left'      # ^img + text$
    elif ini != head and end == tail:
        align = 'right'     # ^text + img$
    else:
        align = 'center'    # default align

    # Some special cases
    if BLOCK.isblock('table'):
        align = 'center'    # ignore when table
#   if TARGET == 'mgp' and align == 'center': align = 'center'

    return align


# Reference: http://www.iana.org/assignments/character-sets
# http://www.drclue.net/F1.cgi/HTML/META/META.html
def get_encoding_string(enc, target):
    if not enc:
        return ''
    # Target specific translation table
    translate = {
        'tex': {
            # missing: ansinew , applemac , cp437 , cp437de , cp865
            'utf-8'       : 'utf8',
            'us-ascii'    : 'ascii',
            'windows-1250': 'cp1250',
            'windows-1252': 'cp1252',
            'ibm850'      : 'cp850',
            'ibm852'      : 'cp852',
            'iso-8859-1'  : 'latin1',
            'iso-8859-2'  : 'latin2',
            'iso-8859-3'  : 'latin3',
            'iso-8859-4'  : 'latin4',
            'iso-8859-5'  : 'latin5',
            'iso-8859-9'  : 'latin9',
            'koi8-r'      : 'koi8-r'
        },
        'rtf': {
            'utf-8'       : 'utf8',
        }
    }
    # Normalization
    enc = re.sub('(?i)(us[-_]?)?ascii|us|ibm367', 'us-ascii'  , enc)
    enc = re.sub('(?i)(ibm|cp)?85([02])'        , 'ibm85\\2'  , enc)
    enc = re.sub('(?i)(iso[_-]?)?8859[_-]?'     , 'iso-8859-' , enc)
    enc = re.sub('iso-8859-($|[^1-9]).*'        , 'iso-8859-1', enc)
    # Apply translation table
    try:
        enc = translate[target][enc.lower()]
    except:
        pass
    return enc


##############################################################################
##MerryChristmas,IdontwanttofighttonightwithyouImissyourbodyandIneedyourlove##
##############################################################################


def process_source_file(file_='', noconf=0, contents=[]):
    """
    Find and Join all the configuration available for a source file.
    No sanity checking is done on this step.
    It also extracts the source document parts into separate holders.

    The config scan order is:
        1. The user configuration file (i.e. $HOME/.txt2tagsrc)
        2. The source document's CONF area
        3. The command line options

    The return data is a tuple of two items:
        1. The parsed config dictionary
        2. The document's parts, as a (head, conf, body) tuple

    All the conversion process will be based on the data and
    configuration returned by this function.
    The source files is read on this step only.
    """
    if contents:
        source = SourceDocument(contents=contents)
    else:
        source = SourceDocument(file_)
    head, conf, body = source.split()
    Message(_("Source document contents stored"), 2)
    if not noconf:
        # Read document config
        source_raw = source.get_raw_config()
        # Join all the config directives found, then parse it
        full_raw = RC_RAW + source_raw + CMDLINE_RAW
        Message(_("Parsing and saving all config found (%03d items)") % (len(full_raw)), 1)
        full_parsed = ConfigMaster(full_raw).parse()
        # Add manually the filename to the conf dic
        if contents:
            full_parsed['sourcefile'] = MODULEIN
            full_parsed['currentsourcefile'] = MODULEIN
            full_parsed['infile'] = MODULEIN
            full_parsed['outfile'] = MODULEOUT
        else:
            full_parsed['sourcefile'] = file_
            full_parsed['currentsourcefile'] = file_
        # Maybe should we dump the config found?
        if full_parsed.get('dump-config'):
            dumpConfig(source_raw, full_parsed)
            Quit()
        # The user just want to know a single config value (hidden feature)
        #TODO pick a better name than --show-config-value
        elif full_parsed.get('show-config-value'):
            config_value = full_parsed.get(full_parsed['show-config-value'])
            if config_value:
                if type(config_value) == type([]):
                    print('\n'.join(config_value))
                else:
                    print(config_value)
            Quit()
        # Okay, all done
        Debug("FULL config for this file: %s" % full_parsed, 1)
    else:
        full_parsed = {}
    return full_parsed, (head, conf, body)


def get_infiles_config(infiles):
    """
    Find and Join into a single list, all configuration available
    for each input file. This function is supposed to be the very
    first one to be called, before any processing.
    """
    return list(map(process_source_file, infiles))


def convert_this_files(configs):
    global CONF
    for myconf, doc in configs:                 # multifile support
        target_head = []
        target_toc  = []
        target_body = []
        target_foot = []
        source_head, source_conf, source_body = doc
        myconf = ConfigMaster().sanity(myconf)
        
        if myconf['target'] in ['aat', 'txt', 'rst', 'mgp'] and myconf['encoding'].lower() == 'utf-8':
            decode_head, decode_body = [], []
            try:
                for line in source_head:
                    decode_head.append(line.decode('utf-8'))
                for line in source_body:
                    decode_body.append(line.decode('utf-8'))
                source_head, source_body = decode_head, decode_body
            except:
                myconf['encoding'] = 'not_utf-8'
                myconf = ConfigMaster().sanity(myconf)

        # Save header info for %%header1..3 macros
        if not source_head:
            myconf['header1'] = ''
            myconf['header2'] = ''
            myconf['header3'] = ''
        else:
            myconf['header1'] = source_head[0]
            myconf['header2'] = source_head[1]
            myconf['header3'] = source_head[2]

        # Parse the full marked body into tagged target
        first_body_line = (len(source_head) or 1) + len(source_conf) + 1
        Message(_("Composing target Body"), 1)
        target_body, marked_toc = convert(source_body, myconf, firstlinenr=first_body_line)

        # If dump-source, we're done
        if myconf['dump-source']:
            for line in source_head + source_conf + target_body:
                print(line)
            return

        # Close the last slide
        if myconf['slides'] and not myconf['toc-only'] and myconf['target'] == 'aat':
            n = (myconf['height'] - 1) - (AA_COUNT % (myconf['height'] - 1) + 1)
            if myconf['web']:
                target_body = target_body + ([''] * n) + [aa_line(AA['bar2'], myconf['width']) + '</pre></section>']
            else:
                target_body = target_body + ([''] * n) + [aa_line(AA['bar2'], myconf['width'])]
            if myconf['qa']:
                n_before = (myconf['height'] - 24) / 2
                n_after = myconf['height'] - 24 - n_before
                head = aa_slide(_("Q&A"), AA['bar2'], myconf['width'], myconf['web'])
                if myconf['height'] > 23 and myconf['width'] > 22:
                    target_body = target_body + head + [''] * n_before + [(myconf['width'] - 23) / 2 * ' ' + line for line in AA_QA] + [''] * n_after + [aa_line(AA['bar2'], myconf['width'])]
                else:
                    target_body = target_body + head + [''] * (myconf['height'] - 7) + [aa_line(AA['bar2'], myconf['width'])]

        if myconf['target'] and not myconf['slides'] and not myconf['web'] and not myconf['spread'] and not myconf['toc-only']:
            for i, url in enumerate(AA_MARKS):
                target_body.extend(textwrap.wrap('[' + str(i + 1) + '] ' + url, myconf['width']))

        # Compose the target file Footer
        Message(_("Composing target Footer"), 1)
        target_foot = doFooter(myconf)

        # Make TOC (if needed)
        Message(_("Composing target TOC"), 1)
        tagged_toc  = toc_tagger(marked_toc, myconf)
        target_toc  = toc_formatter(tagged_toc, myconf)
        target_body = toc_inside_body(target_body, target_toc, myconf)
        if not AUTOTOC and not myconf['toc-only']:
            target_toc = []
        # Finally, we have our document
        myconf['fullBody'] = target_toc + target_body + target_foot

        # Compose the target file Headers
        #TODO escape line before?
        #TODO see exceptions by tex and mgp
        Message(_("Composing target Headers"), 1)
        outlist = doHeader(source_head, myconf)

        if myconf['target'] == 'aat' and myconf['web'] and not myconf['headers']:
            outlist = ['<pre>'] + outlist + ['</pre>']

        # If on GUI, abort before finish_him
        # If module, return finish_him as list
        # Else, write results to file or STDOUT
        if GUI:
            return outlist, myconf
        elif myconf.get('outfile') == MODULEOUT:
            return finish_him(outlist, myconf), myconf
        else:
            Message(_("Saving results to the output file"), 1)
            finish_him(outlist, myconf)


def getImageInfo(filename):
    "Get image type, dimensions, and pixel size."
    try:
        f = open(filename, 'rb')
        head = f.read(2)
        # Default DPI (if none specified in image metadata) of 72
        dpix = 72
        dpiy = 72
        if head == '\x89\x50':  # PNG format image
            imgtype = 'png'
            magic, length, chunkid, width, height, bit_depth, colour_type = struct.unpack('!6sI4sIIBBxxxxxxx', f.read(31))
            if (magic == '\x4e\x47\x0d\x0a\x1a\x0a') and \
                    (length > 0) and \
                    (chunkid == 'IHDR'):
                        chunk = f.read(8)
                        # Now to find the DPI / Pixel dimensions
                        while chunk:
                            length, chunkid = struct.unpack('!I4s', chunk)
                            if chunkid == 'pHYs':
                                dpix, dpiy, units = struct.unpack('!IIbxxxx', f.read(13))
                                if units == 1:
                                    # PNG images have pixel dimensions in pixels per meter,
                                    # convert to pixels per inch
                                    dpix = dpix * 0.0257
                                    dpiy = dpiy * 0.0257
                                else:
                                    # No pixel dimensions, set back to default
                                    dpix = 72
                                    dpiy = 72
                            elif chunkid == 'IDAT':
                                data = f.read(length)
                                f.seek(4, 1)
                            else:
                                f.seek(length + 4, 1)
                            chunk = f.read(8)
                        f.close()
                        return imgtype, width, height, bit_depth, colour_type, dpix, dpiy, data
            else:
                f.close()
                Error('Cannot embed PNG image ' + filename + '. Badly formatted.')

        elif head == '\xff\xd8':  # JPG format image
            imgtype = 'jpeg'
            # Jpeg format is insane. The image size chunk could be anywhere,
            # so we need to search the whole file.
            b = f.read(1)
            while (b != ''):
                # Each chunk in a jpeg file is delimited by at least one
                # \xff character, and possibly more for padding. Seek past 'em
                while (b != '\xff'):
                    b = f.read(1)
                while (b == '\xff'):
                    b = f.read(1)

                # Past them, now to find the type of this particular chunk
                if b == '\xe0':
                    # Header, should be the first chunk in the file.
                    size = struct.unpack('!H', f.read(2))
                    if f.read(5) == 'JFIF\0':
                        # This Jpeg has JFIF metadata, which should include pixel dimensions
                        units, dpix, dpiy = struct.unpack('!xxbHH', f.read(7))
                        if units == 0:
                            # No exact pixel dimensions, just return defaults
                            dpix = 72
                            dpiy = 72
                        elif units == 2:
                            # Pixel dimensions in pixels per centimeter, so convert.
                            #  units == 1 would mean the field is in pixels per inch,
                            #  so no conversion needed in that case.
                            dpix = dpix * 2.57
                            dpiy = dpiy * 2.57
                        f.seek(size[0] - 12, 1)
                    else:
                        # No metadata, just keep the default 72 dpi and
                        # find the image size.
                        f.seek(size[0] - 7, 1)
                    b = f.read(1)
                elif (b >= '\xc0') and (b <= '\xc3'):
                    # Image info chunk, which should include size in pixels
                    height, width = struct.unpack('!xxxHH', f.read(7))
                    f.close()
                    return imgtype, width, height, 'bit_depth', 'colour_type', dpix, dpiy, 'data'

                else:
                    # Wrong chunk type. Get length of chunk and skip to the next one
                    size = struct.unpack('!H', f.read(2))
                    f.seek(size[0] - 2, 1)
                    b = f.read(1)
            f.close()
            # No size information found
            Error('Cannot embed JPG image ' + filename + '. Badly formatted.')
        else:  # Not a supported image format
            f.close()
            Error('Cannot embed image ' + filename + '. Unsupported format.')
    except:
        Error('Cannot embed image ' + filename + '. Unable to open file.')

RTFIMGID = 1000  # Needed so each embedded image can have a unique ID number


def embedImage(filename):
    mytype, width, height, bit_depth, colour_type, dpix, dpiy, data = getImageInfo(filename)
    if TARGET in ('html','xhtml','xhtmls','html5'):

        ## return a data uri with the image embed.
        ## see: http://en.wikipedia.org/wiki/Data_URI_scheme
        import base64
        line = "data: image/%s;base64,"%mytype
        line = line+base64.b64encode(file(filename).read())
        return line
        
    elif TARGET == 'rtf':
        global RTFIMGID
        RTFIMGID += 1
        # Defalt DPI of images.
        if dpix == 0 and dpiy == 0:
            dpix = 72
            dpiy = 72
        try:
            filein = open(filename, 'rb')
            # RTF tags for an embedded bitmap image, with size in pixels and intended display size in twips.
            # Size and dpi converted to float for division, as by default Python 2 will return an integer,
            # probably truncated to 0 in most cases. This behavior is changed in Python3.
            line = r'\\%sblip\\picw%d\\pich%d\\picwgoal%d\\picscalex100\\pichgoal%d\\picscaley100\\bliptag%d{\\*\\blipuid%016x}' \
                    % (mytype, width, height, int(float(width) / float(dpix) * 1440.0), int(float(height) / float(dpiy) * 1440.0), RTFIMGID, RTFIMGID)
            line = line + filein.read().encode('hex')
            filein.close()
            return line
        except:
            Error('Unable to embed image: ' + filename)

    elif TARGET == 'aat':
        if mytype not in ['png']:
            Error("Cannot embed image " + filename + ". Unsupported " + mytype + " format with Ascii Art targets. You should use PNG.")
        if colour_type == 3:
            Error("Cannot embed image " + filename + ". Unsupported indexed-colour image type with Ascii Art targets. You should use greyscale or RGB.")
        if bit_depth not in [8]:
            Error("Cannot embed image " + filename + ". Unsupported bit depth with Ascii Art targets. You should use 8-bit pixels.")
        import zlib
        decomp = zlib.decompress(data)
        n_byte = n_byte_alpha = (colour_type % 4 + 1)
        if colour_type in [4, 6]:
            n_byte_alpha = n_byte + 1
        image = []
        end_line = n_byte_alpha * width + 1
        while decomp:
            line = decomp[1:end_line]
            line_img = []
            while line:
                if n_byte == 1:
                    L, = struct.unpack('!B', line[:n_byte])
                else:
                    R, G, B = struct.unpack('!BBB', line[:n_byte])
                    # ITU-R 601-2 luma transform
                    L = int(0.299 * R + 0.587 * G + 0.114 * B)
                line_img.append(L)
                line = line[n_byte_alpha:]
            image.append(line_img)
            decomp = decomp[end_line:]
        return aa_image(image)


def parse_images(line):
    "Tag all images found"
    global CONF
    while regex['img'].search(line):
        txt = regex['img'].search(line).group(1)
        tag = TAGS['img']

        txt = fix_relative_path(txt)

        # If target supports image alignment, here we go
        if rules['imgalignable']:

            align = get_image_align(line)         # right
            align_name = align.capitalize()       # Right

            # The align is a full tag, or part of the image tag (~A~)
            if TAGS['imgAlign' + align_name]:
                tag = TAGS['imgAlign' + align_name]
            else:
                align_tag = TAGS['_imgAlign' + align_name]
                tag = regex['_imgAlign'].sub(align_tag, tag, 1)

            # Dirty fix to allow centered solo images
            if align == 'center' and TARGET in ('html', 'xhtml'):
                rest = regex['img'].sub('', line, 1)
                if re.match('^\s+$', rest):
                    tag = "<center>%s</center>" % tag
            if align == 'center' and TARGET == 'xhtmls':
                rest = regex['img'].sub('', line, 1)
                if re.match('^\s+$', rest):
                    ## original (not validating):
                    # tag = '<div style="text-align: center;">%s</div>' % tag
                    ## dirty fix:
                    # tag = '</p><div style="text-align: center;">%s</div><p>' % tag
                    ## will validate, though img won't be centered:
                    tag = '%s' % tag

        # Rtf needs some tweaking
        if TARGET == 'rtf' and not CONF.get('embed-images'):
            # insert './' for relative paths if needed
            if not re.match(r':/|:\\', txt):
                tag = regex['x'].sub('./\a', tag, 1)
            # insert image filename an extra time for readers that don't grok linked images
            tag = regex['x'].sub(txt, tag, 1)

        if TARGET == 'tex':
            tag = re.sub(r'\\b', r'\\\\b', tag)
            txt = txt.replace('_', 'vvvvTexUndervvvv')

        if CONF.get('embed-images'):
            # Embedded images find files from the same location as linked images,
            # for consistant behaviour.
            basedir = os.path.dirname(CONF.get('outfile'))
            fullpath = PathMaster().join(basedir, txt)
            txt = embedImage(fullpath)
            if TARGET == 'aat':
                return txt

        # Ugly hack to avoid infinite loop when target's image tag contains []
        tag = tag.replace('[', 'vvvvEscapeSquareBracketvvvv')

        line = regex['img'].sub(tag, line, 1)
        line = regex['x'].sub(txt, line, 1)

        if TARGET == 'rst':
            line = line.split('ENDIMG')[0] + line.split('ENDIMG')[1].strip()

    return line.replace('vvvvEscapeSquareBracketvvvv', '[')


def add_inline_tags(line):
    # Beautifiers
    for beauti in ('bold', 'italic', 'underline', 'strike'):
        if regex['font%s' % beauti.capitalize()].search(line):
            line = beautify_me(beauti, line)

    line = parse_images(line)
    return line


def get_include_contents(file_, path=''):
    "Parses %!include: value and extract file contents"
    ids = {'`': 'verb', '"': 'raw', "'": 'tagged'}
    id_ = 't2t'
    # Set include type and remove identifier marks
    mark = file_[0]
    if mark in ids:
        if file_[:2] == file_[-2:] == mark * 2:
            id_ = ids[mark]      # set type
            file_ = file_[2:-2]  # remove marks
    # Handle remote dir execution
    filepath = PathMaster().join(path, file_)
    # Read included file contents
    lines = Readfile(filepath, remove_linebreaks=1)
    # Default txt2tags marked text, just BODY matters
    if id_ == 't2t':
        lines = get_file_body(filepath)
        lines.insert(0, '%%!currentfile: %s' % (filepath))
        # This appears when included hit EOF with verbatim area open
        #lines.append('%%INCLUDED(%s) ends here: %s' % (id_, file_))
    return id_, lines


def set_global_config(config):
    global CONF, TAGS, regex, rules, TARGET
    CONF   = config
    rules  = getRules(CONF)
    TAGS   = getTags(CONF)
    regex  = getRegexes()
    TARGET = config['target']  # save for buggy functions that need global


def convert(bodylines, config, firstlinenr=1):
    global BLOCK, TITLE, MASK

    set_global_config(config)

    target = config['target']
    BLOCK = BlockMaster()
    MASK  =  MaskMaster()
    TITLE = TitleMaster()

    ret = []
    dump_source = []
    f_lastwasblank = 0

    # Compiling all PreProc regexes
    pre_filter = compile_filters(
        CONF['preproc'], _('Invalid PreProc filter regex'))

    # Let's mark it up!
    linenr = firstlinenr - 1
    lineref = 0
    while lineref < len(bodylines):
        # Defaults
        MASK.reset()
        results_box = ''

        untouchedline = bodylines[lineref]
        dump_source.append(untouchedline)

        line = re.sub('[\n\r]+$', '', untouchedline)   # del line break

        # Apply PreProc filters
        if pre_filter:
            errmsg = _('Invalid PreProc filter replacement')
            for rgx, repl in pre_filter:
                try:
                    line = rgx.sub(repl, line)
                except:
                    Error("%s: '%s'" % (errmsg, repl))

        line = maskEscapeChar(line)                  # protect \ char
        linenr  += 1
        lineref += 1

        Debug(repr(line), 2, linenr)  # heavy debug: show each line

        #------------------[ Comment Block ]------------------------

        # We're already on a comment block
        if BLOCK.block() == 'comment':

            # Closing comment
            if regex['blockCommentClose'].search(line):
                ret.extend(BLOCK.blockout() or [])
                continue

            # Normal comment-inside line. Ignore it.
            continue

        # Detecting comment block init
        if regex['blockCommentOpen'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('comment'))
            continue

        #-------------------------[ Tagged Text ]----------------------

        # We're already on a tagged block
        if BLOCK.block() == 'tagged':

            # Closing tagged
            if regex['blockTaggedClose'].search(line):
                ret.extend(BLOCK.blockout())
                continue

            # Normal tagged-inside line
            BLOCK.holdadd(line)
            continue

        # Detecting tagged block init
        if regex['blockTaggedOpen'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('tagged'))
            continue

        # One line tagged text
        if regex['1lineTagged'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('tagged'))
            line = regex['1lineTagged'].sub('', line)
            BLOCK.holdadd(line)
            ret.extend(BLOCK.blockout())
            continue

        #-------------------------[ Raw Text ]----------------------

        # We're already on a raw block
        if BLOCK.block() == 'raw':

            # Closing raw
            if regex['blockRawClose'].search(line):
                ret.extend(BLOCK.blockout())
                continue

            # Normal raw-inside line
            BLOCK.holdadd(line)
            continue

        # Detecting raw block init
        if regex['blockRawOpen'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('raw'))
            continue

        # One line raw text
        if regex['1lineRaw'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('raw'))
            line = regex['1lineRaw'].sub('', line)
            BLOCK.holdadd(line)
            ret.extend(BLOCK.blockout())
            continue

        #------------------------[ Verbatim  ]----------------------

        #TIP We'll never support beautifiers inside verbatim

        # Closing table mapped to verb
        if BLOCK.block() == 'verb' \
           and BLOCK.prop('mapped') == 'table' \
           and not regex['table'].search(line):
            ret.extend(BLOCK.blockout())

        # We're already on a verb block
        if BLOCK.block() == 'verb':

            # Closing verb
            if regex['blockVerbClose'].search(line):
                ret.extend(BLOCK.blockout())
                continue

            # Normal verb-inside line
            BLOCK.holdadd(line)
            continue

        # Detecting verb block init
        if regex['blockVerbOpen'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('verb'))
            f_lastwasblank = 0
            continue

        # One line verb-formatted text
        if regex['1lineVerb'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('verb'))
            line = regex['1lineVerb'].sub('', line)
            BLOCK.holdadd(line)
            ret.extend(BLOCK.blockout())
            f_lastwasblank = 0
            continue

        # Tables are mapped to verb when target is not table-aware
        if not rules['tableable'] and regex['table'].search(line):
            if not BLOCK.isblock('verb'):
                ret.extend(BLOCK.blockin('verb'))
                BLOCK.propset('mapped', 'table')
                BLOCK.holdadd(line)
                continue

        #---------------------[ blank lines ]-----------------------

        if regex['blankline'].search(line):

            # Close open paragraph
            if BLOCK.isblock('para'):
                ret.extend(BLOCK.blockout())
                f_lastwasblank = 1
                continue

            # Close all open tables
            if BLOCK.isblock('table'):
                ret.extend(BLOCK.blockout())
                f_lastwasblank = 1
                continue

            # Close all open quotes
            while BLOCK.isblock('quote'):
                ret.extend(BLOCK.blockout())

            # Closing all open lists
            if f_lastwasblank:          # 2nd consecutive blank
                if BLOCK.block().endswith('list'):
                    BLOCK.holdaddsub('')   # helps parser
                while BLOCK.depth:  # closes list (if any)
                    ret.extend(BLOCK.blockout())
                continue            # ignore consecutive blanks

            # Paragraph (if any) is wanted inside lists also
            if BLOCK.block().endswith('list'):
                BLOCK.holdaddsub('')

            f_lastwasblank = 1
            continue

        #---------------------[ special ]---------------------------

        if regex['special'].search(line):

            targ, key, val = ConfigLines().parse_line(line, None, target)

            if key:
                Debug("Found config '%s', value '%s'" % (key, val), 1, linenr)
            else:
                Debug('Bogus Special Line', 1, linenr)

            # %!include command
            if key == 'include':

                # The current path is always relative to the file where %!include appeared
                incfile = val
                incpath = os.path.dirname(CONF['currentsourcefile'])
                fullpath = PathMaster().join(incpath, incfile)

                # Infinite loop detection
                if os.path.abspath(fullpath) == os.path.abspath(CONF['currentsourcefile']):
                    Error("%s: %s" % (_('A file cannot include itself (loop!)'), fullpath))

                inctype, inclines = get_include_contents(incfile, incpath)

                # Verb, raw and tagged are easy
                if inctype != 't2t':
                    ret.extend(BLOCK.blockin(inctype))
                    BLOCK.holdextend(inclines)
                    ret.extend(BLOCK.blockout())
                else:
                    # Insert include lines into body
                    #TODO include maxdepth limit
                    bodylines = bodylines[:lineref] + inclines + ['%%!currentfile: %s' % (CONF['currentsourcefile'])] + bodylines[lineref:]
                    # Remove %!include call
                    if CONF['dump-source']:
                        dump_source.pop()

            # %!currentfile command
            elif key == 'currentfile':
                targ, key, val = ConfigLines().parse_line(line, 'currentfile', target)
                if key:
                    Debug("Found config '%s', value '%s'" % (key, val), 1, linenr)
                    CONF['currentsourcefile'] = val
                # This line is done, go to next
                continue

            # %!csv command
            elif key in ['csv', 'csvheader']:

                table = []
                try:
                    filename, delimiter = val.split()
                except:
                    filename, delimiter = val, ','
                if delimiter == 'space':
                    delimiter = ' '
                elif delimiter == 'tab':
                    delimiter = '\t'
                reader = csv.reader(Readfile(filename), delimiter=delimiter)

                # Convert each CSV line to a txt2tags' table line
                # foo,bar,baz -> | foo | bar | baz |
                try:
                    for row in reader:
                        table.append('| %s |' % ' | '.join(row))
                    if key == 'csvheader':
                        table[0] = '|' + table[0]
                except csv.Error as e:
                    Error('CSV: file %s: %s' % (filename, e))

                # Parse and convert the new table
                # Note: cell contents is raw, no t2t marks are parsed
                if rules['tableable']:
                    ret.extend(BLOCK.blockin('table'))
                    if table:
                        BLOCK.tableparser.__init__(table[0])
                        for row in table:
                            tablerow = TableMaster().parse_row(row)
                            BLOCK.tableparser.add_row(tablerow)

                            # Very ugly, but necessary for escapes
                            line = SEPARATOR.join(tablerow['cells'])
                            BLOCK.holdadd(doEscape(target, line))
                        ret.extend(BLOCK.blockout())

                # Tables are mapped to verb when target is not table-aware
                else:
                    ret.extend(BLOCK.blockin('verb'))
                    BLOCK.propset('mapped', 'table')
                    for row in table:
                        BLOCK.holdadd(row)
                    ret.extend(BLOCK.blockout())

                # This line is done, go to next
                continue

        #---------------------[ dump-source ]-----------------------

        # We don't need to go any further
        if CONF['dump-source']:
            continue

        #---------------------[ Comments ]--------------------------

        # Just skip them (if not macro)
        if regex['comment'].search(line) and not \
           regex['macros'].match(line) and not \
           regex['toc'].match(line):
            continue

        #---------------------[ Triggers ]--------------------------

        # Valid line, reset blank status
        f_lastwasblank = 0

        # Any NOT quote line closes all open quotes
        if BLOCK.isblock('quote') and not regex['quote'].search(line):
            while BLOCK.isblock('quote'):
                ret.extend(BLOCK.blockout())

        # Any NOT table line closes an open table
        if BLOCK.isblock('table') and not regex['table'].search(line):
            ret.extend(BLOCK.blockout())

        #---------------------[ Horizontal Bar ]--------------------

        if regex['bar'].search(line):

            # Bars inside quotes are handled on the Quote processing
            # Otherwise we parse the bars right here
            #
            if not (BLOCK.isblock('quote') or regex['quote'].search(line)) \
                or (BLOCK.isblock('quote') and not rules['barinsidequote']):

                # Close all the opened blocks
                ret.extend(BLOCK.blockin('bar'))

                # Extract the bar chars (- or =)
                m = regex['bar'].search(line)
                bar_chars = m.group(2)

                # Process and dump the tagged bar
                BLOCK.holdadd(bar_chars)
                ret.extend(BLOCK.blockout())
                Debug("BAR: %s" % line, 6)

                # We're done, nothing more to process
                continue

        #---------------------[ Title ]-----------------------------

        if (regex['title'].search(line) or regex['numtitle'].search(line)) \
            and not BLOCK.block().endswith('list'):

            if regex['title'].search(line):
                name = 'title'
            else:
                name = 'numtitle'

            # Close all the opened blocks
            ret.extend(BLOCK.blockin(name))

            # Process title
            TITLE.add(line)
            ret.extend(BLOCK.blockout())

            # We're done, nothing more to process
            continue

        #---------------------[ %%toc ]-----------------------

        # %%toc line closes paragraph
        if BLOCK.block() == 'para' and regex['toc'].search(line):
            ret.extend(BLOCK.blockout())

        #---------------------[ apply masks ]-----------------------

        line = MASK.mask(line)

        #XXX from here, only block-inside lines will pass

        #---------------------[ Quote ]-----------------------------

        if regex['quote'].search(line):

            # Store number of leading TABS
            quotedepth = len(regex['quote'].search(line).group(0))

            # Don't cross depth limit
            maxdepth = rules['quotemaxdepth']
            if maxdepth and quotedepth > maxdepth:
                quotedepth = maxdepth

            # New quote
            if not BLOCK.isblock('quote'):
                ret.extend(BLOCK.blockin('quote'))

            # New subquotes
            while BLOCK.depth < quotedepth:
                BLOCK.blockin('quote')

            # Closing quotes
            while quotedepth < BLOCK.depth:
                ret.extend(BLOCK.blockout())

            # Bar inside quote
            if regex['bar'].search(line) and rules['barinsidequote']:
                tempBlock = BlockMaster()
                tagged_bar = []
                tagged_bar.extend(tempBlock.blockin('bar'))
                tempBlock.holdadd(line)
                tagged_bar.extend(tempBlock.blockout())
                BLOCK.holdextend(tagged_bar)
                continue

        #---------------------[ Lists ]-----------------------------

        # An empty item also closes the current list
        if BLOCK.block().endswith('list'):
            m = regex['listclose'].match(line)
            if m:
                listindent = m.group(1)
                listtype = m.group(2)
                currlisttype = BLOCK.prop('type')
                currlistindent = BLOCK.prop('indent')
                if listindent == currlistindent and \
                   listtype == currlisttype:
                    ret.extend(BLOCK.blockout())
                    continue

        if   regex['list'].search(line) or \
          regex['numlist'].search(line) or \
          regex['deflist'].search(line):

            listindent = BLOCK.prop('indent')
            listids = ''.join(list(LISTNAMES.keys()))
            m = re.match('^( *)([%s]) ' % listids, line)
            listitemindent = m.group(1)
            listtype = m.group(2)
            listname = LISTNAMES[listtype]
            results_box = BLOCK.holdadd

            # Del list ID (and separate term from definition)
            if listname == 'deflist':
                term = parse_deflist_term(line)
                line = regex['deflist'].sub(
                    SEPARATOR + term + SEPARATOR, line)
            else:
                line = regex[listname].sub(SEPARATOR, line)

            # Don't cross depth limit
            maxdepth = rules['listmaxdepth']
            if maxdepth and BLOCK.depth == maxdepth:
                if len(listitemindent) > len(listindent):
                    listitemindent = listindent

            # List bumping (same indent, diff mark)
            # Close the currently open list to clear the mess
            if BLOCK.block().endswith('list') \
               and listname != BLOCK.block() \
               and len(listitemindent) == len(listindent):
                ret.extend(BLOCK.blockout())
                listindent = BLOCK.prop('indent')

            # Open mother list or sublist
            if not BLOCK.block().endswith('list') or \
               len(listitemindent) > len(listindent):
                ret.extend(BLOCK.blockin(listname))
                BLOCK.propset('indent', listitemindent)
                BLOCK.propset('type', listtype)

            # Closing sublists
            while len(listitemindent) < len(BLOCK.prop('indent')):
                ret.extend(BLOCK.blockout())

            # O-oh, sublist before list ("\n\n  - foo\n- foo")
            # Fix: close sublist (as mother), open another list
            if not BLOCK.block().endswith('list'):
                ret.extend(BLOCK.blockin(listname))
                BLOCK.propset('indent', listitemindent)
                BLOCK.propset('type', listtype)

        #---------------------[ Table ]-----------------------------

        #TODO escape undesired format inside table
        #TODO add pm6 target
        if regex['table'].search(line):

            if not BLOCK.isblock('table'):   # first table line!
                ret.extend(BLOCK.blockin('table'))
                BLOCK.tableparser.__init__(line)

            tablerow = TableMaster().parse_row(line)
            BLOCK.tableparser.add_row(tablerow)     # save config

            # Maintain line to unmask and inlines
            # XXX Bug: | **bo | ld** | turns **bo\x01ld** and gets converted :(
            # TODO isolate unmask+inlines parsing to use here
            line = SEPARATOR.join(tablerow['cells'])

        #---------------------[ Paragraph ]-------------------------

        if not BLOCK.block() and \
           not line.count(MASK.tocmask):  # new para!
            ret.extend(BLOCK.blockin('para'))

        ############################################################
        ############################################################
        ############################################################

        #---------------------[ Final Parses ]----------------------

        # The target-specific special char escapes for body lines
        line = doEscape(target, line)

        line = add_inline_tags(line)
        line = MASK.undo(line)

        #---------------------[ Hold or Return? ]-------------------

        ### Now we must choose where to put the parsed line
        #
        if not results_box:
            # List item extra lines
            if BLOCK.block().endswith('list'):
                results_box = BLOCK.holdaddsub
            # Other blocks
            elif BLOCK.block():
                results_box = BLOCK.holdadd
            # No blocks
            else:
                line = doFinalEscape(target, line)
                results_box = ret.append

        results_box(line)

    # EOF: close any open para/verb/lists/table/quotes
    Debug('EOF', 7)
    while BLOCK.block():
        ret.extend(BLOCK.blockout())

    # Maybe close some opened title area?
    if rules['titleblocks']:
        ret.extend(TITLE.close_all())

    # Maybe a major tag to enclose body? (like DIV for CSS)
    if TAGS['bodyOpen']:
        ret.insert(0, TAGS['bodyOpen'])
    if TAGS['bodyClose']:
        ret.append(TAGS['bodyClose'])

    if CONF['toc-only']:
        ret = []
    marked_toc = TITLE.dump_marked_toc(CONF['toc-level'])

    # If dump-source, all parsing is ignored
    if CONF['dump-source']:
        ret = dump_source[:]

    return ret, marked_toc


##############################################################################
################################### GUI ######################################
##############################################################################
#
# Tk help: http://python.org/topics/tkinter/
#    Tuto: http://ibiblio.org/obp/py4fun/gui/tkPhone.html
#          /usr/lib/python*/lib-tk/Tkinter.py
#
# grid table : row=0, column=0, columnspan=2, rowspan=2
# grid align : sticky='n,s,e,w' (North, South, East, West)
# pack place : side='top,bottom,right,left'
# pack fill  : fill='x,y,both,none', expand=1
# pack align : anchor='n,s,e,w' (North, South, East, West)
# padding    : padx=10, pady=10, ipadx=10, ipady=10 (internal)
# checkbox   : offvalue is return if the _user_ deselected the box
# label align: justify=left,right,center

def load_GUI_resources():
    "Load all extra modules and methods used by GUI"
    global askopenfilename, showinfo, showwarning, showerror, Tkinter
    from tkinter.filedialog import askopenfilename
    from tkinter.messagebox import showinfo, showwarning, showerror
    import tkinter


class Gui:
    "Graphical Tk Interface"
    def __init__(self, conf={}):
        self.root = tkinter.Tk()    # mother window, come to butthead
        self.root.title(my_name)    # window title bar text
        self.window = self.root     # variable "focus" for inclusion
        self.row = 0                # row count for grid()

        self.action_length = 150    # left column length (pixel)
        self.frame_margin  = 10     # frame margin size  (pixel)
        self.frame_border  = 6      # frame border size  (pixel)

        # The default Gui colors, can be changed by %!guicolors
        self.dft_gui_colors = ['#6c6', 'white', '#cf9', '#030']
        self.gui_colors = []
        self.bg1 = self.fg1 = self.bg2 = self.fg2 = ''

        # On Tk, vars need to be set/get using setvar()/get()
        self.infile  = self.setvar('')
        self.target  = self.setvar('')
        self.target_name = self.setvar('')

        # The checks appearance order
        self.checks = [
            'headers', 'enum-title', 'toc', 'mask-email', 'toc-only', 'stdout'
        ]

        # Creating variables for all checks
        for check in self.checks:
            setattr(self, 'f_' + check, self.setvar(''))

        # Load RC config
        self.conf = {}
        if conf:
            self.load_config(conf)

    def load_config(self, conf):
        self.conf = conf
        self.gui_colors = conf.get('guicolors') or self.dft_gui_colors
        self.bg1, self.fg1, self.bg2, self.fg2 = self.gui_colors
        self.root.config(bd=15, bg=self.bg1)

    ### Config as dic for python 1.5 compat (**opts don't work :( )
    def entry(self, **opts):
        return tkinter.Entry(self.window, opts)

    def label(self, txt='', bg=None, **opts):
        opts.update({'text': txt, 'bg': bg or self.bg1})
        return tkinter.Label(self.window, opts)

    def button(self, name, cmd, **opts):
        opts.update({'text': name, 'command': cmd})
        return tkinter.Button(self.window, opts)

    def check(self, name, checked=0, **opts):
        bg, fg = self.bg2, self.fg2
        opts.update({
            'text': name,
            'onvalue': 1,
            'offvalue': 0,
            'activeforeground': fg,
            'activebackground': bg,
            'highlightbackground': bg,
            'fg': fg,
            'bg': bg,
            'anchor': 'w'
        })
        chk = tkinter.Checkbutton(self.window, opts)
        if checked:
            chk.select()
        chk.grid(columnspan=2, sticky='w', padx=0)

    def menu(self, sel, items):
        return tkinter.OptionMenu(*(self.window, sel) + tuple(items))

    # Handy auxiliary functions
    def action(self, txt):
        self.label(
            txt,
            fg=self.fg1,
            bg=self.bg1,
            wraplength=self.action_length).grid(column=0, row=self.row)

    def frame_open(self):
        self.window = tkinter.Frame(
            self.root,
            bg=self.bg2,
            borderwidth=self.frame_border)

    def frame_close(self):
        self.window.grid(
            column=1,
            row=self.row,
            sticky='w',
            padx=self.frame_margin)
        self.window = self.root
        self.label('').grid()
        self.row += 2   # update row count

    def target_name2key(self):
        name = self.target_name.get()
        target = [x for x in TARGETS if TARGET_NAMES[x] == name]
        try   :
            key = target[0]
        except:
            key = ''
        self.target = self.setvar(key)

    def target_key2name(self):
        key = self.target.get()
        name = TARGET_NAMES.get(key) or key
        self.target_name = self.setvar(name)

    def exit(self):
        self.root.destroy()

    def setvar(self, val):
        z = tkinter.StringVar()
        z.set(val)
        return z

    def askfile(self):
        ftypes = [(_('txt2tags files'), ('*.t2t', '*.txt')), (_('All files'), '*')]
        newfile = askopenfilename(filetypes=ftypes)
        if newfile:
            self.infile.set(newfile)
            newconf = process_source_file(newfile)[0]
            newconf = ConfigMaster().sanity(newconf, gui=1)
            # Restate all checkboxes after file selection
            #TODO how to make a refresh without killing it?
            self.root.destroy()
            self.__init__(newconf)
            self.mainwindow()

    def scrollwindow(self, txt='no text!', title=''):
        # Create components
        win    = tkinter.Toplevel()
        win.title(title)
        frame  = tkinter.Frame(win)
        scroll = tkinter.Scrollbar(frame)
        text   = tkinter.Text(frame, yscrollcommand=scroll.set)
        button = tkinter.Button(win)
        # Config
        text.insert(tkinter.END, '\n'.join(txt))
        scroll.config(command=text.yview)
        button.config(text=_('Close'), command=win.destroy)
        button.focus_set()
        # Packing
        text.pack(side='left', fill='both', expand=1)
        scroll.pack(side='right', fill='y')
        frame.pack(fill='both', expand=1)
        button.pack(ipadx=30)

    def runprogram(self):
        global CMDLINE_RAW
        # Prepare
        self.target_name2key()
        infile, target = self.infile.get(), self.target.get()
        # Sanity
        if not target:
            showwarning(my_name, _("You must select a target type!"))
            return
        if not infile:
            showwarning(my_name, _("You must provide the source file location!"))
            return
        # Compose cmdline
        guiflags = []
        real_cmdline_conf = ConfigMaster(CMDLINE_RAW).parse()
        if 'infile' in real_cmdline_conf:
            del real_cmdline_conf['infile']
        if 'target' in real_cmdline_conf:
            del real_cmdline_conf['target']
        real_cmdline = CommandLine().compose_cmdline(real_cmdline_conf)
        default_outfile = ConfigMaster().get_outfile_name(
            {'sourcefile': infile, 'outfile': '', 'target': target})
        for opt in self.checks:
            val = int(getattr(self, 'f_%s' % opt).get() or "0")
            if opt == 'stdout':
                opt = 'outfile'
            on_config  = self.conf.get(opt) or 0
            on_cmdline = real_cmdline_conf.get(opt) or 0
            if opt == 'outfile':
                if on_config  == STDOUT:
                    on_config = 1
                else:
                    on_config = 0
                if on_cmdline == STDOUT:
                    on_cmdline = 1
                else:
                    on_cmdline = 0
            if val != on_config or (
              val == on_config == on_cmdline and
              opt in real_cmdline_conf):
                if val:
                    # Was not set, but user selected on GUI
                    Debug("user turned  ON: %s" % opt)
                    if opt == 'outfile':
                        opt = '-o-'
                    else:
                        opt = '--%s' % opt
                else:
                    # Was set, but user deselected on GUI
                    Debug("user turned OFF: %s" % opt)
                    if opt == 'outfile':
                        opt = "-o%s" % default_outfile
                    else:
                        opt = '--no-%s' % opt
                guiflags.append(opt)
        cmdline = [my_name, '-t', target] + real_cmdline + guiflags + [infile]
        Debug('Gui/Tk cmdline: %s' % cmdline, 5)
        # Run!
        cmdline_raw_orig = CMDLINE_RAW
        try:
            # Fake the GUI cmdline as the real one, and parse file
            CMDLINE_RAW = CommandLine().get_raw_config(cmdline[1:])
            data = process_source_file(infile)
            # On GUI, convert_* returns the data, not finish_him()
            outlist, config = convert_this_files([data])
            # On GUI and STDOUT, finish_him() returns the data
            result = finish_him(outlist, config)
            # Show outlist in s a nice new window
            if result:
                outlist, config = result
                title = _('%s: %s converted to %s') % (
                    my_name,
                    os.path.basename(infile),
                    config['target'].upper())
                self.scrollwindow(outlist, title)
            # Show the "file saved" message
            else:
                msg = "%s\n\n  %s\n%s\n\n  %s\n%s" % (
                    _('Conversion done!'),
                    _('FROM:'), infile,
                    _('TO:'), config['outfile'])
                showinfo(my_name, msg)
        except error:         # common error (windowed), not quit
            pass
        except:               # fatal error (windowed and printed)
            errormsg = getUnknownErrorMessage()
            print(errormsg)
            showerror(_('%s FATAL ERROR!') % my_name, errormsg)
            self.exit()
        CMDLINE_RAW = cmdline_raw_orig

    def mainwindow(self):
        self.infile.set(self.conf.get('sourcefile') or '')
        self.target.set(self.conf.get('target') or _('-- select one --'))
        outfile = self.conf.get('outfile')
        if outfile == STDOUT:                  # map -o-
            self.conf['stdout'] = 1
        if self.conf.get('headers') == None:
            self.conf['headers'] = 1       # map default

        action1 = _("Enter the source file location:")
        action2 = _("Choose the target document type:")
        action3 = _("Some options you may check:")
        action4 = _("Some extra options:")
        checks_txt = {
            'headers'   : _("Include headers on output"),
            'enum-title': _("Number titles (1, 1.1, 1.1.1, etc)"),
            'toc'       : _("Do TOC also (Table of Contents)"),
            'mask-email': _("Hide e-mails from SPAM robots"),

            'toc-only'  : _("Just do TOC, nothing more"),
            'stdout'    : _("Dump to screen (Don't save target file)")
        }
        targets_menu = [TARGET_NAMES[x] for x in TARGETS]

        # Header
        self.label("%s %s" % (my_name.upper(), my_version),
            bg=self.bg2, fg=self.fg2).grid(columnspan=2, ipadx=10)
        self.label(_("ONE source, MULTI targets") + '\n%s\n' % my_url,
            bg=self.bg1, fg=self.fg1).grid(columnspan=2)
        self.row = 2
        # Choose input file
        self.action(action1)
        self.frame_open()
        e_infile = self.entry(textvariable=self.infile, width=25)
        e_infile.grid(row=self.row, column=0, sticky='e')
        if not self.infile.get():
            e_infile.focus_set()
        self.button(_("Browse"), self.askfile).grid(
            row=self.row, column=1, sticky='w', padx=10)
        # Show outfile name, style and encoding (if any)
        txt = ''
        if outfile:
            txt = outfile
            if outfile == STDOUT:
                txt = _('<screen>')
            l_output = self.label(_('Output: ') + txt, fg=self.fg2, bg=self.bg2)
            l_output.grid(columnspan=2, sticky='w')
        for setting in ['style', 'encoding']:
            if self.conf.get(setting):
                name = setting.capitalize()
                val  = self.conf[setting]
                self.label('%s: %s' % (name, val),
                    fg=self.fg2, bg=self.bg2).grid(
                    columnspan=2, sticky='w')
        # Choose target
        self.frame_close()
        self.action(action2)
        self.frame_open()
        self.target_key2name()
        self.menu(self.target_name, targets_menu).grid(
            columnspan=2, sticky='w')
        # Options checkboxes label
        self.frame_close()
        self.action(action3)
        self.frame_open()
        # Compose options check boxes, example:
        # self.check(checks_txt['toc'], 1, variable=self.f_toc)
        for check in self.checks:
            # Extra options label
            if check == 'toc-only':
                self.frame_close()
                self.action(action4)
                self.frame_open()
            txt = checks_txt[check]
            var = getattr(self, 'f_' + check)
            checked = self.conf.get(check)
            self.check(txt, checked, variable=var)
        self.frame_close()
        # Spacer and buttons
        self.label('').grid()
        self.row += 1
        b_quit = self.button(_("Quit"), self.exit)
        b_quit.grid(row=self.row, column=0, sticky='w', padx=30)
        b_conv = self.button(_("Convert!"), self.runprogram)
        b_conv.grid(row=self.row, column=1, sticky='e', padx=30)
        if self.target.get() and self.infile.get():
            b_conv.focus_set()

        # As documentation told me
        if sys.platform.startswith('win'):
            self.root.iconify()
            self.root.update()
            self.root.deiconify()

        self.root.mainloop()


##############################################################################
##############################################################################

def exec_command_line(user_cmdline=[]):
    global CMDLINE_RAW, RC_RAW, DEBUG, VERBOSE, QUIET, GUI, Error

    # Extract command line data
    cmdline_data = user_cmdline or sys.argv[1:]
    CMDLINE_RAW = CommandLine().get_raw_config(cmdline_data, relative=1)
    cmdline_parsed = ConfigMaster(CMDLINE_RAW).parse()
    DEBUG   = cmdline_parsed.get('debug') or 0
    VERBOSE = cmdline_parsed.get('verbose') or 0
    QUIET   = cmdline_parsed.get('quiet') or 0
    GUI     = cmdline_parsed.get('gui') or 0
    infiles = cmdline_parsed.get('infile') or []

    Message(_("Txt2tags %s processing begins") % my_version, 1)

    # The easy ones
    if cmdline_parsed.get('help'):
        Quit(Usage())
    if cmdline_parsed.get('version'):
        Quit(VERSIONSTR)
    if cmdline_parsed.get('targets'):
        listTargets()
        Quit()

    # Multifile haters
    if len(infiles) > 1:
        errmsg = _("Option --%s can't be used with multiple input files")
        for option in NO_MULTI_INPUT:
            if cmdline_parsed.get(option):
                Error(errmsg % option)

    Debug("system platform: %s" % sys.platform)
    Debug("python version: %s" % (sys.version.split('(')[0]))
    Debug("line break char: %s" % repr(LB))
    Debug("command line: %s" % sys.argv)
    Debug("command line raw config: %s" % CMDLINE_RAW, 1)

    # Extract RC file config
    if cmdline_parsed.get('rc') == 0:
        Message(_("Ignoring user configuration file"), 1)
    else:
        rc_file = get_rc_path()
        if os.path.isfile(rc_file):
            Message(_("Loading user configuration file"), 1)
            RC_RAW = ConfigLines(file_=rc_file).get_raw_config()

        Debug("rc file: %s" % rc_file)
        Debug("rc file raw config: %s" % RC_RAW, 1)

    # Get all infiles config (if any)
    infiles_config = get_infiles_config(infiles)

    # Is GUI available?
    # Try to load and start GUI interface for --gui
    if GUI:
        try:
            load_GUI_resources()
            Debug("GUI resources OK (Tk module is installed)")
            winbox = Gui()
            Debug("GUI display OK")
            GUI = 1
        except:
            Debug("GUI Error: no Tk module or no DISPLAY")
            GUI = 0

    # User forced --gui, but it's not available
    if cmdline_parsed.get('gui') and not GUI:
        print(getTraceback())
        print()
        Error(
            "Sorry, I can't run my Graphical Interface - GUI\n"
            "- Check if Python Tcl/Tk module is installed (Tkinter)\n"
            "- Make sure you are in a graphical environment (like X)")

    # Okay, we will use GUI
    if GUI:
        Message(_("We are on GUI interface"), 1)

        # Redefine Error function to raise exception instead sys.exit()
        def Error(msg):
            showerror(_('txt2tags ERROR!'), msg)
            raise error

        # If no input file, get RC+cmdline config, else full config
        if not infiles:
            gui_conf = ConfigMaster(RC_RAW + CMDLINE_RAW).parse()
        else:
            try:
                gui_conf = infiles_config[0][0]
            except:
                gui_conf = {}

        # Sanity is needed to set outfile and other things
        gui_conf = ConfigMaster().sanity(gui_conf, gui=1)
        Debug("GUI config: %s" % gui_conf, 5)

        # Insert config and populate the nice window!
        winbox.load_config(gui_conf)
        winbox.mainwindow()

    # Console mode rocks forever!
    else:
        Message(_("We are on Command Line interface"), 1)

        # Called with no arguments, show error
        # TODO#1: this checking should be only in ConfigMaster.sanity()
        if not infiles:
            Error(_('Missing input file (try --help)') + '\n\n' +
            _('Please inform an input file (.t2t) at the end of the command.') + '\n' +
            _('Example:') + ' %s -t html %s' % (my_name, _('file.t2t')))

        convert_this_files(infiles_config)

    Message(_("Txt2tags finished successfully"), 1)

if __name__ == '__main__':
    try:
        exec_command_line()
    except error as msg:
        sys.stderr.write("%s\n" % msg)
        sys.stderr.flush()
        sys.exit(1)
    except SystemExit:
        pass
    except:
        sys.stderr.write(getUnknownErrorMessage())
        sys.stderr.flush()
        sys.exit(1)
    Quit()

# The End.
