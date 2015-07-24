#!/usr/bin/env python

"""
For a given Wikimedia page name or category page name, create a file
containing everything required to create a mwlib/mw-zip/mw-render
archive of Wikimedia articles.
"""

# Built-in Python Modules
from __future__ import print_function
import argparse
from cgi import escape
import codecs
import HTMLParser
import re

#3rd Party Modules
import requests


IDE_DEBUGGING = False

# Remove Templates and other "housekeeping" page names from the final list
PAGE_TYPES_TO_REMOVE = ['Template', 'Portal', 'File', 'Book']

# Make this generic so that http or other domains can easily be supported
WIKI_URL_PROTOCOL_PREFIX = 'https://'
WIKI_DOMAIN = 'en.wikipedia.org'
WIKI_BASE_URL = WIKI_URL_PROTOCOL_PREFIX + WIKI_DOMAIN + '/wiki/'


# Computer networking
categories_to_skip = ['Online services', 'Smart devices', 'Computer buses',
                      'Computer network stubs', 'Electronic waste']
category_words_to_skip = ['PlayStation 3']


def uniqifiers_f2(seq):
    """
    Remove duplicate values from the seq iterable
    From http://www.peterbe.com/plog/uniqifiers-benchmark
    """
    checked = []
    for element in seq:
        if element not in checked:
            checked.append(element)
    return checked

def parse_pages_in_category(html_content):
    """
    Slices the HTML to return only the "Pages in category" content
    """
    return html_content[html_content.find('Pages in category'): \
                        html_content.find('<noscript>')]

def parse_html_content(html_content):
    """
    Slices the HTML to return only the Mediawiki text content
    """
    return html_content[html_content.find('<div id="mw-content-text"'):
                        html_content.find('<noscript>')]

def remove_content_type(content_prefix, page_titles):
    """
    Given a content_prefix eg. 'File' remove all elements of the page_titles
    list that contain 'File:'
    """
    i = 0
    while i < len(page_titles):
        if page_titles[i].startswith(content_prefix+':'):
            del page_titles[i]
        else:
            i += 1
    return page_titles

def skipword_not_present(category_name):
    """
    Check to see if category_name contains a skipword.
    """
    for word in category_words_to_skip:
        if category_name.find(word) > -1:
            return False
    return True

def build_mw_command_from_topic(category_name, page_titles, limit_to_levels,
                                current_level, add_categories_to_list=False):
    """
    Given a category_name, build a list of page names from a page
    limit_to_levels deep. This function is called recursively until all page
    names have been acquired
    """
    # Check to see if category name does not contain a skipword or is in the
    #   category skip list
    if skipword_not_present(category_name) and \
       category_name not in categories_to_skip:
        html_parser = HTMLParser.HTMLParser()
        url = WIKI_BASE_URL + 'Category:' + escape(category_name)
        #indent = " " * (current_level-1 * 2)
        print(" " * ((current_level - 1) * 4), end="")
        #else:
        #    print
        print ("Getting topic (" + str(current_level) + "/" + \
               str(limit_to_levels) + ") \"" + category_name +"\"")
        # Get page and identify if this is a category page or topic page
        req = requests.get(url)
        if req.content.find( \
            'Wikipedia does not have a <a href="/wiki/Wikipedia:Category"') > -1:
            print ("Category name not found in this Wikipedia. " + \
                   "Checking for standalone page...")
            url = WIKI_BASE_URL + escape(category_name)
            req = requests.get(url)
            if req.content.find('The page') > -1 and \
               req.content.find('(page does not exist)') > -1:
                print ("Page name not found on this Wikipedia. Terminating...")
                exit()
        else:
            if add_categories_to_list:
                page_titles.append('Category:' + category_name)
        main_page_content = req.content
        # Get all category topics (these are page names)
        while True:
            subcontent = parse_pages_in_category(req.content)
            if not subcontent:
                subcontent = parse_html_content(req.content)
            page_titles.extend( \
                re.findall(u'<li>.{2,100}?" title="(.{2,100}?)"', subcontent))
            # Get (next page) if it exists
            if req.content.find('&amp;pagefrom=') > -1 and \
               req.content.find('(next page)') == -1:
                url = WIKI_URL_PROTOCOL_PREFIX + WIKI_DOMAIN + '/' + \
                    html_parser.unescape(re.findall( \
                    r'\(<a href="(/w/index\.php\?title=Category:.{1,100}?' + \
                    r'&amp;pagefrom=.{1,100}?)" title="Category:.{1,100}?">' + \
                    r'next page</a>\)', req.content)[0])
                req = requests.get(url)
            else:
                break
        # Get all Subcategories within the parameter limits
        if main_page_content.find('<h2>Subcategories</h2>') > -1 and \
           current_level < limit_to_levels:
            subcontent = main_page_content[ \
                main_page_content.find('<h2>Subcategories</h2>'): \
                main_page_content.find('<span id="Pages_in_category">')]
            subcats = re.findall( \
                'CategoryTreeLabelCategory" href="/wiki/Category:' + \
                '.{1,100}?">(.{1,100}?)</a>', subcontent)
            current_level += 1
            for subcat in subcats:
                build_mw_command_from_topic(
                    subcat, page_titles, limit_to_levels, current_level,
                    add_categories_to_list)
        for page_type in PAGE_TYPES_TO_REMOVE:
            page_titles = remove_content_type(page_type, page_titles)

    return page_titles


def process_topic(wiki_topic, levels_to_get, add_categories_to_list, sort_topics):
    """
    Takes a single Wiki category name OR page name as wiki_topic and processes
    that topic levels_to_get deep
    """
    print ()
    # Build the list of topics levels_to_get deep
    page_titles = build_mw_command_from_topic( \
        wiki_topic, [], levels_to_get, 1, add_categories_to_list)
    # Remove any duplicate values from the list
    page_titles = uniqifiers_f2(page_titles)
    # If sorting, grab the first element of the list, sort the rest of page
    #   names and then insert the first article back at the top of the list
    if sort_topics:
        page_title1 = page_titles.pop(0)
        page_titles.sort()
        page_titles.insert(0, page_title1)
    # Create the mw-zip script file
    outfilename = 'build_'+ wiki_topic + "_" + str(levels_to_get) + '.txt'
    outfilename = outfilename.replace(" ", "_").lower()
    outfile = codecs.open(outfilename, 'wb', 'utf-8')
    outfile.write("echo\n")
    outfile.write("echo " + str(len(page_titles)) + ' titles to retrieve:\n')
    # ***************************************************************
    # To avoid bash doing a history expand on '!' in a topic so set  +H
    outfile.write("set +H\n")
    outfile.write("mw-zip -c :en -o \"" + wiki_topic + ".zip\" ")
    for title in page_titles:
        outfile.write('"' + title.decode('utf-8') + '" ')
    outfile.write("\nset -H\n\n")
    outfile.close()
    print ("\nDone processing %s. See %s for commands" % (wiki_topic, outfilename))


def main():
    """
    main()
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-t", "--topic",
                           help="The Wikimedia page name or category name you " + \
                           "want to build an archive of",
                           required=True)
    argparser.add_argument("-l", "--levels",
                           help="Levels of recursion to build topic page names from. Default is 2",
                           type=int,
                           default=2)
    argparser.add_argument("-i", "--include",
                           help="Include category names in the build list. Default is False.",
                           action="store_true",
                           default=False)
    argparser.add_argument("-s", "--sort",
                           help="Sort topic page names alphabetically. Default is True.",
                           action="store_true",
                           default=True)
    argparser.add_argument("-x", "--eXcludeCats",
                           help="Category titles to exclude separated by a comma." + \
                           " For example -x\"Some title,Another Title,Finally Another\"",
                           nargs='+', action='store')
    argparser.add_argument("-w", "--excludeWords",
                           help="Skip-words for excluding categories by word." + \
                           " For example -wdating,skipjack",
                           nargs='+', action='store')
    if IDE_DEBUGGING:
        args = argparser.parse_args(['-l', '1', '-tComputer Networking'])
    else:
        args = argparser.parse_args()
    if args.eXcludeCats:
        categories_to_skip = args.eXcludeCats[0].split(',')
        print ("Excluding Categories", categories_to_skip)
    if args.excludeWords:
        category_words_to_skip = args.excludeWords[0].split(',')
        print ("Excluding Categories with Skipwords", category_words_to_skip)
    process_topic(wiki_topic=args.topic, levels_to_get=args.levels,
                  add_categories_to_list=args.include,
                  sort_topics=args.sort)


if __name__ == "__main__":
    main()
