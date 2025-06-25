#!/usr/bin/env python3
"""
RAG Optimizer for Existing Linkedu School Data
Converts existing school JSON data to RAG-optimized format
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchoolRAGOptimizer:
    def __init__(self):
        # Define common keywords for better RAG content matching
        self.education_keywords = {
            'UK': ['united kingdom', 'england', 'london', 'british', 'scotland', 'wales'],
            'US': ['united states', 'america', 'california', 'new york', 'boston'],
            'AU': ['australia', 'sydney', 'melbourne', 'brisbane'],
            'CA': ['canada', 'toronto', 'vancouver', 'montreal'],
            'CN': ['china', 'hong kong', 'macau', 'beijing', 'shanghai']
        }
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing newlines and excessive whitespace for better JSON formatting
        """
        if not text:
            return ""
            
        # Replace newlines with spaces
        text = re.sub(r'\n+', ' ', text)
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
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
        
        # Clean the text first to ensure proper extraction
        cleaned_text = self._clean_text(text)
        
        # Extract words longer than 3 characters that might be significant
        words = re.findall(r'\b\w{4,}\b', cleaned_text.lower())
        
        # Filter out common words and keep only unique keywords
        stopwords = {'school', 'university', 'college', 'campus', 'student', 'students', 'education'}
        keywords = [word for word in words if word not in stopwords]
        
        # Keep only unique words and limit to 20 keywords
        unique_keywords = list(set(keywords))[:20]
        return unique_keywords
    
    def _extract_headings(self, content: str) -> List[str]:
        """
        Extract headings from content for RAG structure
        """
        if not content:
            return []
            
        headings = []
        # Don't fully clean for headings as we need to preserve markdown format
        # Just normalize line endings for consistency
        normalized_content = re.sub(r'\r\n', '\n', content)
        
        heading_pattern = re.compile(r'^#+\s+(.+)$', re.MULTILINE)
        
        for match in heading_pattern.finditer(normalized_content):
            # Clean each heading individually
            heading_text = self._clean_text(match.group(1))
            if heading_text:
                headings.append(heading_text)
            
        return headings
    
    def _generate_search_variations(self, school: Dict) -> List[str]:
        """
        Generate search variations to improve RAG retrieval
        """
        variations = []
        
        # Add school name variations
        if school.get('name'):
            name = school['name']
            variations.append(name)
            
            # Add with country if available
            if school.get('country'):
                variations.append(f"{name} {school['country']}")
        
        # Add variations with popular subjects
        for subject in school.get('popular_subjects', [])[:3]:  # Limit to first 3
            if school.get('name'):
                variations.append(f"{school['name']} {subject}")
        
        # Add variations with country keywords
        country = school.get('country', '')
        if country and country in self.education_keywords:
            for keyword in self.education_keywords[country][:3]:  # Limit to first 3
                if school.get('name'):
                    variations.append(f"{school['name']} {keyword}")
        
        return variations[:10]  # Limit to 10 variations
    
    def optimize_schools(self, input_file: str, output_file: str) -> None:
        """
        Convert existing school data to RAG-optimized format
        """
        logger.info(f"Reading school data from {input_file}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if data contains schools
            if not isinstance(data, dict) or 'schools' not in data:
                logger.error(f"Invalid data format in {input_file}")
                return
            
            logger.info(f"Found {len(data['schools'])} schools in input file")
            
            optimized_schools = []
            
            # Process each school
            for i, school in enumerate(data['schools']):
                # Extract headings for better structure
                headings = self._extract_headings(school.get('content', ''))
                
                # Extract keywords from content
                keywords = self._extract_keywords(school.get('content', '') + ' ' + school.get('description', ''))
                
                # Get country from address if not present
                country = school.get('country', '') or self._extract_country_from_address(school.get('address', ''))
                
                # Process course information
                courses = []
                course_offerings = []
                if 'courses' in school:
                    for course in school['courses']:
                        if isinstance(course, dict) and 'title' in course:
                            # Clean course content if available
                            if 'content' in course:
                                course['content'] = self._clean_text(course['content'])
                            courses.append(course)
                            course_offerings.append(course['title'])
                        elif isinstance(course, str):
                            courses.append({'title': course, 'content': ''})
                            course_offerings.append(course)
                
                # Clean description and content for better formatting
                description = self._clean_text(school.get('description', school.get('excerpt', '')))[:300] if school.get('description') or school.get('excerpt') else ''
                content = self._clean_text(school.get('content', ''))
                
                # Create optimized school data
                optimized_school = {
                    'id': school.get('id', f"linkedu_school_{i+1:04d}"),
                    'name': school.get('name', ''),
                    'url': school.get('url', ''),
                    'country': country,
                    'popular_subjects': school.get('popular_subjects', []),
                    'description': description,
                    'courses': courses or school.get('courses', []),
                    'course_offerings': course_offerings or school.get('course_offerings', []),
                    'content': content,
                    'website': school.get('website', ''),
                    'rag_metadata': {
                        'headings': headings,
                        'keywords': keywords,
                        'search_variations': self._generate_search_variations({
                            'name': school.get('name', ''),
                            'country': country,
                            'popular_subjects': school.get('popular_subjects', [])
                        })
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
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Save to JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(optimized_schools)} optimized schools to {output_file}")
            
        except Exception as e:
            logger.error(f"Error optimizing schools: {str(e)}")

def main():
    """
    Main function to run the optimizer
    """
    optimizer = SchoolRAGOptimizer()
    
    input_file = input("Enter the path to the input JSON file (default: linkedu_schools.json): ").strip()
    if not input_file:
        input_file = "linkedu_schools.json"
    
    output_file = input("Enter the path for the optimized output file (default: linkedu_schools_rag_optimized.json): ").strip()
    if not output_file:
        output_file = "linkedu_schools_rag_optimized.json"
    
    print(f"Converting {input_file} to RAG-optimized format...")
    optimizer.optimize_schools(input_file, output_file)
    
    print(f"\nOptimization completed!")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    main()
