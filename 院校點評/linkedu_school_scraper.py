#!/usr/bin/env python3
"""
LinkedU School Scraper
Scrapes school information from https://linkedu.hk/school-rank/ pages and formats them for RAG
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
import random
from urllib.parse import urljoin
from datetime import datetime
import logging
from typing import List, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LinkedUSchoolScraper:
    def __init__(self):
        self.base_url = "https://linkedu.hk"
        self.schools_url = "https://linkedu.hk/school-rank/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.schools_data = []
        # Define common keywords for better RAG content matching
        self.education_keywords = {
            'UK': ['united kingdom', 'england', 'london', 'british', 'scotland', 'wales'],
            'US': ['united states', 'america', 'california', 'new york', 'boston'],
            'AU': ['australia', 'sydney', 'melbourne', 'brisbane'],
            'CA': ['canada', 'toronto', 'vancouver', 'montreal'],
            'CN': ['china', 'hong kong', 'macau', 'beijing', 'shanghai']
        }
    
    def get_school_urls(self, max_pages: int = 10) -> List[Dict[str, str]]:
        """
        Extract school URLs from the school ranking pages
        Returns list of dictionaries with URL, name
        """
        schools = []
        
        for page in range(1, max_pages + 1):
            try:
                # LinkedU uses pagination with _pager parameter
                url = f"{self.schools_url}?_pager={page}"
                
                logger.info(f"Scraping page {page}: {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find the schools grid container
                schools_grid = soup.find('div', id='schools-grid')
                
                if not schools_grid:
                    logger.warning(f"No schools grid found on page {page}")
                    continue
                
                # Find all school cards
                school_cards = schools_grid.find_all('div', class_='school-card__wrap')
                
                if not school_cards:
                    logger.warning(f"No school cards found on page {page}")
                    continue
                
                page_schools = 0
                for card in school_cards:
                    # Find the school title and link
                    title_wrap = card.find('div', class_='school-card__title-wrap')
                    
                    if not title_wrap:
                        continue
                    
                    title_span = title_wrap.find('span', class_='ct-span')
                    
                    if not title_span:
                        continue
                    
                    link = title_span.find('a')
                    
                    if not link or not link.get('href'):
                        continue
                    
                    school_url = link.get('href')
                    school_name = link.text.strip()
                    
                    # Get school address if available
                    address = ""
                    address_elem = card.find('h3', class_='school-card__address')
                    if address_elem:
                        address_span = address_elem.find('span', class_='ct-span')
                        if address_span:
                            address = address_span.text.strip()
                    
                    # Get excerpt/description
                    excerpt = ""
                    excerpt_elem = card.find('div', class_='school-card__excerpt')
                    if excerpt_elem:
                        text_block = excerpt_elem.find('div', class_='ct-text-block')
                        if text_block:
                            span = text_block.find('span', class_='ct-span')
                            if span:
                                excerpt = span.text.strip()
                    
                    # Make URL absolute if needed
                    if school_url and not school_url.startswith('http'):
                        school_url = urljoin(self.base_url, school_url)
                    
                    # Only keep essential data for schools list
                    schools.append({
                        'name': school_name,
                        'url': school_url,
                        'address': address,
                        'excerpt': excerpt
                    })
                    
                    page_schools += 1
                    logger.info(f"Found school: {school_name}")
                
                logger.info(f"Found {page_schools} schools on page {page}")
                
                # Add a small delay to avoid overwhelming the server
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Error scraping page {page}: {str(e)}")
        
        logger.info(f"Total schools found: {len(schools)}")
        return schools
    
    def _extract_country_from_address(self, address: str) -> str:
        """
        Extract country information from school address
        """
        if not address:
            return ""
            
        # Common country indicators in addresses
        countries = {
            "UK": ["UK", "United Kingdom", "England", "Scotland", "Wales", "Northern Ireland"],
            "US": ["US", "USA", "United States", "America"],
            "CA": ["Canada", "CA"],
            "AU": ["Australia", "AU"],
            "CN": ["China", "CN", "Hong Kong", "Macau"]
        }
        
        # Check for country indicators in the address
        address_upper = address.upper()
        for country_code, indicators in countries.items():
            for indicator in indicators:
                if indicator.upper() in address_upper:
                    return country_code
        
        return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract relevant keywords from text for better RAG search
        """
        if not text:
            return []
        
        # Extract words longer than 3 characters that might be significant
        words = re.findall(r'\b\w{4,}\b', text.lower())
        
        # Filter out common words and keep only unique keywords
        stopwords = {'school', 'university', 'college', 'campus', 'student', 'students', 'education'}
        keywords = [word for word in words if word not in stopwords]
        
        # Keep only unique words and limit to 20 keywords
        unique_keywords = list(set(keywords))[:20]
        return unique_keywords
            
    def scrape_school_content(self, school_url: str) -> Optional[Dict]:
        """
        Scrape detailed information from a school page
        """
        try:
            logger.info(f"Scraping school: {school_url}")
            response = self.session.get(school_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Basic school info
            school_name = ""
            
            # Find the school name
            name_selectors = [
                'h1',
                'h1.entry-title',
                'span#span-178-5961',  # From example HTML
                '.school-content__subtitle span'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem and name_elem.text.strip():
                    school_name = name_elem.text.strip()
                    break
            
            # Extract popular subjects/features
            popular_subjects = []
            subjects_section = soup.select_one('.school-content__detail')
            if subjects_section:
                subjects_heading = subjects_section.find('h2')
                if subjects_heading and "熱門科目" in subjects_heading.text:
                    subjects_elem = subjects_section.find('div', class_='ct-text-block')
                    if subjects_elem:
                        subjects_span = subjects_elem.find('span', class_='ct-span')
                        if subjects_span:
                            # Split by <br> tags
                            for line in subjects_span.stripped_strings:
                                subject = line.strip()
                                if subject:
                                    popular_subjects.append(subject)
            
            # Extract course information
            courses = []
            accordion_items = soup.select('.oxy-pro-accordion_item')
            for item in accordion_items:
                course_title = ""
                course_content = ""
                
                title_elem = item.select_one('.oxy-pro-accordion_title')
                if title_elem:
                    course_title = title_elem.text.strip()
                
                content_elem = item.select_one('.oxy-pro-accordion_content')
                if content_elem:
                    course_content = content_elem.text.strip()
                
                # Keep both title and content for better RAG retrieval
                if course_title:
                    courses.append({
                        'title': course_title,
                        'content': course_content
                    })
            
            # Extract main content
            content = ""
            content_elem = soup.select_one('.post-content')
            if not content_elem:
                content_elem = soup.select_one('.school-content')
            
            if content_elem:
                content = self._clean_content(content_elem)
            
            # Extract school address if not already found
            address = ""
            address_elem = soup.select_one('.school-card__address')
            if address_elem:
                address = address_elem.text.strip()
            
            # Extract school website if available
            website = ""
            website_elem = soup.select_one('a[href*="http"]:not([href*="linkedu.hk"])')
            if website_elem:
                website = website_elem.get('href', '')
            
            # Compile the minimal school information needed for RAG
            school_info = {
                'name': school_name,
                'url': school_url,
                'address': address,
                'popular_subjects': popular_subjects,
                'courses': courses,
                'content': content,
                'website': website
            }
            
            return school_info
            
        except Exception as e:
            logger.error(f"Error scraping school content from {school_url}: {str(e)}")
            return None
    
    def _clean_content(self, content_elem) -> str:
        """
        Clean and format school content for RAG
        """
        # Remove unwanted elements
        for elem in content_elem.find_all(['script', 'style', 'nav', 'footer', 'aside', 'iframe']):
            elem.decompose()
        
        # Extract text while preserving structure
        content_parts = []
        
        # Process headings and paragraphs
        for elem in content_elem.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            text = elem.get_text(strip=True)
            if not text:
                continue
                
            # Format based on element type
            if elem.name.startswith('h'):
                level = int(elem.name[1])
                prefix = '#' * level
                # Use spaces instead of newlines for better JSON formatting
                content_parts.append(f"{prefix} {text}")
            elif elem.name == 'li':
                content_parts.append(f"• {text}")
            else:
                content_parts.append(text)
        
        # Join with spaces instead of newlines
        return ' '.join(content_parts)
    
    def _extract_headings(self, content: str) -> List[str]:
        """
        Extract headings from content for RAG structure
        """
        headings = []
        heading_pattern = re.compile(r'#+\s+(.+?)\s')
        
        for match in heading_pattern.finditer(content):
            headings.append(match.group(1).strip())
            
        return headings
    
    def _generate_search_variations(self, school_data: Dict) -> List[str]:
        """
        Generate search variations to improve RAG retrieval
        """
        variations = []
        
        # Add school name variations
        if school_data.get('name'):
            name = school_data['name']
            variations.append(name)
            
            # Add with country if available
            if school_data.get('country'):
                variations.append(f"{name} {school_data['country']}")
        
        # Add variations with popular subjects
        for subject in school_data.get('popular_subjects', [])[:3]:  # Limit to first 3
            if school_data.get('name'):
                variations.append(f"{school_data['name']} {subject}")
        
        # Add variations with country keywords
        country = school_data.get('country', '')
        if country and country in self.education_keywords:
            for keyword in self.education_keywords[country][:3]:  # Limit to first 3
                if school_data.get('name'):
                    variations.append(f"{school_data['name']} {keyword}")
        
        return variations[:10]  # Limit to 10 variations
    
    def scrape_all_schools(self, max_pages: int = 10, output_file: str = "院校點評/linkedu_schools.json", max_schools: int = None):
        """
        Scrape all schools and save to JSON file
        
        Args:
            max_pages: Maximum number of pages to scrape
            output_file: Path to save the JSON output
            max_schools: Maximum number of schools to scrape (for testing)
        """
        # Get all school URLs
        school_urls = self.get_school_urls(max_pages)
        
        # For testing/preview, limit to max_schools if specified
        if max_schools is not None and max_schools > 0:
            logger.info(f"Limiting to {max_schools} schools for testing")
            school_urls = school_urls[:max_schools]
        
        scraped_schools = []
        
        # Process each school
        for i, school in enumerate(school_urls, 1):
            logger.info(f"Processing school {i}/{len(school_urls)}: {school['name']}")
            
            # Prepare optimized data structure for RAG
            school_data = {
                'id': f"linkedu_school_{i:04d}",
                'name': school.get('name', ''),
                'url': school.get('url', ''),
                'country': self._extract_country_from_address(school.get('address', '')),
                'description': school.get('excerpt', '')[:300] if school.get('excerpt') else ''
            }
            
            # Scrape detailed content
            school_content = self.scrape_school_content(school['url'])
            
            if school_content:
                # Update with only RAG-essential content
                school_data.update({
                    'content': school_content.get('content', ''),
                    'popular_subjects': school_content.get('popular_subjects', []),
                    'courses': school_content.get('courses', []),
                    'website': school_content.get('website', '')
                })
            
            scraped_schools.append(school_data)
            
            # Add a delay between requests to be polite
            time.sleep(random.uniform(2, 4))
        
        # Process schools - extract key information for better RAG retrieval
        optimized_schools = []
        
        for school in scraped_schools:
            # Extract headings for better structure
            headings = self._extract_headings(school.get('content', ''))
            
            # Extract keywords from content
            keywords = self._extract_keywords(school.get('content', '') + ' ' + school.get('description', ''))
            
            # Generate search variations
            search_variations = self._generate_search_variations(school)
            
            # Create a more RAG-friendly structure with the most important information
            optimized_school = {
                'id': school['id'],
                'name': school['name'],
                'url': school['url'],
                'country': school.get('country', ''),
                'popular_subjects': school.get('popular_subjects', []),
                'description': school.get('description', ''),
                'courses': school.get('courses', []),
                'course_offerings': [c['title'] for c in school.get('courses', [])] if isinstance(school.get('courses', []), list) and all(isinstance(c, dict) for c in school.get('courses', [])) else [],
                'content': school.get('content', ''),
                'website': school.get('website', ''),
                'rag_metadata': {
                    'headings': headings,
                    'keywords': keywords,
                    'search_variations': search_variations
                }
            }
            optimized_schools.append(optimized_school)
        
        # Prepare the final data structure
        final_data = {
            'metadata': {
                'source': 'LinkedU Schools',
                'scraped_at': datetime.now().isoformat(),
                'total_schools': len(optimized_schools),
                'scraper_version': '1.1',
                'rag_optimized': True,
                'optimization_features': [
                    'Content structuring',
                    'Heading extraction',
                    'Keyword extraction',
                    'Search variations',
                    'Country identification'
                ]
            },
            'schools': optimized_schools
        }
        
        # Validate output file path
        if not output_file:
            output_file = os.path.join(os.path.dirname(__file__), "linkedu_schools_default.json")
            logger.warning(f"Empty output file path provided. Using default: {output_file}")
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(scraped_schools)} schools to {output_file}")
        return scraped_schools

def main():
    """
    Main function to run the scraper
    """
    scraper = LinkedUSchoolScraper()
    
    # Temporarily limit to 10 schools for testing
    print("Starting LinkedU school scraping (test mode with RAG optimization)...")
    # Make sure we use the full path for the output file
    output_file = os.path.join(os.path.dirname(__file__), "linkedu_schools_rag_optimized_test.json")
    schools = scraper.scrape_all_schools(
        max_pages=2,  # Just check first 2 pages 
        output_file=output_file,
        max_schools=10  # Limit to 10 schools
    )
    
    if schools:
        # Print summary
        print(f"\nScraping completed!")
        print(f"Total schools scraped: {len(schools)}")
        print(f"Saved to: {output_file}")
    else:
        print("No schools were scraped successfully.")

if __name__ == "__main__":
    main()
