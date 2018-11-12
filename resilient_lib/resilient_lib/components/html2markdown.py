import re
import logging
try:
    from HTMLParser import HTMLParser
except:
    from html.parser import HTMLParser

class MarkdownParser(HTMLParser):
    QUILL_RTE = "rte"       # first <div> will have this class
    MKDWN_BOLD = "**"
    MKDWN_ITALIC = "*"
    MKDWN_UNDERSCORE = "__"
    MKDWN_STRIKEOUT = "~~"

    MKDWN_LIST_BULLET = "*"
    MKDWN_LIST_SPACING = "    "

    HTML_STYLE_COLOR = r'rgb\(([\d]*)[,\s]*([\d]*)[,\s]*([\d]*)\)'

    SUPPORTED_TAGS = ["div", "span", "br", "strong", "em", "s", "u", "ol", "ul", "li", "a"]

    MARKDOWN_NEWLINE = "\n"
    MARKDOWN_NEWSECTION = "\n\n"

    def __init__(self):
        HTMLParser.__init__(self)
        self.log = logging.getLogger(__name__)

        self.buffer = []      # end markdown buffer
        self.curr_tag = []    # stack of tags to track
        self.curr_attrs = []  # stack of tag attributes to track
        self.curr_list = []   # stack of embedded ordered and unordered list symbols
        self.data = []        # buffer for a given tag, cleared when and ending tag is found (ex. </p>)
        self.data_pre = []    # markdown data to prefix the data
        self.data_post = []   # markdown data to follow the data

    def convert(self, data):
        """
        starting point for app, wrapper to htmlparser.feed
        :param data: html string
        :return: converted text to markdown
        """
        self.feed(data)
        return self.toString()

    def handle_starttag(self, tag, attrs):
        """
        handler for the start of tags. Logic is added to surround data with markdown
        :param tag:
        :param attrs:
        :return: None
        """
        #self.push_data()        # if any data is still in our data buffer, flush it

        # retain the hierarchy of nested command, which may be needed
        self.curr_tag.append(tag)
        self.curr_attrs.append(attrs)

        if tag == "div":
            pass
        elif tag == "span":
            pass
        elif tag == "strong":
            self.data_pre.append(MarkdownParser.MKDWN_BOLD)
            self.data_post.insert(0, MarkdownParser.MKDWN_BOLD)
        elif tag == "em":
            self.data_pre.append(MarkdownParser.MKDWN_ITALIC)
            self.data_post.insert(0, MarkdownParser.MKDWN_ITALIC)
        elif tag == "s":
            self.data_pre.append(MarkdownParser.MKDWN_STRIKEOUT)
            self.data_post.insert(0, MarkdownParser.MKDWN_STRIKEOUT)
        elif tag == "u":
            self.data_pre.append(MarkdownParser.MKDWN_UNDERSCORE)
            self.data_post.insert(0, MarkdownParser.MKDWN_UNDERSCORE)
        elif tag == "ol":
            self.curr_list.append(0)  # number to be increments with every <li>
        elif tag == "ul":
            self.curr_list.append(MarkdownParser.MKDWN_LIST_BULLET)  # unordered lists are all "*"
        elif tag == "li":
            # add proper # of spaces
            self.data_pre.append(MarkdownParser.MARKDOWN_NEWLINE)
            self.data_pre.append(MarkdownParser.MKDWN_LIST_SPACING * len(self.curr_list))
            if self.curr_list[-1] == MarkdownParser.MKDWN_LIST_BULLET:
                self.data_pre.append('{} '.format(MarkdownParser.MKDWN_LIST_BULLET))
            else:
                num = self.curr_list.pop()
                num = num+1
                self.curr_list.append(num)
                self.data_pre.append("{}. ".format(num))

        elif tag == "br":
            pass
        elif tag == "a":
            href = self.get_attr(attrs, 'href')
            self.data_pre.extend(["[{}]".format(href), '('])
            self.data_post.insert(0, ")")
        elif tag not in MarkdownParser.SUPPORTED_TAGS:
            self.log.warning("Unknown html tag: {}".format(tag))
            self.data_post.insert(0, MarkdownParser.MARKDOWN_NEWSECTION)


        # determine if styling is needed
        style = self.get_attr(attrs, 'style')
        if style:
            rgb = self.get_style_attr(style, 'color')
            if rgb:
                rgb_hex = self.convert_rgb(self.get_rgb(rgb))
                self.data_pre.append("{{color:{0}}}".format(rgb_hex))
                self.data_post.insert(0, "{color}")

            # format monospace data blocks
            font_family = self.get_style_attr(style, 'font-family')
            if font_family and font_family == "monospace":
                self.data_pre.append("{{")
                self.data_post.insert(0, "}}")

        self.log.debug(self.data_pre)


    def handle_endtag(self, tag):
        """
        handler for end tags.
        :param tag:
        :return: None
        """

        prev_tag = None
        prev_attrs = None
        if len(self.curr_tag) == 0 or self.curr_tag[-1] != tag:
            raise ValueError("Mismatch tag {} expecting {}".format(tag, prev_tag))

        self.curr_tag.pop()
        prev_attrs = self.curr_attrs.pop()

        if tag == "div":
            cls = self.get_attr(prev_attrs, 'class')
            # don't need extra line breaks when parsing the enclosing <div> tag
            if cls and cls == MarkdownParser.QUILL_RTE:
                self.data_post.append(MarkdownParser.MARKDOWN_NEWLINE)
            else:
                self.data_post.append(MarkdownParser.MARKDOWN_NEWSECTION)

        elif tag in ("ol", "ul"):
            if len(self.curr_list) > 0:
                self.curr_list.pop()        # clear top item on list symbols
            self.data_post.insert(0, MarkdownParser.MARKDOWN_NEWLINE)
        elif tag == "br":
            self.data_post.insert(0, MarkdownParser.MARKDOWN_NEWSECTION)

        self.push_data()

    def handle_data(self, data):
        """
        data handler. Basically, add tagged data to the growing buffer
        :param data:
        :return: None
        """
        # clean data of prefix whitespace
        cleaned = re.search(r"^[\n\t\r]*(.*)", data)
        cleaned and self.data.append(cleaned.group(1))

    def push_data(self):
        """
        flush the data buffer and reset for next html tag
        :return: None
        """

        # only push buffers if there's data. pre and post data alone is not pushed
        #  this avoids excessive newlines when nesting <div>
        if len(''.join(self.data)) > 0:
            self.buffer.extend([item for sublist in [self.data_pre, self.data, self.data_post] for item in sublist])

        # clean up
        self.data = []
        self.data_pre = []
        self.data_post = []


    def convert_rgb(self, rgb):
        """
        convert rgb values to hexcode format
        :param rgb:
        :return:
        """
        return '#'+''.join('%02x'% int(i) for i in rgb)


    def get_attr(self, attrs, key):
        """
        get an attribute from the data's previous block
        ex. <div style='font-family: monospace'>zzz</div>
        :param attrs:
        :param key:
        :return: found attribute or None
        """
        for attr in attrs:
            if attr[0] == key:
                return attr[1]

        return None

    def get_style_attr(self, style, key):
        """
        find css data within the style attribute
        :param style:
        :param key: css label
        :return: css data
        """
        for attr in style.split(';'):
            attr_split = attr.split(':')
            if attr_split[0].strip() == key:
                return attr_split[1].strip()

        return None

    def get_rgb(self, str):
        """
        format of rgb information is "rgb(rrr, ggg, bbb)"
        :param str:
        :return: list of values
        """
        m = re.search(MarkdownParser.HTML_STYLE_COLOR,  str)
        return m.group(1, 2, 3) if m else None

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()

    def toString(self):
        """
        we're done. flush the data buffer and print entire content
        :return: markdown result
        """
        self.push_data()

        return ''.join(self.buffer)
