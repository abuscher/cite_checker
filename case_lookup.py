import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import os.path


def cal_html_from_web(law_code, section_num):
	# Selenium Setup
	chrome_options = Options()
	chrome_options.add_argument("--headless")
	driver = webdriver.Chrome(options=chrome_options)
	# Get page
	start_url = 'https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=%s&sectionNum=%s' % (
		law_code, section_num
	)
	driver.get(start_url)
	page_html = driver.page_source.encode("utf-8")
	soup = BeautifulSoup(page_html, features="lxml")
	page_html = soup.find("div", {"id": "codeLawSectionNoHead"})
	driver.quit()
	return page_html, start_url


def usc_html_from_web(first, last):
	# Selenium Setup
	chrome_options = Options()
	chrome_options.add_argument("--headless")
	driver = webdriver.Chrome(options=chrome_options)

	# Get page
	start_url = 'https://www.law.cornell.edu/uscode/text/'+str(first)+'/'+str(last)+'/'
	driver.get(start_url)
	page_html = driver.page_source.encode("utf-8")
	soup = BeautifulSoup(page_html, features="lxml")
	page_html = soup.find("div", {"id": "tab_default_1"})
	driver.quit()
	return page_html, start_url


def fr_html_from_web(code, rule):
	# Selenium Setup
	chrome_options = Options()
	chrome_options.add_argument("--headless")
	driver = webdriver.Chrome(options=chrome_options)

	# Get page
	start_url = 'https://www.law.cornell.edu/rules/'+str(code)+'/rule_'+str(rule)+'/'
	driver.get(start_url)
	page_html = driver.page_source.encode("utf-8")
	soup = BeautifulSoup(page_html, features="lxml")
	page_html = soup.find("div", {"id": "extracted-content"})
	driver.quit()
	return page_html, start_url


def case_html_from_web(query):
	# Selenium Setup
	chrome_options = Options()
	chrome_options.add_argument("--headless")
	driver = webdriver.Chrome(options=chrome_options)

	# Initial Search
	start_url = "https://scholar.google.com/scholar?hl=en&as_sdt=2006&q="+query.replace(' ', "+")+"&btnG="
	driver.get(start_url)
	page_html = driver.page_source.encode("utf-8")

	# Parse Search Page
	soup = BeautifulSoup(page_html, features="lxml")
	div_tag = soup.find_all("div", {"class": "gs_ri"})
	tag = div_tag[0]
	td_tags = tag.find_all("a")
	tag = td_tags[0]

	# Pull first link
	start_url = "https://scholar.google.com"+str(tag['href'])
	driver.get(start_url)
	page_html = driver.page_source.encode("utf-8")
	soup = BeautifulSoup(page_html, features="lxml")
	page_html = soup.find("div", {"id": "gs_opinion"})
	driver.quit()
	return page_html, start_url


def process_page(page_html, start_url):
	# Process the Page
	page_html_str = str(page_html)
	page_links = re.findall('<a class="gsl_pagenum2" .*>\*[0-9]+<\/a>', page_html_str)
	html_split = re.split('<a class="gsl_pagenum2" .*>\*[0-9]+<\/a>', page_html_str)

	html_by_page = {}
	for i in range(len(page_links)):
		page_link = page_links[i]
		page_string = re.findall('\*[0-9]+<', page_link)[0][1:-1]
		page_no = int(page_string)
		soup = BeautifulSoup(html_split[i+1], 'html.parser')
		html_by_page[page_no] = soup.prettify()
	upper_page_no = page_no

	soup = BeautifulSoup(html_split[0], 'html.parser')
	html_by_page[0] = soup.prettify()

	case_title = soup.find("h3", {"id": "gsl_case_name"})
	case_title = str(case_title.text)

	#TODO get footnotes
	return start_url, page_html, html_by_page, upper_page_no, case_title


def save_case(file_name, page_html, start_url):
	with open(file_name, "w") as text_file:
		text_file.writelines(start_url+'\n')
		text_file.write(str(page_html))


def case_lookup(query):
	file_name = "cases/" + query.replace(" ", "-") + ".html"

	if os.path.isfile(file_name):
		with open(file_name, 'r') as file:
			start_url = file.readline()
			page_html = file.read()
	else:
		# page_html, start_url = ("<test html>", "google.com")  # html_from_web(query)
		page_html, start_url = case_html_from_web(query)
		save_case(file_name, page_html, start_url)

	return process_page(page_html, start_url)


def main():
	pass
	# query = "138 sct 2206"
	#query = "38 Cal. App. 5th 47"
	#case_lookup(query)
	#print(usc_html_from_web(18, 2703))
	#print (cal_html_from_web("PEN",'1202.4'))
	#print(cal_html_from_web("CIV", '1798.83'))

	#print(fr_html_from_web('frcp', 26))
	print(fr_html_from_web('fre', 703))

if __name__ == '__main__':
	main()
