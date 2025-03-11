import unittest
from resilient_lib.components.html2markdown import MarkdownParser

class TestFunctionMetrics(unittest.TestCase):
    """ Tests for the attachment_hash function"""

    def test_no_html(self):

        parser = MarkdownParser()
        data =  """The General Preferences Pane allows you to tell me how you want me to behave. 
For example, do you want me to make sure there is a document open when I launch?
You can also tell me if I should constantly update the preview window as you type, or wait for you to hit command-R instead.
Maybe you prefer your editor window on the right? Or to see the word-count as you type. 
This is also the place to tell me if you are interested in pre-releases of me, or just want to stick to better-tested official releases."""

        converted = parser.convert(data)
        self.assertEqual(converted, data)

    def test_paragraph(self):
        data = """<div class="rte"><div>this is line 1</div><div>this is line 2</div><div>this is line 3</div></div>"""
        markdown = "this is line 1\nthis is line 2\nthis is line 3"

        parser = MarkdownParser()
        converted= parser.convert(data)
        self.assertEqual(converted, markdown)

    def test_blockquote(self):
        data = """<div class="rte"><blockquote>this is line 1
this is line 2
this is line 3</blockquote></div>"""
        markdown = "```this is line 1\nthis is line 2\nthis is line 3```"

        parser = MarkdownParser()
        converted= parser.convert(data)
        self.assertEqual(converted, markdown)

    def test_anchor(self):
        parser = MarkdownParser()
        data = """<div>
<a href="https://ibm/biz/resilientcommunity" target="_blank">anchor</a>
</div>"""
        data_monospace = """<div style="text-align: justify;">
<a href="https://ibm/biz/resilientcommunity" style="font-size: 10.0px;font-family: monospace;" target="_blank">anchor</a>
</div>"""
        markdown="[https://ibm/biz/resilientcommunity](anchor)"
        markdown_monospace="[https://ibm/biz/resilientcommunity]({{anchor}})"
        converted = parser.convert(data)
        self.assertEqual(converted, markdown)

        parser_monospace = MarkdownParser()
        converted_monospace = parser_monospace.convert(data_monospace)
        self.assertEqual(converted_monospace, markdown_monospace)

    def test_strong_emphasis_underline_strikeout(self):
        data = """<div><strong>bold</strong><span> </span><em>italic</em><span> </span><u>underline</u><span> </span><s>strikeout</s></div>"""
        markdown = "**bold** *italic* __underline__ ~~strikeout~~"

        parser = MarkdownParser()
        converted = parser.convert(data)
        self.assertEqual(converted, markdown)

    def test_underline_and_emphasis(self):
        data = "<div class='rte'><div><strong><u>underline and strong</u></strong></div></div>"
        markdown = "**__underline and strong__**"

        parser = MarkdownParser()
        converted = parser.convert(data)
        self.assertEqual(converted, markdown)

        data = "<div class='rte'><div style='font-family: monospace; color: rgb(0, 255, 0)'><strong><u>underline and strong</u></strong></div></div>"
        markdown = "{color:#00ff00}{{**__underline and strong__**}}{color}"

        parser = MarkdownParser()
        converted = parser.convert(data)
        self.assertEqual(converted, markdown)

    def test_color(self):
        data = """<div class='rte'><span style="color: rgb(255,0,0);">this is red</span></div>"""
        markdown = "{color:#ff0000}this is red{color}"

        parser = MarkdownParser()
        converted = parser.convert(data)
        self.assertEqual(converted, markdown)

        # same test but using str() which calls __str__()
        self.assertEqual(str(parser), markdown)

    def test_h(self):
        data = """<div><h1>this is a header</h1><strong>strong</strong></div>"""
        markdown = "h1. this is a header\n**strong**"

        parser = MarkdownParser()
        parser.convert(data)
        self.assertEqual(str(parser), markdown)

        data = """<div><h1>this is a header</h1><h2>h2</h2></div>"""
        markdown = "* this is a header\n** h2"

        parser = MarkdownParser(headers=['*', '**', '***'])
        parser.convert(data)
        self.assertEqual(str(parser), markdown)

    def test_unknown(self):
        data = """<div><x>this is a header</x><strong>strong</strong></div>"""
        markdown = "this is a header\n**strong**"

        parser = MarkdownParser()
        parser.convert(data)
        self.assertEqual(str(parser), markdown)

    def test_mismatch_tag(self):
        data = """<div><h1>this is a header</h1><strong>strong</strong></xx>"""

        parser = MarkdownParser()

        with self.assertRaises(ValueError):
            parser.convert(data)

    def test_missing_tag(self):
        data = """<div><h1>this is a header</h1><strong>strong</div>"""

        parser = MarkdownParser()

        with self.assertRaises(ValueError):
            parser.convert(data)


    def test_lists(self):
        data_ordered = """<div><ol><li>1</li><li>2</li><li>3</li></ol></div>"""
        markdown_ordered = """
    1. 1
    2. 2
    3. 3"""

        data_unordered = """<div><ul><li>1</li><li>2</li><li>3</li></ul></div>"""
        markdown_unordered = """
    * 1
    * 2
    * 3"""

        data_nested_ol_ol = """<div><ol><li>1</li><li>2</li><li>3</li><ol><li>31</li><li>32</li><li>33</li></ol><li>4</li></ol></div>"""
        markdown_ol_ol = """
    1. 1
    2. 2
    3. 3
        1. 31
        2. 32
        3. 33
    4. 4"""

        data_nested_ul_ol = """<div><ul><li>1</li><li>2</li><li>3</li><ol><li>31</li><li>32</li><li>33</li></ol><li>4</li></ul></div>"""
        markdown_ul_ol = """
    * 1
    * 2
    * 3
        1. 31
        2. 32
        3. 33
    * 4"""

        data_nested_ul_ul = """<div><ul><li>1</li><li>2</li><li>3</li><ul><li>31</li><li>32</li><li>33</li></ul><li>4</li></ul></div>"""
        markdown_ul_ul = """
    * 1
    * 2
    * 3
        * 31
        * 32
        * 33
    * 4"""

        data_nested_ol_ul = """<div><ol><li>1</li><li>2</li><li>3</li><ul><li>31</li><li>32</li><li>33</li></ul><li>4</li></ol></div>"""
        markdown_ol_ul = """
    1. 1
    2. 2
    3. 3
        * 31
        * 32
        * 33
    4. 4"""

        data_nested_ol_ul_ol = """<div class="rte"><ol><li>1</li><li>2</li><li>3</li></ol><ul><ul><li>a</li><li>b</li><li>c</li></ul></ul><ol><ol><ol><li>i</li><li>ii</li><li>iii</li></ol></ol></ol></div>"""
        markdown_ol_ul_ol = """
    1. 1
    2. 2
    3. 3
        * a
        * b
        * c
            1. i
            2. ii
            3. iii"""

        parser = MarkdownParser()
        converted_ordered = parser.convert(data_ordered)
        self.assertEqual(converted_ordered, markdown_ordered)

        parser = MarkdownParser()
        converted_unordered = parser.convert(data_unordered)
        self.assertEqual(converted_unordered, markdown_unordered)

        parser = MarkdownParser()
        converted_ol_ol = parser.convert(data_nested_ol_ol)
        self.assertEqual(converted_ol_ol, markdown_ol_ol)

        parser = MarkdownParser()
        converted_ul_ol = parser.convert(data_nested_ul_ol)
        self.assertEqual(converted_ul_ol, markdown_ul_ol)

        parser = MarkdownParser()
        converted_ul_ul = parser.convert(data_nested_ul_ul)
        self.assertEqual(converted_ul_ul, markdown_ul_ul)

        parser = MarkdownParser()
        converted_ol_ul = parser.convert(data_nested_ol_ul)
        self.assertEqual(converted_ol_ul, markdown_ol_ul)

        parser = MarkdownParser()
        converted_ol_ul_ol = parser.convert(data_nested_ol_ul_ol)
        self.assertEqual(converted_ol_ul_ol, markdown_ol_ul_ol)

        data_custom = """<div class="rte"><ul><li>1</li><li>2</li><li>3</li></ul><ul><ul><li>a</li><li>b</li><li>c</li></ul></ul><ul><ul><ul><li>i</li><li>ii</li><li>iii</li></ul></ul></ul></div>"""
        markdown_custom = """
    * 1
    * 2
    * 3
        + a
        + b
        + c
            - i
            - ii
            - iii"""

        parser = MarkdownParser(bullets=["*", "+", "-"])
        converted_custom = parser.convert(data_custom)
        self.assertEqual(converted_custom, markdown_custom)

        markdown_custom_single = """
* 1
* 2
* 3
* a
* b
* c
* i
* ii
* iii"""

        parser = MarkdownParser(bullets="*", indent=0)
        converted_custom = parser.convert(data_custom)
        self.assertEqual(converted_custom, markdown_custom_single)

    def test_end_list(self):
        data = u'<div class="rte"><div><strong>rich text</strong></div><div><br /></div><ol><li>111</li><li>2222</li><li>333</li><li>444</li></ol><div>normal</div></div>'
        data_result = "**rich text**\n\n\n\n\n    1. 111\n    2. 2222\n    3. 333\n    4. 444\n\nnormal"

        parser = MarkdownParser()
        converted_custom = parser.convert(data)
        self.assertEqual(converted_custom, data_result)

    def test_modify_symbols(self):
        data = "<div class='rte'><div><strong><u>underline and strong</u></strong></div></div>"
        markdown = "*_underline and strong_*"

        parser = MarkdownParser(bold="*", underline="_")
        converted = parser.convert(data)
        self.assertEqual(converted, markdown)

        data_unordered = """<div><ul><li>1</li><li>2</li><li>3</li></ul></div>"""
        markdown_unordered = """
  + 1
  + 2
  + 3"""

        parser = MarkdownParser(indent=2, bullets='+')
        converted_unordered = parser.convert(data_unordered)
        self.assertEqual(converted_unordered, markdown_unordered)

        data_ordered = """<div><ol><li>1</li><li>2</li><li>3</li></ol></div>"""
        markdown_ordered = """
    # 1
    # 2
    # 3"""

        parser = MarkdownParser(number='#')
        converted_ordered = parser.convert(data_ordered)
        self.assertEqual(converted_ordered, markdown_ordered)

    def test_monospace(self):
        data = """<div class="rte"><div><strong style="font-family: monospace;">monospace</strong><strong> and bold</strong></div><div><u>underline</u></div><div><strong><u>bold and underline</u></strong></div><div><br /></div></div>"""
        markdown_monospace = """**{{monospace}}**** and bold**\n__underline__\n**__bold and underline__**"""

        parser = MarkdownParser(number='#')
        converted_monospace = parser.convert(data)
        self.assertEqual(converted_monospace, markdown_monospace)

    def test_mixed(self):
        data = """<div class="rte"><div>this is a line with <strong>bold</strong> and <span style="color: rgb(255,0,0);">red</span></div></div>"""
        markdown_mixed="""this is a line with **bold** and {color:#ff0000}red{color}"""

        parser = MarkdownParser()
        converted_mixed = parser.convert(data)
        self.assertEqual(converted_mixed, markdown_mixed)

    def test_nested(self):
        data = """<div class="rte"><ol><li>111</li><li>222<ol><li>aaa</li><li>bbb</li></ol></li><li>333</li></ol></div>"""
        markdown = "\n    1. 111\n    2. 222\n        1. aaa\n        2. bbb\n    3. 333"

        parser = MarkdownParser(bullets=["*", "+", "-"])
        converted_mixed = parser.convert(data)
        self.assertEqual(converted_mixed, markdown)
