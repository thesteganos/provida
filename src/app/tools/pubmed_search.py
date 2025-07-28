from Bio import Entrez
import asyncio
import logging
from typing import List, Dict, Any

from src.app.config.settings import settings

logger = logging.getLogger(__name__)

class PubMedSearch:
    def __init__(self):
        self.api_key = os.getenv("ENTREZ_API_KEY")
        self.email = os.getenv("ENTREZ_EMAIL")

        if not self.api_key:
            logger.error("ENTREZ_API_KEY não encontrada nas variáveis de ambiente. É necessária para Entrez.")
            raise ValueError("ENTREZ_API_KEY não encontrada nas variáveis de ambiente. É necessária para Entrez.")
        if not self.email:
            logger.error("ENTREZ_EMAIL não encontrado nas variáveis de ambiente. É necessário para Entrez.")
            raise ValueError("ENTREZ_EMAIL não encontrado nas variáveis de ambiente. É necessário para Entrez.")

        Entrez.api_key = self.api_key
        Entrez.email = self.email

    async def search(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """Searches PubMed for articles asynchronously.

        Args:
            query (str): The search query.
            count (int): The maximum number of UIDs to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing article details.
        """
        logger.info(f"Iniciando busca no PubMed para: '{query}' (count: {count})")
        try:
            # Envolver chamadas síncronas em asyncio.to_thread para não bloquear o loop de eventos
            handle = await asyncio.to_thread(Entrez.esearch, db="pubmed", term=query, retmax=count)
            record = await asyncio.to_thread(Entrez.read, handle)
            await asyncio.to_thread(handle.close)
            id_list = record["IdList"]

            if not id_list:
                logger.info(f"Nenhum resultado encontrado no PubMed para: '{query}'")
                return []

            handle = await asyncio.to_thread(Entrez.efetch, db="pubmed", id=id_list, retmode="xml")
            articles = await asyncio.to_thread(Entrez.read, handle)
            await asyncio.to_thread(handle.close)

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
            logger.info(f"Busca no PubMed concluída para: '{query}'. Resultados: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"Erro durante a chamada à API do PubMed para '{query}': {e}", exc_info=True)
            return []