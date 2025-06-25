#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to scrape popular major subjects from LinkedU.hk
and extract the article content for each subject page.

This script will:
1. Scrape all subject links from https://linkedu.hk/popular-subjects/
2. For each subject, extract detailed information from the subject page
3. Save the content in a JSON format optimized for RAG retrieval
"""

import os
import re
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinkeduSubjectScraper:
    """Class to scrape subjects and their details from LinkedU.hk website."""
    
    def __init__(self, base_url="https://linkedu.hk", 
                 subjects_url="https://linkedu.hk/popular-subjects/"):
        """Initialize the scraper with base URL and subjects page URL."""
        self.base_url = base_url
        self.subjects_url = subjects_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        })
        self.subjects = []
        self.output_directory = Path(os.path.dirname(os.path.abspath(__file__)))

    def get_soup(self, url):
        """Get BeautifulSoup object from a URL."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_subjects_from_page(self):
        """Extract all subject links from the main subjects page."""
        logger.info(f"Fetching subjects from {self.subjects_url}")
        soup = self.get_soup(self.subjects_url)
        
        if not soup:
            logger.error("Failed to fetch subjects page")
            return []
            
        # Find the dynamic list containing all subject items
        subject_list = soup.select_one('div#_dynamic_list-39-29463.oxy-dynamic-list')
        
        if not subject_list:
            logger.error("Subject list container not found")
            return []
            
        subject_items = subject_list.select('li.subject__menu-item')
        
        subjects_data = []
        for item in subject_items:
            link_element = item.select_one('a.ct-link')
            if not link_element:
                continue
                
            url = link_element.get('href', '')
            
            # Get Chinese name
            chinese_name_elem = link_element.select_one('h3.ct-headline span.ct-span')
            chinese_name = chinese_name_elem.text if chinese_name_elem else ''
            
            # Get English name
            english_name_elem = link_element.select_one('h4.ct-headline span.ct-span')
            english_name = english_name_elem.text if english_name_elem else ''
            
            if url and english_name:
                subjects_data.append({
                    'url': url,
                    'chinese_name': chinese_name,
                    'english_name': english_name
                })
                
        logger.info(f"Found {len(subjects_data)} subjects")
        return subjects_data

    def extract_article_content(self, url, subject_data):
        """Extract article content from a subject page."""
        logger.info(f"Extracting content from {url}")
        soup = self.get_soup(url)
        
        if not soup:
            logger.error(f"Failed to fetch article at {url}")
            return None
            
        # Extract article metadata and content
        article = soup.select_one('article.ct-div-block.subject-content')
        if not article:
            logger.error(f"Article content not found at {url}")
            return None
        
        # Extract last updated date
        updated_date_elem = article.select_one('.oxy-post-modified-date')
        updated_date_text = updated_date_elem.get_text(strip=True) if updated_date_elem else ''
        last_updated = ''
        
        if updated_date_text:
            # Extract date from text like "最後更新於 2024年10月10日"
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', updated_date_text)
            if date_match:
                year, month, day = date_match.groups()
                last_updated = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Extract author info
        author_name_elem = article.select_one('.post__author-name span.ct-span')
        author_name = author_name_elem.get_text(strip=True) if author_name_elem else ''
        
        author_title_elem = article.select_one('.post__author-title span.ct-span')
        author_title = author_title_elem.get_text(strip=True) if author_title_elem else ''
        
        # Extract main content
        content_elem = article.select_one('.post-content .ct-span')
        content = ''
        if content_elem:
            # Extract all text content while preserving structure
            for elem in content_elem.descendants:
                if elem.name is None and elem.strip():  # Text node
                    content += elem.strip() + ' '
                elif elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    heading_text = elem.get_text(strip=True)
                    content += f" {heading_text}. "
                elif elem.name == 'li':
                    item_text = elem.get_text(strip=True)
                    content += f" • {item_text}. "
                elif elem.name == 'p':
                    para_text = elem.get_text(strip=True)
                    if para_text:
                        content += f"{para_text} "
        
        # Extract skills section
        skills_elem = article.select_one('.subject__skill.info-wrap')
        skills_text = ''
        if skills_elem:
            skills_text = skills_elem.get_text(strip=True)
        
        # Extract requirements sections
        requirements = []
        for req_elem in article.select('.subject-requirement'):
            title_elem = req_elem.select_one('.tf-title')
            content_elem = req_elem.select_one('.info-wrap')
            
            if title_elem and content_elem:
                req_title = title_elem.get_text(strip=True)
                req_content = content_elem.get_text(strip=True)
                requirements.append({
                    'title': req_title,
                    'content': req_content
                })
        
        # Get recommended schools if available
        recommended_schools = []
        schools_section = soup.select_one('#recommendation')
        if schools_section:
            for school_card in schools_section.select('.school-card__wrap'):
                school_name_elem = school_card.select_one('.school-card__title a')
                school_desc_elem = school_card.select_one('.school-card__excerpt')
                
                if school_name_elem:
                    school_name = school_name_elem.get_text(strip=True)
                    school_url = school_name_elem.get('href', '')
                    school_desc = school_desc_elem.get_text(strip=True) if school_desc_elem else ''
                    
                    recommended_schools.append({
                        'name': school_name,
                        'url': school_url,
                        'description': school_desc
                    })
        
        # Get rankings if available
        rankings = []
        rankings_section = soup.select_one('#rankings')
        if rankings_section:
            for rank_row in rankings_section.select('.school-ranking__wrap'):
                rank_cells = rank_row.select('td')
                if len(rank_cells) >= 2:
                    rank_num = rank_cells[0].get_text(strip=True)
                    school_elem = rank_cells[1].select_one('a')
                    if school_elem:
                        school_name = school_elem.get_text(strip=True)
                        school_url = school_elem.get('href', '')
                        rankings.append({
                            'rank': rank_num,
                            'school': school_name,
                            'url': school_url
                        })
        
        # Compile subject data
        subject_data.update({
            'url': url,
            'last_updated': last_updated,
            'author': {
                'name': author_name,
                'title': author_title
            },
            'content': content.strip(),
            'skills_info': skills_text,
            'requirements': requirements,
            'recommended_schools': recommended_schools,
            'rankings': rankings,
        })
        
        return subject_data
    
    def scrape_all_subjects(self):
        """Scrape all subjects and their content."""
        subjects_list = self.extract_subjects_from_page()
        
        all_subject_data = []
        for i, subject in enumerate(subjects_list):
            logger.info(f"Processing subject {i+1}/{len(subjects_list)}: {subject['english_name']}")
            subject_data = self.extract_article_content(subject['url'], subject.copy())
            
            if subject_data:
                all_subject_data.append(subject_data)
                
            # Be nice to the server - add a short delay between requests
            if i < len(subjects_list) - 1:
                time.sleep(1)
        
        return all_subject_data

    def clean_text(self, text):
        """Clean text by removing unnecessary whitespace and newlines."""
        if not text:
            return ""
            
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove unnecessary whitespace
        text = text.strip()
        # Replace multiple line breaks with single space
        text = re.sub(r'\n+', ' ', text)
        return text

    def optimize_for_rag(self, subjects_data):
        """Optimize the subjects data for RAG retrieval."""
        optimized_data = []
        
        for subject in subjects_data:
            # Create chunks with different sections of content
            chunks = []
            
            # Basic info chunk
            basic_info = {
                'chunk_id': f"{subject['english_name'].lower().replace(' ', '_')}_basic",
                'title': f"{subject['english_name']} ({subject['chinese_name']})",
                'type': 'basic_info',
                'content': self.clean_text(f"Subject: {subject['english_name']} ({subject['chinese_name']}). Last updated: {subject['last_updated']}. Author: {subject['author']['name']}, {subject['author']['title']}")
            }
            chunks.append(basic_info)
            
            # Skills and requirements chunk
            if subject['skills_info']:
                skills = {
                    'chunk_id': f"{subject['english_name'].lower().replace(' ', '_')}_skills",
                    'title': f"{subject['english_name']} - Skills and Requirements",
                    'type': 'skills_info',
                    'content': self.clean_text(subject['skills_info'])
                }
                chunks.append(skills)
            
            # Academic requirements chunks
            for req in subject['requirements']:
                req_chunk = {
                    'chunk_id': f"{subject['english_name'].lower().replace(' ', '_')}_{req['title'].lower().replace(' ', '_').replace('（', '').replace('）', '')}",
                    'title': req['title'],
                    'type': 'requirement',
                    'content': self.clean_text(req['content'])
                }
                chunks.append(req_chunk)
            
            # Main content - split into reasonable chunks
            if subject['content']:
                # Simple chunking by paragraphs but clean text first
                clean_content = self.clean_text(subject['content'])
                # Split into sentences for more granular chunking
                sentences = re.split(r'(?<=[.!?])\s+', clean_content)
                
                current_chunk = ""
                chunk_count = 0
                
                for sentence in sentences:
                    # If adding this sentence would make the chunk too large, save current chunk
                    if len(current_chunk) + len(sentence) > 1000 and current_chunk:
                        chunk_count += 1
                        content_chunk = {
                            'chunk_id': f"{subject['english_name'].lower().replace(' ', '_')}_content_{chunk_count}",
                            'title': f"{subject['english_name']} - Content Part {chunk_count}",
                            'type': 'content',
                            'content': current_chunk.strip()
                        }
                        chunks.append(content_chunk)
                        current_chunk = sentence
                    else:
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence
                
                # Save the last chunk if there's anything left
                if current_chunk:
                    chunk_count += 1
                    content_chunk = {
                        'chunk_id': f"{subject['english_name'].lower().replace(' ', '_')}_content_{chunk_count}",
                        'title': f"{subject['english_name']} - Content Part {chunk_count}",
                        'type': 'content',
                        'content': current_chunk.strip()
                    }
                    chunks.append(content_chunk)
            
            # Recommended schools chunk
            if subject['recommended_schools']:
                schools_text = "Recommended schools: "
                for school in subject['recommended_schools']:
                    schools_text += f"{school['name']}: {self.clean_text(school['description'])}. "
                
                schools_chunk = {
                    'chunk_id': f"{subject['english_name'].lower().replace(' ', '_')}_recommended_schools",
                    'title': f"{subject['english_name']} - Recommended Schools",
                    'type': 'recommended_schools',
                    'content': schools_text.strip()
                }
                chunks.append(schools_chunk)
            
            # Rankings chunk
            if subject['rankings']:
                # Store rankings as a structured list in metadata
                rankings_list = []
                for rank in subject['rankings']:
                    rankings_list.append({
                        'rank': rank['rank'],
                        'school': rank['school'],
                        'url': rank.get('url', '')
                    })
                
                # Also create a text version for content
                rankings_text = "Subject rankings: "
                for rank in subject['rankings']:
                    rankings_text += f"#{rank['rank']}: {rank['school']}. "
                
                rankings_chunk = {
                    'chunk_id': f"{subject['english_name'].lower().replace(' ', '_')}_rankings",
                    'title': f"{subject['english_name']} - University Rankings",
                    'type': 'rankings',
                    'content': rankings_text.strip(),
                    'rankings': rankings_list  # Include structured rankings data
                }
                chunks.append(rankings_chunk)
            
            # Add metadata to all chunks
            for chunk in chunks:
                chunk.update({
                    'metadata': {
                        'subject': subject['english_name'],
                        'chinese_name': subject['chinese_name'],
                        'url': subject['url'],
                        'last_updated': subject['last_updated']
                    }
                })
            
            optimized_data.extend(chunks)
        
        return optimized_data

    def save_to_json(self, data, filename):
        """Save data to a JSON file."""
        filepath = self.output_directory / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Data saved to {filepath}")
        return str(filepath)

    def run(self):
        """Run the complete scraping process."""
        try:
            # Scrape all subjects
            subjects_data = self.scrape_all_subjects()
            
            # Save raw data
            raw_filepath = self.save_to_json(subjects_data, 'linkedu_subjects.json')
            
            # Create optimized version for RAG
            optimized_data = self.optimize_for_rag(subjects_data)
            
            # Save optimized data
            optimized_filepath = self.save_to_json(optimized_data, 'linkedu_subjects_rag_optimized.json')
            
            return {
                'raw_data': raw_filepath,
                'optimized_data': optimized_filepath,
                'subject_count': len(subjects_data)
            }
            
        except Exception as e:
            logger.error(f"Error during scraping process: {e}")
            raise

def main():
    """Main function to run the scraper."""
    scraper = LinkeduSubjectScraper()
    result = scraper.run()
    
    logger.info(f"Scraping completed successfully!")
    logger.info(f"Scraped {result['subject_count']} subjects")
    logger.info(f"Raw data saved to: {result['raw_data']}")
    logger.info(f"Optimized data saved to: {result['optimized_data']}")

if __name__ == "__main__":
    main()
