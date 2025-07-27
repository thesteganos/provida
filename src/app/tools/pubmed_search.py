from Bio import Entrez
from typing import List, Dict, Any

from app.config.settings import settings

class PubMedSearch:
    def __init__(self):
        self.api_key = settings.entrez_api_key
        self.email = settings.entrez_email
        if not self.email:
            raise ValueError("ENTREZ_EMAIL not found in environment variables. It is required by Entrez.")
        Entrez.email = self.email
        if self.api_key:
            Entrez.api_key = self.api_key

    def search(self, query: str, retmax: int = 10) -> List[Dict[str, Any]]:
        """Searches PubMed for articles.

        Args:
            query (str): The search query.
            retmax (int): The maximum number of UIDs to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing article details.
        """
        try:
            handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax)
            record = Entrez.read(handle)
            handle.close()
            id_list = record["IdList"]

            if not id_list:
                return []

            handle = Entrez.efetch(db="pubmed", id=id_list, retmode="xml")
            articles = Entrez.read(handle)
            handle.close()

            results = []
            for article in articles['PubmedArticle']:
                medline = article['MedlineCitation']
                article_info = medline['Article']
                
                title = str(article_info.get('ArticleTitle', 'N/A'))
                abstract = 'N/A'
                if 'Abstract' in article_info and 'AbstractText' in article_info['Abstract']:
                    abstract = " ".join(article_info['Abstract']['AbstractText'])

                authors = []
                if 'AuthorList' in article_info:
                    for author in article_info['AuthorList']:
                        if 'LastName' in author and 'ForeName' in author:
                            authors.append(f"{author['LastName']} {author['ForeName']}")
                        elif 'CollectiveName' in author:
                            authors.append(author['CollectiveName'])

                journal = str(article_info.get('Journal', {}).get('Title', 'N/A'))
                pub_date = 'N/A'
                if 'Journal' in article_info and 'JournalIssue' in article_info['Journal'] and 'PubDate' in article_info['Journal']['JournalIssue']:
                    pub_date_info = article_info['Journal']['JournalIssue']['PubDate']
                    if 'Year' in pub_date_info:
                        pub_date = pub_date_info['Year']
                        if 'Month' in pub_date_info:
                            pub_date += f" {pub_date_info['Month']}"

                results.append({
                    "pmid": medline['PMID'],
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "journal": journal,
                    "pub_date": pub_date,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{medline['PMID']}/"
                })
            return results

        except Exception as e:
            print(f"Error during PubMed API call: {e}")
            return []
