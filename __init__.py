import re
import types


class MarkdownColorFormatter:
        _BLACK, _RED, _GREEN, _YELLOW, _BLUE, _MAGENTA, _CYAN, _WHITE = range(8)

        _FORMATS = {
    		'BOLD'		: 1,
    		'ITALICS'	: 3,
    		'UNDERLINE'	: 4,
    		'REVERSE'	: 7,
    		'STRIKETHROUGH'	: 9
        }

        _COLORS = {
    		'BLACK'		: _BLACK,
    		'RED'		: _RED,
    		'GREEN'		: _GREEN,
    		'YELLOW'	: _YELLOW,
    		'BLUE'		: _BLUE,
    		'MAGENTA'	: _MAGENTA,
    		'CYAN'		: _CYAN,
    		'WHITE'		: _WHITE
        }

        _CUSTOM = {
    		'ok'		: '{{green}}**%s**{{green}}',
    		'failed'	: '{{red}}**%s**{{red}}',
    		'warn'		: '{{red}}**%s**{{red}}',
    		'error'		: '{{white-red}}**%s**{{white}}'
        }

        class _ESC:
            SEQ = '\033[%sm'
            RESET = '\033[0m'

        LOG_LEVEL_COLORS = {
            'WARNING': '{{yellow}}%s{{yellow}}',
            'INFO': '**{{blue}}%s{{blue}}**',
            'DEBUG': '**{{white-blue}}%s{{white}}**',
            'CRITICAL': '**{{red}}%s{{red}}**',
            'ERROR': '**{{white-red}}%s{{white}}**'
        }

        class LogFunctions:
            LOG_START = '{{logstart}}'
            BLANK = '{{blank}}'

            def log_start(self, logger):
                    logger.info(self.LOG_START)

            def log_blank_line(self, logger):
                    logger.info(self.BLANK)

        class Formatter:
            FORMAT = ("%(asctime)s - [**%(name)s**][%(levelname)s]" " %(message)s " "(**%(filename)s**:%(lineno)d)")

            def __init__(self, use_color=False):
                self._use_color = use_color
                self._fmt_modified = False
                self._parser = MarkdownColorFormatter.Parser()
                self.log_format = self._initialize_log_format()

            def _initialize_log_format(self):
                return self._parser(self.FORMAT, not self._use_color)

            def format(self, record, fmt):
                if self._fmt_modified:
                    fmt = self._initialize_log_format()
                    self._fmt_cleared = False

                levelname = record.levelname
                msg = record.msg

                # colorize and format logname
                if self._use_color and levelname in MarkdownColorFormatter.LOG_LEVEL_COLORS:
                    record.levelname = self._parser(MarkdownColorFormatter.LOG_LEVEL_COLORS[levelname] % levelname)

                # colorize and format message...if msg is a str
                if isinstance(msg, basestring):
                    if msg.find(MarkdownColorFormatter.LogFunctions.BLANK) > -1:
                        fmt = ''
                        self._fmt_modified = True

                    elif msg.find(MarkdownColorFormatter.LogFunctions.LOG_START) > -1:
                        fmt = '%(message)s'
                        msg =           '\n\n ##########################################################\n' + \
                                        '##                                                        ##\n' + \
                                        '##               {{failed}}ALEXA LOGGING STARTING...{{failed}}                ##\n' + \
                                        '##                                                        ##\n' + \
                                        ' ##########################################################\n\n\n\n'
                        self._fmt_modified = True

                    if self._use_color:
                        # parse colors/formats TODO: fix BG
                        msg = self._parser(msg)
                    else:
                        msg = self._parser(msg, True)

                    record.msg = msg

                return record, fmt

        class _Renderer:

            def __init__(self, colors, formats):
                self.bg_colors = []

                for color in colors:
                    self.bg_colors.append('bg-' + color)

                self.colors = colors
                self.formats = formats

            def __call__(self, structure, text_only):
                self._output = []

                for output in structure:
                    attr_values = []

                    for attribute in output['attributes']:
                        if attribute in self.colors:
                            attr_values.append(MarkdownColorFormatter._COLORS[attribute.upper()] + 30)

                        elif attribute in self.bg_colors:
                            attr_values.append(MarkdownColorFormatter._COLORS[attribute.split('-')[1].upper()] + 40)

                        elif attribute in self.formats:
                            attr_values.append(MarkdownColorFormatter._FORMATS[attribute.upper()])

                        else:
                            attr_values.append('')

                    if not text_only:
                        self._output.append({
                            'seq': ';'.join(map(str, attr_values)),
                            'text': output['text']
                        })

                    else:
                        self._output.append({
                            'seq': '',
                            'text': output['text']
                        })

                return self._render(self._output)

            def _render(self, raw_out):
                out = ''

                for x in raw_out:
                    if x['seq'] == None:
                        out += x['text']

                    else:
                        out += '%s%s%s' % (MarkdownColorFormatter._ESC.SEQ % x['seq'], x['text'], MarkdownColorFormatter._ESC.RESET)

                return out

        class Parser:
            colors = ['black', 'red', 'yellow', 'green', 'blue', 'cyan', 'magenta', 'white']
            formats = ['bold', 'italics', 'reverse', 'underline', 'strikethrough']

            text = re.compile(r'^[\s\S]+?(?=[\[/_*`~{]| {2,}\n|$)')
            reverse = re.compile(r'^(`+)\s*([\s\S]*?[^`])\s*\1(?!`)')  # `reverse`
            italics = re.compile(r'^\/{2}([\s\S]+?)\/{2}(?!\/)')  # //italics//
            bold = re.compile(r'^\*{2}([\s\S]+?)\*{2}(?!\*)')  # **bold**
            underline = re.compile(r'^_{2}([\s\S]+?)_{2}(?!_)')  # __underline__
            strikethrough = re.compile(r'^\~{2}(?=\S)([\s\S]*?\S)\~{2}')  # ~~strikethrough~~

            def __init__(self):
                self.rules = self._merge_array(
                    self.formats, self.colors)

                for key, value in MarkdownColorFormatter._CUSTOM.iteritems():
                    setattr(self, key, self._custom_compile)

                for color in self.colors:
                    setattr(self, color, self._color_compile)

                self._render = MarkdownColorFormatter._Renderer(self.colors, self.formats)

            def __call__(self, text, text_only=False):
                self._output = []
                self._parsing = []
                out = self._parse(text)
                return self._render(out, text_only)

            def _merge_array(self, rules_list, color_list):
                rules_list.extend(color_list)
                rules_list.append('text')
                return rules_list

            def _color_compile(self, color):
                return re.compile(r'{{2}([\s\S]+?)}{2}([\s\S]+?){{2}%s}{2}' % (color))

            def _custom_compile(self, custom):
                return re.compile(r'{{%s}}([\s\S]+?){{%s}}' % (custom, custom))

            def _parse(self, text, levels=0, parsing=False):
                        def parse(text, levels):
                                for key in self.rules:
                                        if key in self.colors:
                                                pattern = getattr(self, key)(key)

                                        else:
                                                pattern = getattr(self, key)

                                        m = pattern.match(text)

                                        if m is not None:
                                                if not parsing:
                                                        self.parsing = []

                                                if pattern.groups > 0:  # only attributes have more than one group
                                                        levels += 1

                                                        if pattern.groups > 1:
                                                                if m.group(1).find('-') > 2: # shortest color len is 3 ('red')
                                                                        self._parsing = self._parsing + \
                                                                            [key, 'bg-' + m.group(1).split('-')[1]]

                                                                else:
                                                                        self._parsing.append(key)

                                                                self._parse(m.group(2), levels, key)

                                                        else:
                                                                self._parsing.append(key)
                                                                self._parse(m.group(1), levels, key)

                                                else:  # text only
                                                        self._output.append({'attributes': list(self._parsing), 'text': m.group(0)})

                                                return key, m

                                        else:
                                                continue

                                return False

                        while text:

				for k,v in MarkdownColorFormatter._CUSTOM.iteritems():
					pattern = getattr(self, k)(k)
					m = pattern.match(text)

					if m is not None:
						text = v % m.group(1) + text[len(m.group(0)):]

                                ret = parse(text, levels)

                                if ret is not False:
                                        key, m = ret
                                        text = text[len(m.group(0)):]
                                        self._parsing = [parsing]
                                        continue

                                if text:
                                        # catch parsing error
                                        raise RuntimeError('Infinite loop at: %s' % text)

                        return self._output


        def log_hooks(log):
            setattr(log, 'start', types.MethodType(MarkdownColorFormatter.LogFunctions().log_start, log))
            setattr(log, 'blank_line', types.MethodType(MarkdownColorFormatter.LogFunctions().log_blank_line, log))

        log_hooks = staticmethod(log_hooks)
