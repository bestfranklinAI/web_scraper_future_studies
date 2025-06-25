#!/usr/bin/env python3
"""
LinkedU Article Scraper
Scrapes articles from https://linkedu.hk/article/ and formats them for RAG
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging
from typing import List, Dict, Optional
from rag_optimizer import RAGOptimizer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LinkedUArticleScraper:
    def __init__(self):
        self.base_url = "https://linkedu.hk"
        self.articles_url = "https://linkedu.hk/article/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.articles_data = []
        
    def get_article_urls(self, max_pages: int = 14) -> List[Dict[str, str]]:
        """
        Extract article URLs from the main articles page
        Returns list of dictionaries with URL, title, excerpt, etc.
        """
        articles = []
        page = 1
        
        while page <= max_pages:
            try:
                # LinkedU uses pagination with _pager parameter
                if page == 1:
                    url = self.articles_url
                else:
                    url = f"{self.articles_url}?_pager={page}"
                
                logger.info(f"Scraping page {page}: {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find article cards using the structure you provided
                article_cards = soup.find_all('article', class_=['ct-div-block', 'post-item'])
                
                if not article_cards:
                    # Try alternative selectors
                    article_cards = soup.find_all('div', class_='post-card__wrap')
                
                if not article_cards:
                    logger.warning(f"No articles found on page {page}")
                    break
                
                page_articles = 0
                for card in article_cards:
                    article_info = self._extract_article_info_from_card(card)
                    if article_info:
                        articles.append(article_info)
                        page_articles += 1
                
                logger.info(f"Found {page_articles} articles on page {page}")
                
                if page_articles == 0:
                    break
                    
                page += 1
                time.sleep(1)  # Be respectful to the server
                
            except Exception as e:
                logger.error(f"Error scraping page {page}: {str(e)}")
                break
        
        logger.info(f"Total articles found: {len(articles)}")
        return articles
    
    def _extract_article_info_from_card(self, card) -> Optional[Dict[str, str]]:
        """
        Extract article information from a single article card
        """
        try:
            # Find the title and URL
            title_elem = card.find('h4', class_='post-card__title')
            if not title_elem:
                title_elem = card.find('a')
            
            if not title_elem:
                return None
            
            # Get the link
            link_elem = title_elem.find('a') if title_elem.name != 'a' else title_elem
            if not link_elem:
                return None
                
            url = link_elem.get('href', '')
            title = link_elem.get_text(strip=True)
            
            if not url or not title:
                return None
            
            # Make URL absolute
            if url.startswith('/'):
                url = urljoin(self.base_url, url)
            
            # Extract excerpt/description
            excerpt_elem = card.find('div', class_='post-card__excerpt')
            excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else ""
            
            # Extract categories
            categories_elem = card.find('span', class_='post-card__cat')
            categories = categories_elem.get_text(strip=True) if categories_elem else ""
            
            # Extract reading time
            reading_time_elem = card.find('div', class_='post-card__readtime')
            reading_time = reading_time_elem.get_text(strip=True) if reading_time_elem else ""
            
            # Extract author
            author_elem = card.find('span', class_='name')
            author = author_elem.get_text(strip=True) if author_elem else ""
            
            return {
                'url': url,
                'title': title,
                'excerpt': excerpt,
                'categories': categories,
                'reading_time': reading_time,
                'author': author
            }
            
        except Exception as e:
            logger.error(f"Error extracting article info: {str(e)}")
            return None
    
    def scrape_article_content(self, article_url: str) -> Optional[Dict[str, str]]:
        """
        Scrape the full content of a single article
        """
        try:
            logger.info(f"Scraping article: {article_url}")
            response = self.session.get(article_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article content - look for the main content area
            content_selectors = [
                '.ct-span.oxy-stock-content-styles',
                '.article-content',
                '.post-content',
                '.entry-content',
                'article .content',
                '[class*="content"]'
            ]
            
            content_elem = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    break
            
            if not content_elem:
                # Fallback: look for the specific span you mentioned
                content_elem = soup.find('span', id=lambda x: x and 'span-' in x, class_='ct-span')
            
            if not content_elem:
                logger.warning(f"Could not find content for {article_url}")
                return None
            
            # Clean and extract content
            content = self._clean_content(content_elem)
            
            # Extract title
            title_selectors = ['h1', '.entry-title', '.post-title', '.article-title']
            title = ""
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Extract metadata
            meta_description = ""
            meta_elem = soup.find('meta', attrs={'name': 'description'})
            if meta_elem:
                meta_description = meta_elem.get('content', '')
            
            # Extract headings for structure
            headings = []
            for heading in content_elem.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                headings.append({
                    'level': heading.name,
                    'text': heading.get_text(strip=True)
                })
            
            return {
                'title': title,
                'content': content,
                'meta_description': meta_description,
                'headings': headings,
                'url': article_url
            }
            
        except Exception as e:
            logger.error(f"Error scraping article {article_url}: {str(e)}")
            return None
    
    def _clean_content(self, content_elem) -> str:
        """
        Clean and format article content for RAG
        """
        # Remove unwanted elements
        for elem in content_elem.find_all(['script', 'style', 'nav', 'footer', 'aside']):
            elem.decompose()
        
        # Remove buttons and UI elements
        for elem in content_elem.find_all('button'):
            elem.decompose()
        
        # Remove SVG icons
        for elem in content_elem.find_all('svg'):
            elem.decompose()
        
        # Convert to text while preserving structure
        content_parts = []
        
        for elem in content_elem.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td']):
            text = elem.get_text(strip=True)
            if text and len(text) > 10:  # Filter out very short text
                # Add heading markers
                if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    content_parts.append(f"\n## {text}\n")
                elif elem.name == 'li':
                    content_parts.append(f"• {text}")
                else:
                    content_parts.append(text)
        
        return '\n\n'.join(content_parts)
    
    def scrape_all_articles(self, max_pages: int = 14, max_articles: int = None) -> List[Dict]:
        """
        Scrape all articles and return formatted JSON data
        """
        # Get article URLs
        article_urls = self.get_article_urls(max_pages)
        
        if max_articles:
            article_urls = article_urls[:max_articles]
        
        scraped_articles = []
        
        for i, article_info in enumerate(article_urls, 1):
            logger.info(f"Processing article {i}/{len(article_urls)}: {article_info['title']}")
            
            # Scrape full content
            full_content = self.scrape_article_content(article_info['url'])
            
            if full_content:
                # Combine metadata with content
                article_data = {
                    'id': f"linkedu_{i:04d}",
                    'source': 'LinkedU',
                    'source_url': article_info['url'],
                    'title': full_content['title'] or article_info['title'],
                    'excerpt': article_info['excerpt'],
                    'content': full_content['content'],
                    'meta_description': full_content['meta_description'],
                    'categories': article_info['categories'],
                    'author': article_info['author'],
                    'reading_time': article_info['reading_time'],
                    'headings': full_content['headings'],
                    'scraped_at': datetime.now().isoformat(),
                    'content_length': len(full_content['content']),
                    'language': 'zh-HK',  # Hong Kong Chinese
                    'topics': self._extract_topics(article_info['categories'])
                }
                
                scraped_articles.append(article_data)
                
            # Be respectful to the server
            time.sleep(2)
        
        return scraped_articles
    
    def _extract_topics(self, categories: str) -> List[str]:
        """
        Extract topics from categories string
        """
        if not categories:
            return []
        
        # Split by common delimiters
        topics = re.split(r'[．·,，\s]+', categories)
        return [topic.strip() for topic in topics if topic.strip()]
    
    def save_to_json(self, articles: List[Dict], filename: str = 'linkedu_articles.json', rag_optimized: bool = True):
        """
        Save articles to JSON file with optional RAG optimization
        """
        try:
            if rag_optimized:
                # Use RAG optimizer
                optimizer = RAGOptimizer()
                optimized_data = optimizer.optimize_articles_for_rag(articles)
                
                # Save RAG-optimized version
                rag_filename = filename.replace('.json', '_rag_optimized.json')
                with open(rag_filename, 'w', encoding='utf-8') as f:
                    json.dump(optimized_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Saved {len(articles)} articles (RAG optimized) to {rag_filename}")
                
                # Also save original format
                original_data = {
                    'metadata': {
                        'source': 'LinkedU Articles',
                        'scraped_at': datetime.now().isoformat(),
                        'total_articles': len(articles),
                        'scraper_version': '1.0'
                    },
                    'articles': articles
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(original_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Saved {len(articles)} articles (original) to {filename}")
                
            else:
                # Save original format only
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        'metadata': {
                            'source': 'LinkedU Articles',
                            'scraped_at': datetime.now().isoformat(),
                            'total_articles': len(articles),
                            'scraper_version': '1.0'
                        },
                        'articles': articles
                    }, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Saved {len(articles)} articles to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")

def main():
    """
    Main function to run the scraper
    """
    scraper = LinkedUArticleScraper()
    
    # Scrape articles
    print("Starting LinkedU article scraping...")
    articles = scraper.scrape_all_articles(max_pages=14, max_articles=None)  # Scrape all 14 pages
    
    if articles:
        # Save to JSON with RAG optimization
        scraper.save_to_json(articles, rag_optimized=True)
        
        # Print summary
        print(f"\nScraping completed!")
        print(f"Total articles scraped: {len(articles)}")
        print(f"Average content length: {sum(a['content_length'] for a in articles) / len(articles):.0f} characters")
        print(f"Original format saved to: linkedu_articles.json")
        print(f"RAG-optimized format saved to: linkedu_articles_rag_optimized.json")
        print(f"\n🎯 For RAG/chatbot use, use the '_rag_optimized.json' file!")
    else:
        print("No articles were scraped successfully.")

if __name__ == "__main__":
    main()
