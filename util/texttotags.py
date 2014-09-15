--- txt2tags.py	(original)
+++ txt2tags.py	(refactored)
@@ -281,7 +281,7 @@
   'spip'   : _('SPIP article'),
   'rtf'    : _('RTF document'),
 }
-TARGETS = TARGET_NAMES.keys()
+TARGETS = list(TARGET_NAMES.keys())
 TARGETS.sort()
 
 
@@ -306,7 +306,7 @@
 # ASCII Art config
 AA_KEYS = 'corner border side bar1 bar2 level2 level3 level4 level5 bullet hhead vhead'.split()
 AA_VALUES = '+-|-==-^"-=$'  # do not edit here, please use --chars
-AA = dict(zip(AA_KEYS, AA_VALUES))
+AA = dict(list(zip(AA_KEYS, AA_VALUES)))
 AA_COUNT = 0
 AA_TITLE = ''
 AA_MARKS = []
@@ -332,7 +332,7 @@
 # http://docs.python.org/release/2.7/documenting/rest.html#sections
 RST_KEYS = 'title level1 level2 level3 level4 level5 bar1 bullet'.split()
 RST_VALUES = '#*=-^"--'  # do not edit here, please use --chars
-RST = dict(zip(RST_KEYS, RST_VALUES))
+RST = dict(list(zip(RST_KEYS, RST_VALUES)))
 
 RC_RAW = []
 CMDLINE_RAW = []
@@ -2221,7 +2221,7 @@
 
     # Make the HTML -> XHTML inheritance
     xhtml = alltags['html'].copy()
-    for key in xhtml.keys():
+    for key in list(xhtml.keys()):
         xhtml[key] = xhtml[key].lower()
     # Some like HTML tags as lowercase, some don't... (headers out)
     if HTML_LOWER:
@@ -2251,7 +2251,7 @@
 
     for key in keys:
         tags[key] = ''  # create empty keys
-    for key in target_tags.keys():
+    for key in list(target_tags.keys()):
         tags[key] = maskEscapeChar(target_tags[key])  # populate
 
     # Map strong line to pagebreak
@@ -3021,7 +3021,7 @@
 
     # %%macroname [ (formatting) ]
     bank['macros'] = re.compile(r'%%%%(?P<name>%s)\b(\((?P<fmt>.*?)\))?' % (
-        '|'.join(MACROS.keys())), re.I)
+        '|'.join(list(MACROS.keys()))), re.I)
 
     # %%TOC special macro for TOC positioning
     bank['toc'] = re.compile(r'^ *%%toc\s*$', re.I)
@@ -3296,7 +3296,7 @@
         return len(txt)
     l = 0
     for char in txt:
-        if unicodedata.east_asian_width(unicode(char)) in ('F', 'W'):
+        if unicodedata.east_asian_width(str(char)) in ('F', 'W'):
             l = l + 2
         else:
             l = l + 1
@@ -3316,12 +3316,12 @@
 
 
 def echo(msg):   # for quick debug
-    print '\033[32;1m%s\033[m' % msg
+    print('\033[32;1m%s\033[m' % msg)
 
 
 def Quit(msg=''):
     if msg:
-        print msg
+        print(msg)
     sys.exit(0)
 
 
@@ -3350,14 +3350,14 @@
 def Message(msg, level):
     if level <= VERBOSE and not QUIET:
         prefix = '-' * 5
-        print "%s %s" % (prefix * level, msg)
+        print("%s %s" % (prefix * level, msg))
 
 
 def Debug(msg, id_=0, linenr=None):
     "Show debug messages, categorized (colored or not)"
     if QUIET or not DEBUG:
         return
-    if int(id_) not in range(8):
+    if int(id_) not in list(range(8)):
         id_ = 0
     # 0:black 1:red 2:green 3:yellow 4:blue 5:pink 6:cyan 7:white ;1:light
     ids            = ['INI', 'CFG', 'SRC', 'BLK', 'HLD', 'GUI', 'OUT', 'DET']
@@ -3371,7 +3371,7 @@
         else:
             color = colors_bgdark[id_]
         msg = '\033[3%sm%s\033[m' % (color, msg)
-    print "++ %s: %s" % (ids[id_], msg)
+    print("++ %s: %s" % (ids[id_], msg))
 
 
 def Readfile(file_path, remove_linebreaks=0, ignore_error=0):
@@ -3388,7 +3388,7 @@
     # URL
     elif PathMaster().is_url(file_path):
         try:
-            from urllib import urlopen
+            from urllib.request import urlopen
             f = urlopen(file_path)
             if f.getcode() == 404:  # URL not found
                 raise
@@ -3409,7 +3409,7 @@
                 Error(_("Cannot read file:") + ' ' + file_path)
 
     if remove_linebreaks:
-        data = map(lambda x: re.sub('[\n\r]+$', '', x), data)
+        data = [re.sub('[\n\r]+$', '', x) for x in data]
 
     Message(_("File read (%d lines): %s") % (len(data), file_path), 2)
     return data
@@ -3427,13 +3427,13 @@
     cont = []
     if CONF['target'] in ('aat', 'rst', 'txt'):
         for line in contents:
-            if isinstance(line, unicode):
+            if isinstance(line, str):
                 cont.append(line.encode('utf-8'))
             else:
                 cont.append(line)
     elif CONF['target'] == 'mgp':
         for line in contents:
-            if isinstance(line, unicode):
+            if isinstance(line, str):
                 cont.append(line.encode('latin1', 'replace'))
             else:
                 cont.append(line)
@@ -3444,8 +3444,8 @@
 
 
 def showdic(dic):
-    for k in dic.keys():
-        print "%15s : %s" % (k, dic[k])
+    for k in list(dic.keys()):
+        print("%15s : %s" % (k, dic[k]))
 
 
 def dotted_spaces(txt=''):
@@ -3550,9 +3550,9 @@
         raw = CommandLine().get_raw_config(sys.argv[1:])
     """
     def __init__(self):
-        self.all_options = OPTIONS.keys()
-        self.all_flags   = FLAGS.keys()
-        self.all_actions = ACTIONS.keys()
+        self.all_options = list(OPTIONS.keys())
+        self.all_flags   = list(FLAGS.keys())
+        self.all_actions = list(ACTIONS.keys())
 
         # short:long options equivalence
         self.short_long = {
@@ -3576,7 +3576,7 @@
     def _compose_short_opts(self):
         "Returns a string like 'hVt:o' with all short options/flags"
         ret = []
-        for opt in self.short_long.keys():
+        for opt in list(self.short_long.keys()):
             long_ = self.short_long[opt]
             if long_ in self.all_options:   # is flag or option?
                 opt = opt + ':'             # option: have param
@@ -3586,10 +3586,10 @@
 
     def _compose_long_opts(self):
         "Returns a list with all the valid long options/flags"
-        ret = map(lambda x: x + '=', self.all_options)        # add =
+        ret = [x + '=' for x in self.all_options]        # add =
         ret.extend(self.all_flags)                            # flag ON
         ret.extend(self.all_actions)                          # actions
-        ret.extend(map(lambda x: 'no-' + x, self.all_flags))  # add no-*
+        ret.extend(['no-' + x for x in self.all_flags])  # add no-*
         ret.extend(['no-style', 'no-encoding'])               # turn OFF
         ret.extend(['no-outfile', 'no-infile'])               # turn OFF
         ret.extend(['no-dump-config', 'no-dump-source'])      # turn OFF
@@ -3609,7 +3609,7 @@
         # Parse it!
         try:
             opts, args = getopt.getopt(cmdline, short, long_)
-        except getopt.error, errmsg:
+        except getopt.error as errmsg:
             Error(_("%s (try --help)") % errmsg)
         return (opts, args)
 
@@ -3621,7 +3621,7 @@
         ret = []
 
         # We need lists, not strings (such as from %!options)
-        if type(cmdline) in (type(''), type(u'')):
+        if type(cmdline) in (type(''), type('')):
             cmdline = self._tokenize(cmdline)
 
         # Extract name/value pair of all configs, check for invalid names
@@ -3717,7 +3717,7 @@
             args.append('-t ' + cfg['target'])
             del cfg['target']
         # Add other options
-        for key in cfg.keys():
+        for key in list(cfg.keys()):
             if key not in valid_opts:
                 continue  # may be a %!setting
             if key == 'outfile' or key == 'infile':
@@ -3847,7 +3847,7 @@
             ref[1] = 2
         rgx = getRegexes()
         on_comment_block = 0
-        for i in xrange(ref[1], len(buf)):         # find body init:
+        for i in range(ref[1], len(buf)):         # find body init:
             # Handle comment blocks inside config area
             if not on_comment_block \
                and rgx['blockCommentOpen'].search(buf[i]):
@@ -3883,7 +3883,7 @@
         # Fancyness sample: head conf body (1 4 8)
         self.areas_fancy = "%s (%s)" % (
             ' '.join(self.areas),
-            ' '.join(map(str, map(lambda x: x or '', ref))))
+            ' '.join(map(str, [x or '' for x in ref])))
         Message(_("Areas found: %s") % self.areas_fancy, 2)
 
     def get_raw_config(self):
@@ -3976,11 +3976,11 @@
     def _get_off(self):
         "Turns OFF all the config/options/flags"
         off = {}
-        for key in self.defaults.keys():
+        for key in list(self.defaults.keys()):
             kind = type(self.defaults[key])
             if kind == type(9):
                 off[key] = 0
-            elif kind == type('') or kind == type(u''):
+            elif kind == type('') or kind == type(''):
                 off[key] = ''
             elif kind == type([]):
                 off[key] = []
@@ -4007,7 +4007,7 @@
         # %!options
         if key == 'options':
             # Actions are not valid inside %!options
-            ignoreme = self.dft_actions.keys()
+            ignoreme = list(self.dft_actions.keys())
             # --target inside %!options is not allowed (use %!target)
             ignoreme.append('target')
             # But there are some exceptions that are allowed (XXX why?)
@@ -4118,7 +4118,7 @@
         empty.update(config)
         config = empty.copy()
         # Check integers options
-        for key in config.keys():
+        for key in list(config.keys()):
             if key in self.numeric:
                 try:
                     config[key] = int(config[key])
@@ -4175,11 +4175,11 @@
                 if len(config['chars']) != len(AA_VALUES):
                     Error(_("--chars: Expected %i chars, got %i") % (
                         len(AA_VALUES), len(config['chars'])))
-                if isinstance(config['chars'], unicode): 
+                if isinstance(config['chars'], str): 
                     for char in config['chars']:
                         if unicodedata.east_asian_width(char) in ('F', 'W'):
                             Error(_("--chars: Expected no CJK double width chars, but got %s") % char.encode('utf-8'))
-                AA = dict(zip(AA_KEYS, config['chars']))
+                AA = dict(list(zip(AA_KEYS, config['chars'])))
             elif target == 'rst':
                 if len(config['chars']) != len(RST_VALUES):
                     Error(_("--chars: Expected %i chars, got %i") % (
@@ -4198,7 +4198,7 @@
                         if locale.getpreferredencoding() == 'UTF-8':
                             char_8 = char_8.encode('utf-8') 
                         Error(_("--chars: Expected chars in : %s but got %s") % (chars_bullet, char_8))
-                    RST = dict(zip(RST_KEYS, config['chars']))
+                    RST = dict(list(zip(RST_KEYS, config['chars'])))
 
         # --toc-only is stronger than others
         if config['toc-only']:
@@ -4227,7 +4227,7 @@
                 self.add(key, value.decode('utf-8'))
             else:
                 self.add(key, value)
-        Message(_("Added the following keys: %s") % ', '.join(self.parsed.keys()), 2)
+        Message(_("Added the following keys: %s") % ', '.join(list(self.parsed.keys())), 2)
         return self.parsed.copy()
 
     def find_value(self, key='', target=''):
@@ -4320,7 +4320,7 @@
         errormsg = _("Invalid CONFIG line on %s") + "\n%03d:%s"
         lines = Readfile(filename, remove_linebreaks=1)
         # Sanity: try to find invalid config lines
-        for i in xrange(len(lines)):
+        for i in range(len(lines)):
             line = lines[i].rstrip()
             if not line:  # empty
                 continue
@@ -4358,7 +4358,7 @@
             ret.append([target, key, val])
             Message(_("Added %s") % key, 3)
 
-        for i in xrange(len(self.lines)):
+        for i in range(len(self.lines)):
             line = self.lines[i]
             Message(_("Processing line %03d: %s") % (first + i, line), 2)
             target, key, val = self.parse_line(line)
@@ -4744,10 +4744,10 @@
             # Reset sublevels count (if any)
             max_levels = len(self.count)
             if self.level < max_levels - 1:
-                for i in xrange(self.level + 1, max_levels):
+                for i in range(self.level + 1, max_levels):
                     self.count[i] = 0
             # Compose count id from hierarchy
-            for i in xrange(self.level):
+            for i in range(self.level):
                 count_id = "%s%d." % (count_id, self.count[i + 1])
         self.count_id = count_id
 
@@ -4947,7 +4947,7 @@
             tborder = ''
         # Set the columns alignment
         if rules['tablecellaligntype'] == 'column':
-            calign = map(lambda x: TAGS['_tableColAlign%s' % x], self.colalign)
+            calign = [TAGS['_tableColAlign%s' % x] for x in self.colalign]
             calign = calignsep.join(calign)
         # Align full table, set border and Column align (if any)
         topen = regex['_tableAlign'].sub(talign , topen)
@@ -4987,8 +4987,8 @@
         close = TAGS['tableCellClose']
         sep = TAGS['tableCellSep']
         head = TAGS['tableCellHead']
-        calign = map(lambda x: TAGS['_tableCellAlign' + x], rowdata['cellalign'])
-        caligntag = map(lambda x: TAGS['tableCellAlign' + x], rowdata['cellalign'])
+        calign = [TAGS['_tableCellAlign' + x] for x in rowdata['cellalign']]
+        caligntag = [TAGS['tableCellAlign' + x] for x in rowdata['cellalign']]
         calignsep = TAGS['tableColAlignSep']
         ncolumns = len(self.colalign)
 
@@ -5055,9 +5055,9 @@
 
         # Cells pre processing
         if rules['tablecellstrip']:
-            cells = map(lambda x: x.strip(), cells)
+            cells = [x.strip() for x in cells]
         if rowdata['title'] and rules['tabletitlerowinbold']:
-            cells = map(lambda x: enclose_me('fontBold', x), cells)
+            cells = [enclose_me('fontBold', x) for x in cells]
 
         # Add cell BEGIN/END tags
         for cell in cells:
@@ -5158,7 +5158,7 @@
         # Find cells span
         ret['cellspan'] = self._get_cell_span(ret['cells'])
         # Remove span ID
-        ret['cells'] = map(lambda x: re.sub('\a\|+$', '', x), ret['cells'])
+        ret['cells'] = [re.sub('\a\|+$', '', x) for x in ret['cells']]
         # Find cells align
         ret['cellalign'] = self._get_cell_align(ret['cells'])
         # Hooray!
@@ -5252,7 +5252,7 @@
             'title'   : [],
             'numtitle': [],
         }
-        self.allblocks = self.contains.keys()
+        self.allblocks = list(self.contains.keys())
 
         # If one is found inside another, ignore the marks
         self.exclusive = ['comment', 'verb', 'raw', 'tagged']
@@ -5415,7 +5415,7 @@
         ret = []
         for line in self.hold():
             linetype = type(line)
-            if linetype == type('') or linetype == type(u''):
+            if linetype == type('') or linetype == type(''):
                 ret.append(self._last_escapes(line))
             elif linetype == type([]):
                 ret.extend(line)
@@ -5490,7 +5490,7 @@
 
     def raw(self):
         lines = self.hold()
-        return map(lambda x: doEscape(TARGET, x), lines)
+        return [doEscape(TARGET, x) for x in lines]
 
     def tagged(self):
         return self.hold()
@@ -5626,7 +5626,7 @@
             try:
                 import aafigure
                 t_name = 'table_' + str(self.tablecount) + '.png'
-                aafigure.render(unicode('\n'.join(aa_t)), t_name, {'format':'png', 'background':'#000000', 'foreground':'#FFFFFF', 'textual':True})  
+                aafigure.render(str('\n'.join(aa_t)), t_name, {'format':'png', 'background':'#000000', 'foreground':'#FFFFFF', 'textual':True})  
                 return ['%center', '%newimage "' + t_name + '"']
             except:
                 return ['%font "mono"'] + aa_t + ['']
@@ -5644,7 +5644,7 @@
 
         # Rewrite all table cells by the unmasked and escaped data
         lines = self._get_escaped_hold()
-        for i in xrange(len(lines)):
+        for i in range(len(lines)):
             cells = lines[i].split(SEPARATOR)
             self.tableparser.rows[i]['cells'] = cells
         result.extend(self.tableparser.dump())
@@ -5987,7 +5987,7 @@
                         # 'Thu, 18 Nov 2010 22:42:11 GMT'
                         # >>>
                         #
-                        from urllib import urlopen
+                        from urllib.request import urlopen
                         from email.Utils import parsedate
 
                         f = urlopen(self.infile)
@@ -6055,11 +6055,11 @@
     for typ in TARGET_TYPES:
         targets = list(TARGET_TYPES[typ][1])
         targets.sort()
-        print
-        print TARGET_TYPES[typ][0] + ':'
+        print()
+        print(TARGET_TYPES[typ][0] + ':')
         for target in targets:
-            print "\t%s\t%s" % (target, TARGET_NAMES.get(target))
-    print
+            print("\t%s\t%s" % (target, TARGET_NAMES.get(target)))
+    print()
 
 
 def dumpConfig(source_raw, parsed_config):
@@ -6071,16 +6071,16 @@
     ]
     # First show all RAW data found
     for label, cfg in data:
-        print _('RAW config for %s') % label
+        print(_('RAW config for %s') % label)
         for target, key, val in cfg:
             target = '(%s)' % target
             key    = dotted_spaces("%-14s" % key)
             val    = val or _('ON')
-            print '  %-8s %s: %s' % (target, key, val)
-        print
+            print('  %-8s %s: %s' % (target, key, val))
+        print()
     # Then the parsed results of all of them
-    print _('Full PARSED config')
-    keys = parsed_config.keys()
+    print(_('Full PARSED config'))
+    keys = list(parsed_config.keys())
     keys.sort()  # sorted
     for key in keys:
         val = parsed_config[key]
@@ -6097,13 +6097,13 @@
             else:
                 sep = ', '
             val = sep.join(val)
-        print "%25s: %s" % (dotted_spaces("%-14s" % key), val)
-    print
-    print _('Active filters')
+        print("%25s: %s" % (dotted_spaces("%-14s" % key), val))
+    print()
+    print(_('Active filters'))
     for filter_ in ['preproc', 'postproc', 'postvoodoo']:
         for rule in parsed_config.get(filter_) or []:
-            print "%25s: %s  ->  %s" % (
-                dotted_spaces("%-14s" % filter_), rule[0], rule[1])
+            print("%25s: %s  ->  %s" % (
+                dotted_spaces("%-14s" % filter_), rule[0], rule[1]))
 
 
 def get_file_body(file_):
@@ -6186,19 +6186,19 @@
             return outlist, config
         else:
             for line in outlist:
-                print line
+                print(line)
     else:
         Savefile(outfile, addLineBreaks(outlist))
         if not GUI and not QUIET:
-            print _('%s wrote %s') % (my_name, outfile)
+            print(_('%s wrote %s') % (my_name, outfile))
 
     if config['split']:
         if not QUIET:
-            print "--- html..."
+            print("--- html...")
         sgml2html = 'sgml2html -s %s -l %s %s' % (
             config['split'], config['lang'] or lang, outfile)
         if not QUIET:
-            print "Running system command:", sgml2html
+            print("Running system command:", sgml2html)
         os.system(sgml2html)
 
 
@@ -6344,14 +6344,14 @@
     config['stylepath_out'] = fix_css_out_path(config)
 
     # Populate head_data with config info
-    for key in head_data.keys():
+    for key in list(head_data.keys()):
         val = config.get(key.lower())
         if key == 'STYLE' and 'html' in target:
             val = config.get('stylepath_out') or []
         # Remove .sty extension from each style filename (freaking tex)
         # XXX Can't handle --style foo.sty, bar.sty
         if target == 'tex' and key == 'STYLE':
-            val = map(lambda x: re.sub('(?i)\.sty$', '', x), val)
+            val = [re.sub('(?i)\.sty$', '', x) for x in val]
         if key == 'ENCODING':
             val = get_encoding_string(val, target)
         head_data[key] = val
@@ -6436,7 +6436,7 @@
     # If found, remove the reference
     # If there isn't any other key reference on the same line, remove it
     #TODO loop by template line > key
-    for key in head_data.keys():
+    for key in list(head_data.keys()):
         if head_data.get(key):
             continue
         for line in template:
@@ -6453,7 +6453,7 @@
         head_data['STYLE'] = styles[0]
     elif len(styles) > 1:
         style_mark = '%(STYLE)s'
-        for i in xrange(len(template)):
+        for i in range(len(template)):
             if template[i].count(style_mark):
                 while styles:
                     template.insert(i + 1, template[i].replace(style_mark, styles.pop()))
@@ -6461,7 +6461,7 @@
                 break
 
     # Expand macros on *all* lines of the template
-    template = map(MacroMaster(config=config).expand, template)
+    template = list(map(MacroMaster(config=config).expand, template))
     # Add Body contents to template data
     head_data['BODY'] = '\n'.join(config['fullBody'])
     # Populate template with data (dict expansion)
@@ -6472,7 +6472,7 @@
     if target in ('html', 'xhtml', 'xhtmls', 'html5') and config.get('css-inside') and \
        config.get('stylepath'):
         set_global_config(config)  # usually on convert(), needed here
-        for i in xrange(len(config['stylepath'])):
+        for i in range(len(config['stylepath'])):
             cssfile = config['stylepath'][i]
             try:
                 contents = Readfile(cssfile, remove_linebreaks=1)
@@ -6637,14 +6637,14 @@
 def maskEscapeChar(data):
     "Replace any Escape Char \ with a text mask (Input: str or list)"
     if type(data) == type([]):
-        return map(lambda x: EscapeCharHandler('mask', x), data)
+        return [EscapeCharHandler('mask', x) for x in data]
     return EscapeCharHandler('mask', data)
 
 
 def unmaskEscapeChar(data):
     "Undo the Escape char \ masking (Input: str or list)"
     if type(data) == type([]):
-        return map(lambda x: EscapeCharHandler('unmask', x), data)
+        return [EscapeCharHandler('unmask', x) for x in data]
     return EscapeCharHandler('unmask', data)
 
 
@@ -6667,7 +6667,7 @@
 
 def compile_filters(filters, errmsg='Filter'):
     if filters:
-        for i in xrange(len(filters)):
+        for i in range(len(filters)):
             patt, repl = filters[i]
             try:
                 rgx = re.compile(patt)
@@ -7006,9 +7006,9 @@
             config_value = full_parsed.get(full_parsed['show-config-value'])
             if config_value:
                 if type(config_value) == type([]):
-                    print '\n'.join(config_value)
+                    print('\n'.join(config_value))
                 else:
-                    print config_value
+                    print(config_value)
             Quit()
         # Okay, all done
         Debug("FULL config for this file: %s" % full_parsed, 1)
@@ -7023,7 +7023,7 @@
     for each input file. This function is supposed to be the very
     first one to be called, before any processing.
     """
-    return map(process_source_file, infiles)
+    return list(map(process_source_file, infiles))
 
 
 def convert_this_files(configs):
@@ -7066,7 +7066,7 @@
         # If dump-source, we're done
         if myconf['dump-source']:
             for line in source_head + source_conf + target_body:
-                print line
+                print(line)
             return
 
         # Close the last slide
@@ -7671,7 +7671,7 @@
                         table.append('| %s |' % ' | '.join(row))
                     if key == 'csvheader':
                         table[0] = '|' + table[0]
-                except csv.Error, e:
+                except csv.Error as e:
                     Error('CSV: file %s: %s' % (filename, e))
 
                 # Parse and convert the new table
@@ -7839,7 +7839,7 @@
           regex['deflist'].search(line):
 
             listindent = BLOCK.prop('indent')
-            listids = ''.join(LISTNAMES.keys())
+            listids = ''.join(list(LISTNAMES.keys()))
             m = re.match('^( *)([%s]) ' % listids, line)
             listitemindent = m.group(1)
             listtype = m.group(2)
@@ -7986,15 +7986,15 @@
 def load_GUI_resources():
     "Load all extra modules and methods used by GUI"
     global askopenfilename, showinfo, showwarning, showerror, Tkinter
-    from tkFileDialog import askopenfilename
-    from tkMessageBox import showinfo, showwarning, showerror
-    import Tkinter
+    from tkinter.filedialog import askopenfilename
+    from tkinter.messagebox import showinfo, showwarning, showerror
+    import tkinter
 
 
 class Gui:
     "Graphical Tk Interface"
     def __init__(self, conf={}):
-        self.root = Tkinter.Tk()    # mother window, come to butthead
+        self.root = tkinter.Tk()    # mother window, come to butthead
         self.root.title(my_name)    # window title bar text
         self.window = self.root     # variable "focus" for inclusion
         self.row = 0                # row count for grid()
@@ -8035,15 +8035,15 @@
 
     ### Config as dic for python 1.5 compat (**opts don't work :( )
     def entry(self, **opts):
-        return Tkinter.Entry(self.window, opts)
+        return tkinter.Entry(self.window, opts)
 
     def label(self, txt='', bg=None, **opts):
         opts.update({'text': txt, 'bg': bg or self.bg1})
-        return Tkinter.Label(self.window, opts)
+        return tkinter.Label(self.window, opts)
 
     def button(self, name, cmd, **opts):
         opts.update({'text': name, 'command': cmd})
-        return Tkinter.Button(self.window, opts)
+        return tkinter.Button(self.window, opts)
 
     def check(self, name, checked=0, **opts):
         bg, fg = self.bg2, self.fg2
@@ -8058,13 +8058,13 @@
             'bg': bg,
             'anchor': 'w'
         })
-        chk = Tkinter.Checkbutton(self.window, opts)
+        chk = tkinter.Checkbutton(self.window, opts)
         if checked:
             chk.select()
         chk.grid(columnspan=2, sticky='w', padx=0)
 
     def menu(self, sel, items):
-        return apply(Tkinter.OptionMenu, (self.window, sel) + tuple(items))
+        return tkinter.OptionMenu(*(self.window, sel) + tuple(items))
 
     # Handy auxiliary functions
     def action(self, txt):
@@ -8075,7 +8075,7 @@
             wraplength=self.action_length).grid(column=0, row=self.row)
 
     def frame_open(self):
-        self.window = Tkinter.Frame(
+        self.window = tkinter.Frame(
             self.root,
             bg=self.bg2,
             borderwidth=self.frame_border)
@@ -8092,7 +8092,7 @@
 
     def target_name2key(self):
         name = self.target_name.get()
-        target = filter(lambda x: TARGET_NAMES[x] == name, TARGETS)
+        target = [x for x in TARGETS if TARGET_NAMES[x] == name]
         try   :
             key = target[0]
         except:
@@ -8108,7 +8108,7 @@
         self.root.destroy()
 
     def setvar(self, val):
-        z = Tkinter.StringVar()
+        z = tkinter.StringVar()
         z.set(val)
         return z
 
@@ -8127,14 +8127,14 @@
 
     def scrollwindow(self, txt='no text!', title=''):
         # Create components
-        win    = Tkinter.Toplevel()
+        win    = tkinter.Toplevel()
         win.title(title)
-        frame  = Tkinter.Frame(win)
-        scroll = Tkinter.Scrollbar(frame)
-        text   = Tkinter.Text(frame, yscrollcommand=scroll.set)
-        button = Tkinter.Button(win)
+        frame  = tkinter.Frame(win)
+        scroll = tkinter.Scrollbar(frame)
+        text   = tkinter.Text(frame, yscrollcommand=scroll.set)
+        button = tkinter.Button(win)
         # Config
-        text.insert(Tkinter.END, '\n'.join(txt))
+        text.insert(tkinter.END, '\n'.join(txt))
         scroll.config(command=text.yview)
         button.config(text=_('Close'), command=win.destroy)
         button.focus_set()
@@ -8230,7 +8230,7 @@
             pass
         except:               # fatal error (windowed and printed)
             errormsg = getUnknownErrorMessage()
-            print errormsg
+            print(errormsg)
             showerror(_('%s FATAL ERROR!') % my_name, errormsg)
             self.exit()
         CMDLINE_RAW = cmdline_raw_orig
@@ -8257,7 +8257,7 @@
             'toc-only'  : _("Just do TOC, nothing more"),
             'stdout'    : _("Dump to screen (Don't save target file)")
         }
-        targets_menu = map(lambda x: TARGET_NAMES[x], TARGETS)
+        targets_menu = [TARGET_NAMES[x] for x in TARGETS]
 
         # Header
         self.label("%s %s" % (my_name.upper(), my_version),
@@ -8402,8 +8402,8 @@
 
     # User forced --gui, but it's not available
     if cmdline_parsed.get('gui') and not GUI:
-        print getTraceback()
-        print
+        print(getTraceback())
+        print()
         Error(
             "Sorry, I can't run my Graphical Interface - GUI\n"
             "- Check if Python Tcl/Tk module is installed (Tkinter)\n"
@@ -8453,7 +8453,7 @@
 if __name__ == '__main__':
     try:
         exec_command_line()
-    except error, msg:
+    except error as msg:
         sys.stderr.write("%s\n" % msg)
         sys.stderr.flush()
         sys.exit(1)
