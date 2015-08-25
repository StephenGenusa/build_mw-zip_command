build_mwzip_command
===================

This program was written for the [PediaPress mwlib] (https://github.com/pediapress/mwlib) MediaWiki parser and utility library. It will build a complete mw-zip command to create an archive of Wikimedia files for a given topic by building a list of topic pages to any level of recursion you choose. The command:

build_mwzip_command -t "Computer networking" -l 2 -x"Unwanted category,Another unwanted category" -wbinomial,stubs

- will create the mw-zip command necessary to pull all topic and category titles for the "Computer networking" topic 
- with 2 levels of recursion 
- excluding the -x category titles "Unwanted category" and "Another unwanted category"
- excluding any category titles containing the -w skip words "binomial" and "stubs"

##Usage
<pre><code>
usage: build_mwzip_command.py [-h] -t TOPIC [-l LEVELS] [-i] [-s]
                              [-x EXCLUDECATS [EXCLUDECATS ...]]
                              [-w EXCLUDEWORDS [EXCLUDEWORDS ...]]

optional arguments:
  -h, --help            show this help message and exit
  -t TOPIC, --topic TOPIC
                        The Wikimedia page name or category name you want to
                        build an archive of
  -l LEVELS, --levels LEVELS
                        Levels of recursion to build topic page names from.
                        Default is 2
  -i, --include         Include category names in the build list. Default is
                        False.
  -s, --sort            Sort topic page names alphabetically. Default is True.
  -x EXCLUDECATS [EXCLUDECATS ...], --eXcludeCats EXCLUDECATS [EXCLUDECATS ...]
                        Category titles to exclude separated by a comma. For
                        example -x"Some title,Another Title,Finally Another"
  -w EXCLUDEWORDS [EXCLUDEWORDS ...], --excludeWords EXCLUDEWORDS [EXCLUDEWORDS ...]
                        Skip-words for excluding categories by word. For
                        example -wdating,skipjack
</code></pre>