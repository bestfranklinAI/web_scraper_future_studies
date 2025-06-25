#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to run the LinkedU subjects scraper
"""

from linkedu_subjects_scraper import LinkeduSubjectScraper

def main():
    """Main function to run the scraper."""
    print("Starting LinkedU subjects scraper...")
    scraper = LinkeduSubjectScraper()
    result = scraper.run()
    
    print(f"Scraping completed successfully!")
    print(f"Scraped {result['subject_count']} subjects")
    print(f"Raw data saved to: {result['raw_data']}")
    print(f"Optimized data saved to: {result['optimized_data']}")

if __name__ == "__main__":
    main()
