import docx
from case_lookup import case_lookup, usc_html_from_web
from docx2python import docx2python
import re
from collections import OrderedDict


class Case:

    def __init__(self, cite_text):
        t = cite_text.strip().split(" ")
        self.volume = int(t[0])
        self.first_page = int(t[-1])
        self.register = ''.join(t[1:-1])
        self.top_citations = []
        self.key = ''

        url, page_html, html_by_page, upper_page_no, case_title = case_lookup(cite_text)
        #url, page_html, html_by_page, upper_page_no, case_title = (cite_text+"url", cite_text+"page_html", ['1','2'],
        #                                                           self.first_page+20, cite_text)

        self.url = url
        self.html_by_page = html_by_page
        self.last_page = upper_page_no
        self.case_title = case_title

    def get_html_page(self, page_no):
        page_no = int(page_no)
        if page_no < self.first_page or page_no > self.last_page:
            return "bad cite"
        if page_no in self.html_by_page:
            return self.html_by_page[page_no]
        else:
            return self.html_by_page[0]


class Citation:
    def __init__(self, citation_text, pincite):
        self.citation_key = ''
        self.pincite = pincite
        self.error_list = []


def match_to_case(prefix, pincite, case_bank):
    volume = re.search(r'\d+', prefix).group()
    register = prefix.replace(volume, "", 1).replace(' ','')
    i = 0
    for case in case_bank:
        if register == case.register.replace(" ","") and int(volume) == int(case.volume):
            #TODO and if page number is in range
            return i
        i += 1

    return -1


alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|Mt)[.]"
cases = "(Id|id|App|Cal|S|Ct|So|Wash|F|Supp|A|R|D|C)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|me|edu)"


def split_into_sentences(text):
    # see https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(cases, "\\1<prd>", text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "'”" in text: text = text.replace(".'”", "'”.") # added
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace(";", ";<stop>")
    text = text.replace(")", ")<stop>") # added
    text = text.replace("(", "(<stop>") # added
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences


def read_doc(file_name):
    doc = docx.Document(file_name)
    return doc


def get_citations(doc):
    regex_strings = OrderedDict([
        (r'[0-9]+\sU[. ]*S[. ]*C[. §]*\s[0-9]+','usc'),                    # USC

        (r'[0-9]+\s[^0-9].*[^0-9]\s[0-9]+,\s[0-9]+-[0-9]+','long-range'),  # 23 cal. app. 4th 23, 23-24 #FULL
        (r'[0-9]+\s[^0-9].*[^0-9]\sat\s[0-9]+-[0-9]+','short-range'),      # 23 cal. app. 4th at 23-24
        (r'[iI]d\.\sat\s[0-9]+-[0-9]+','id-range'),                        # Id. at 23-24

        (r'[0-9]+\s[^0-9].*[^0-9]\s[0-9]+,\s[0-9]+','long'),  # 23 cal. app. 4th 23, 24 #FULL
        (r'[0-9]+\s[^0-9].*[^0-9]\sat\s[0-9]+','short'),      # 23 cal. app. 4th at 23
        (r'[0-9]+\s[^0-9].*[^0-9]\s[0-9]+','no-pin'),         # 23 cal. app. 4th 23 #FULL
        (r'Id\.\sat\s[0-9]+','id'),                           # Id. at 23
        (r'[Ii]d\.', 'id-same')])                            # Id. at 23

    case_bank = []
    all_cases = []
    active_index = -1
    active_pin = -1

    left_full = ''
    right_full = ''

    #print(doc.footnotes[0][0][0])
    for paragraph in doc.body[0][0][0]:
        input_text = paragraph
        citation_html = {} #key is index-page, value is html

        #insert footnotes into the paragraph
        match = re.findall('----footnote(\d+)----', input_text)
        if match:
            for fn in match:
                index = 2 * int(fn) + 1 # TODO more robust footnote checking
                replace_text = doc.footnotes[0][0][0][index]
                old_text = '----footnote%s----' % fn
                input_text = input_text.replace(old_text, replace_text)
        final_text = input_text


        for sentence in split_into_sentences(input_text):
            save_cite = True
            if "quoting" in sentence or "citing" in sentence:
                save_cite = False

            for regex_string in regex_strings.keys():
                found = False
                re_match = re.findall(regex_string, sentence)
                if re_match:
                    for match_text in re_match:
                        if regex_strings[regex_string] == 'usc':

                            first = re.match(r'\s*\d+', match_text).group()
                            last = re.search(r'\d+$', match_text).group()
                            page_html, start_url = usc_html_from_web(first, last)
                            key = "" + str(first) + "-usc-" + str(last)
                            if key not in citation_html:
                                page_html = str(page_html).replace('href', 'style="pointer-events: none;" href')
                                citation_html[key] = "<h4><a target='_blank' href='" + str(start_url) + "'>" \
                                                     +str(first) + " U.S. Code Section "+ str(last) + "</a></h4>" + page_html

                            # Make New Citation
                            new_cite_text = '<a href="javascript:void(0);" class="cite-link" onclick=\'citationChangeOption("' \
                                            + key \
                                            + '")\'>' + match_text \
                                            + '</a>'

                            final_text = final_text.replace(match_text, new_cite_text)
                            sentence = sentence.replace(match_text, '')
                            continue

                        if regex_strings[regex_string] in {"cal-pen", "cal-civ", "cal-bpc", "cal-evid"}:
                            pass

                        if regex_strings[regex_string] in {"fre", "frcp", "cfr"}:
                            pass

                        if regex_strings[regex_string] in {"long-range", 'long', 'no-pin'}:
                            #TODO throw a warning for multiple long
                            #TODO change to "try" and throw error for poorly formed cite

                            try:
                                if match_text.find(',') > -1 and regex_strings[regex_string] in {"long-range", 'long'}:
                                    lookup_text=match_text[0:match_text.find(',')]
                                else:
                                    lookup_text=match_text
                                case_bank.append(Case(lookup_text))
                            except:
                                pass

                        #Get pincite and prefix
                        if match_text.find(',') > -1:
                            pincite = re.search(r'\d+', match_text[match_text.find(','):]).group()
                            prefix = match_text[0:match_text.find(',')]
                            t = prefix.strip().split(" ")
                            prefix = ''.join(t[:-1])
                        elif match_text.find('at') > -1:
                            pincite = re.search(r'\d+', match_text[match_text.find('at'):]).group()
                            prefix = match_text[0:match_text.find('at')].replace(' ','')
                        elif regex_strings[regex_string] == "id-same":
                            pincite = active_pin
                        else:
                            prefix = match_text
                            t = prefix.strip().split(" ")
                            prefix = ''.join(t[:-1])
                            pincite = t[-1]

                        if save_cite:
                            active_pin = pincite

                        if regex_strings[regex_string] in {"id-range", 'id', "id-same"}:
                            case_index = active_index
                        else:
                            case_index = match_to_case(prefix, pincite, case_bank)
                            if save_cite:
                                active_case = prefix
                                active_index = case_index

                        sentence = sentence.replace(match_text, '')
                        if case_index == -1:
                            continue

                        key = "" + str(case_index) + "-" + str(pincite)
                        if key not in citation_html:
                            case = case_bank[case_index]
                            page_html = case.get_html_page(pincite)
                            citation_html[key] = "<h4><a target='_blank' href='"+str(case.url)+"'>"+case.case_title+" (page *"+pincite+")</a></h4>" + page_html

                        # Make New Citation
                        new_cite_text = '<a href="javascript:void(0);" class="cite-link" onclick=\'citationChangeOption("'\
                                        + key\
                                        + '")\'>' + match_text \
                                        + '</a>'

                        final_text = final_text.replace(match_text, new_cite_text)
                        all_cases.append(Citation(match_text, pincite))


        right_html=''
        for key, value in citation_html.items():
            div_html = '<div class="citation-divs" id="cite-'+key+'" style="display:none">'+value+'</div>'
            right_html += div_html

        left_full += '<p>'+final_text+'</p>'
        right_full += right_html

    right_full = right_full.replace("<h2>", "<h4>")
    right_full = right_full.replace("</h2>", "</h4>")
    right_full = right_full.replace('href="/scholar', 'target="_blank" href="https://scholar.google.com/scholar')
    return left_full, right_full


def main():
    file_name = 'test_doc_3.docx'
    file_name = 'test_doc_1.docx'

    doc_result = docx2python(file_name)
    left_full, right_full = get_citations(doc_result)

    #TODO strip numbers off front for cases like 1081 (N.D. Cal. 2019)
    #TODO put the paragraph loop inside so the citation numbering is good
    #TODO error check remaining bugs

    with open("left.html", "w") as text_file:
        text_file.write(left_full)
    with open("right.html", "w") as text_file:
        text_file.write(right_full)


if __name__ == '__main__':
    main()

