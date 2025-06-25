# Further Studies - Educational Resource Scraper

This repository contains tools for scraping educational resources from [LinkedU.hk](https://linkedu.hk) to create optimized data collections for RAG (Retrieval-Augmented Generation) systems. The scraped content is organized into several categories focused on helping students with further education planning and university selection.

## Project Structure

- **Countries/** - Educational system information for different countries (AU, CN, UK, US)
- **升學攻略/** (Study Guides) - Articles related to further studies and educational planning
- **熱門科目/** (Popular Subjects) - Information about popular academic subjects and majors
- **院校點評/** (Institution Reviews) - Reviews and details about educational institutions

## Features

- Web scraping from LinkedU.hk educational resources
- Data optimization for RAG (Retrieval-Augmented Generation) systems
- Structured storage of educational content in JSON format
- Support for Chinese language educational resources

## Requirements

- Python 3.6+
- See `requirements.txt` for required packages

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Scrape Articles
```
python 升學攻略/linkedu_scraper.py
```

### Scrape Subjects
```
python 熱門科目/run_subjects_scraper.py
```

### Scrape Schools
```
python 院校點評/run_full_school_scraper.py
```

### Optimize RAG Data
```
python 升學攻略/rag_optimizer.py
```

## Data Format

The scraped data is stored in JSON format with optimizations for RAG systems, including:
- Content segmentation
- Keyword extraction
- Metadata enrichment
- Hierarchical categorization

## License

This project is for educational purposes only. Please respect the copyright and terms of service of LinkedU.hk when using this code.

## Contributing

Contributions to improve the scrapers or data optimization are welcome. Please feel free to submit a pull request or open an issue.
