import requests
from bs4 import BeautifulSoup
import csv
import os
import uuid

# This is an example of web scraping using Beautiful Soup

csv_header = [
            ["Venue", "Year", "Title", "Author", "Affiliation", "Country", "Name of Track/Workshop", "Keywords", "Citation count", "URL", "Page number", "Abstract"]
        ]

YEARS = ["2019", "2020", "2021", "2022", "2023"]
google_scholar_api_url = "https://serpapi.com/search.json?engine=google_scholar&"
google_scholar_api_key = os.environ.get('SERP_API_KEY')

def generate_random_code():
    # Generate a random UUID (Universally Unique Identifier)
    random_code = uuid.uuid4()
    
    # Convert UUID to a string without hyphens
    random_code_str = str(random_code).replace('-', '')
    
    return random_code_str

def get_country_from_address(address):
    country = address.split(",")[-1].strip()
    return country

def get_citation_count(doi):
    if doi:
        url = f"{google_scholar_api_url}&q={doi}&api_key={google_scholar_api_key}"
        response = requests.get(url)
        citation_count = 0
        if response.status_code == 200:
            response = response.json()
            if response["organic_results"] :
                record = response["organic_results"][0]
                try:
                    citation_count = record["inline_links"]["cited_by"]["total"]
                except Exception as e:
                    return 0
        return citation_count
    return 0

def get_paper_data_content(data, url):
    paper_url = f"https://link.springer.com{url}"
    paper_link_res = requests.get(paper_url)
    if paper_link_res.status_code == 200:
        paper_html_content = BeautifulSoup(paper_link_res.text, 'html.parser')
        abstract_html_content = paper_html_content.find('section', attrs={'data-title': 'Abstract'})
        if abstract_html_content:
            abstract = abstract_html_content.find('p').text.strip()

        # Find affiliations
        affiliation_section_html_content = paper_html_content.find('ol', class_='c-article-author-affiliation__list')
        affiliation_list_html_content = affiliation_section_html_content.find_all('p', class_='c-article-author-affiliation__address')

        affiliations = []
        countries = []
        for affiliation_html in affiliation_list_html_content:
            affiliation = affiliation_html.text.strip()
            affiliations.append(affiliation)

            # Find country
            country = get_country_from_address(affiliation)
            if country:
                if country not in countries:
                    countries.append(country)

        # Find keywords
        keywords_section = paper_html_content.find_all('li', class_='c-article-subject-list__subject')
        keywords = []
        for keyword in keywords_section:
            keyword_html = keyword.find('span')
            keywords.append(keyword_html.text.strip())
        
        # Find citation count
        doi = url.strip('/chapter/')
        citation_count = 0
        if doi:
            citation_count = get_citation_count(doi)

        data["URL"] = paper_url
        data["Affiliation"] = ' | '.join(affiliations)
        data["Country"] = ' | '.join(countries) if countries else ""
        data["Keywords"] = ' | '.join(keywords)
        data["Abstract"] = abstract
        data["Citation count"] = citation_count
        return data



def get_conference_book_content(data, year, url):
    # Goto the link and start scraping data
    conf_link_response = requests.get(f"https://link.springer.com{url}")
    if conf_link_response.status_code == 200:
        conf_html_content = BeautifulSoup(conf_link_response.text, 'html.parser')

        # Get titles
        papers_list_section = conf_html_content.find('section', attrs={'data-title': 'book-toc'})

        papers_list_group_section = papers_list_section.find_all('li', class_='c-card c-card--flush c-list-group__item')
        for paper_list_group_item in papers_list_group_section:
            paper_group_title = paper_list_group_item.find('h3', attrs={'data-title': 'part-title'})
            papers_list = paper_list_group_item.find_all('li', attrs={'data-test': 'chapter'})
            for paper in papers_list:
                title_card = paper.find('h4', class_='c-card__title')
                if title_card:
                    title_link = title_card.find('a')
                    if title_link:
                        title = title_link.text.strip()
                        title_link_url = title_link.get('href')

                        # Find author names
                        auth_html_content = paper.find('li', class_='c-author-list__item')
                        if auth_html_content:
                            authors = auth_html_content.text.strip()
                        ## Find the number of pages

                        # Find page numbers
                        pageno_html_content = paper.find('span', attrs={'data-test': 'page-number'})
                        page_numbers = pageno_html_content.text.strip('Pages')

                        ## Build data
                        pub_data = {
                            'Venue': 'ICWE',
                            'Year': year,
                            'Title': title,
                            'Author': authors,
                            'Page number': page_numbers,
                            'Name of track/workshop': paper_group_title.text.strip()
                        }
                        pub_data = get_paper_data_content(pub_data, title_link_url)
                        data.append([pub_data['Venue'], pub_data['Year'], pub_data['Title'], pub_data['Author'], pub_data['Affiliation'], pub_data['Country'], pub_data['Name of track/workshop'], pub_data['Keywords'], pub_data['Citation count'], pub_data['URL'], pub_data['Page number'], pub_data['Abstract']])

                        #csv_writer.writerows([pub_data['Venue'], pub_data['Year'], pub_data['Title'], pub_data['Author'], pub_data['Affiliation'], pub_data['Country'],pub_data['Keywords'], pub_data['Citation count'], pub_data['URL'], pub_data['Page number'], pub_data['Abstract']])

        # // Get content from next page
        next_page = conf_html_content.find('a', class_='c-pagination__link', attrs={'data-test': 'next-page'})
        if next_page:
            next_page_link = next_page.get('href')
            if next_page_link:
                print(f"Next page link is: {next_page_link}")
                get_conference_book_content(data, year, next_page_link)

        
        return data
        
    else:
        print("failed")



def scrape_parent_link(parent_url):
    response = requests.get(parent_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        timeline_ol = soup.find('ol', class_='app-conference-series-timeline')
        scraped_data = []
        if timeline_ol:
            #loop over <li> elements
            lis = timeline_ol.find_all('li', class_='app-conference-series-timeline__year')
            
            with open(f"icwe_conference_data_{generate_random_code}.csv", 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerows(csv_header)
            
                for li in lis:
                    if li:
                        year = li.find('span', class_='app-conference-series-timeline__marker').text.strip()
                        if year in YEARS:
                            conference_series = li.find('ul', class_='app-conference-series-timeline__list')
                            if conference_series:
                                timeline_items = conference_series.find_all('li', class_='app-conference-series-timeline__item')
                                for timeline_item in timeline_items:
                                    title = timeline_item.find('a', class_='u-serif')
                                    print(f"Title is: {title.text.strip()} for year {year}")    

                                    # Find link
                                    book_link_for_year = title.get('href')
                                    scraped_data = get_conference_book_content([], year, book_link_for_year)
                                    csv_writer.writerows(scraped_data)
                        else:
                            break
                
            print(f'--------------Data has been written----------------------------')
    else:
        print(f"Failed to retrieve the parent page. Status code: {response.status_code}")

# Example usage
icwe_url = "https://link.springer.com/conference/icwe"
scrape_parent_link("https://link.springer.com/conference/icwe")





