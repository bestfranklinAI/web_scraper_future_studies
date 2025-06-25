#!/usr/bin/env python3
"""
Run Full LinkedU School Scraper
Script to run the full school scraping and save results to the main output file
"""

from linkedu_school_scraper import LinkedUSchoolScraper

def main():
    """
    Run the full school scraper after the test scrape has been validated
    """
    print("Starting LinkedU school full scraping with RAG optimization...")
    print("This will scrape all school pages and may take some time.")
    
    # Ask user to confirm they want to run the full scrape
    confirmation = input("Do you want to proceed with full scrape? (y/n): ").strip().lower()
    
    if confirmation != 'y':
        print("Scrape cancelled.")
        return
        
    scraper = LinkedUSchoolScraper()
    
    # Run scraper with no limitations
    schools = scraper.scrape_all_schools(
        max_pages=10,  # Get all pages
        output_file="院校點評/linkedu_schools_rag_optimized.json",
        max_schools=None  # No limit
    )
    
    if schools:
        print(f"\nFull scraping completed!")
        print(f"Total schools scraped: {len(schools)}")
        print(f"Saved to: 院校點評/linkedu_schools_rag_optimized.json")
    else:
        print("No schools were scraped successfully.")

if __name__ == "__main__":
    main()
