
Python libraries for cite checking legal documents

case_lookup.py:
-takes as input a search query and returns the case text as HTML
-WARNING: this is for demonstration purposes only, do not use this carelessly. This uses selenium to grab html from Google Scholar. Google Scholar is not meant to be scraped and Google will lock you out if you overuse/abuse this tool.

word_doc.py:
- Takes a word document file name as input (see test_doc_1.docx and test_doc_2.docx).
- Outputs two HTML files: left.html is the original text marked up with links. and right.html.
- See examples at https://austinbuscher.com/citechecker/

