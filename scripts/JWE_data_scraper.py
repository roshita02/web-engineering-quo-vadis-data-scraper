import requests
import csv
from dotenv import load_dotenv
import os
import uuid

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


publication_title="Journal of Web Engineering"
issn="1544-5976"
ieee_api_key = os.environ.get('IEEE_API_KEY')
ieee_api_url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
csv_header = [
                ["Venue", "Year", "Title", "Author", "Affiliation", "Country", "Author Keywords", "IEEE Keywords", "Volume Number", "Issue", "Issue Identifier", "Citation count" , "URL", "Page number", "Abstract"]
            ]
max_records=200

# Load environment variables from .env file
load_dotenv()

def get_journal_publication_data(record_data):
    year = record_data["publication_year"]
    # Get author name
    authornames = []
    affiliations = []
    countries = []
    for author in record_data["authors"]["authors"]:
        authornames.append(author["full_name"])
        affiliations.append(author["affiliation"])
        country = get_country_from_address(author["affiliation"])
        if country not in countries:
            countries.append(country)

    country_names = " | ".join(countries)

    authornames = " | ".join(authornames)
    affiliations = " | ".join(affiliations)

    # Get title
    title = record_data["title"]

    # Get Keywords
    index_terms = record_data["index_terms"] if 'index_terms' in record_data else ""
    author_keywords = " | ".join(index_terms["author_terms"]["terms"]) if 'author_terms' in index_terms else ""
    ieee_keywords = " | ".join(index_terms["ieee_terms"]["terms"]) if 'ieee_terms' in index_terms else ""


    # Get URL of publication
    url = record_data["html_url"] if 'html_url' in record_data else ""

    # Get abstract
    abstract = record_data["abstract"] if 'abstract' in record_data else ""

    doi = record_data["doi"] if 'doi' in record_data else ""
    citation_count = get_citation_count(doi)
    volume_number = record_data["volume"]
    issue = record_data["issue"]
    issue_number = record_data["is_number"]
    page_number = f"{record_data['start_page']}-{record_data['end_page']}"


    return ['JWE', year, title, authornames, affiliations, country_names, author_keywords, ieee_keywords, volume_number, issue, issue_number, citation_count, url, page_number, abstract]
        

def scrape_journal_publications(url):
    # Send an HTTP request to the URL
    response = requests.get(url)
    # Check if the request was successful (status code 200)
    data = []
    if response.status_code == 200:
        js = response.json()
        print("------------------------------------------------------------------------------------------------")
        # export data in a csv
        articles = js["articles"]
        for article in articles:
            pub_data = get_journal_publication_data(article)
            data.append(pub_data)
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
    return data



with open(f"JWE_scraped_data_{generate_random_code()}.csv", 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerows(csv_header)
    for year in YEARS:
        scraped_data = []
        print(f"Scraping publications from Year: {year}")
        url_to_scrape = f"{ieee_api_url}?publication_title={publication_title}&issn={issn}&publication_year={year}&apikey={ieee_api_key}&max_records={max_records}"
        
        scraped_data = scrape_journal_publications(url_to_scrape)

        # Writing multiple rows at once
        csv_writer.writerows(scraped_data)

print(f'--------------Data has been written----------------------------')












