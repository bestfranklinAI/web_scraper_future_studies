#!/usr/bin/env python3
"""
RAG Optimization Module
Optimizes scraped articles for better RAG retrieval and question answering
"""

import json
import re
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RAGOptimizer:
    def __init__(self):
        self.stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好', '自己', '這', '那', '可以', '這個', '那個', '但是', '因為', '所以', '如果', '雖然', '然後', '還是', '已經', '應該', '可能', '時候', '地方', '問題', '方法', '情況', '時間', '工作', '生活', '學習', '知道', '認為', '覺得', '希望', '需要', '想要', '開始', '進行', '發現', '出現', '產生', '形成', '建立', '創造', '發展', '提高', '增加', '減少', '改變', '影響', '作用', '關係', '聯繫', '比較', '不同', '相同', '重要', '主要', '基本', '一般', '特別', '尤其', '特殊', '具體', '詳細', '簡單', '複雜', '容易', '困難', '可能', '不可能', '必須', '應當', '能夠', '無法', '允許', '禁止', '包括', '除了', '關於', '對於', '根據', '按照', '通過', '利用', '使用', '採用', '選擇', '決定', '確定', '安排', '計劃', '準備', '完成', '實現', '達到', '獲得', '取得', '成功', '失敗', '正確', '錯誤', '好的', '壞的', '大的', '小的', '多的', '少的', '高的', '低的', '長的', '短的', '新的', '舊的'
        }
    
    def optimize_articles_for_rag(self, articles: List[Dict]) -> Dict[str, Any]:
        """
        Optimize articles for RAG by restructuring and enhancing content
        """
        optimized_articles = []
        
        for i, article in enumerate(articles):
            try:
                optimized = self._optimize_single_article(article, i + 1)
                if optimized:
                    optimized_articles.append(optimized)
            except Exception as e:
                logger.error(f"Error optimizing article {i+1}: {str(e)}")
                continue
        
        return {
            'metadata': {
                'source': 'LinkedU Articles (RAG Optimized)',
                'total_documents': len(optimized_articles),
                'optimization_date': datetime.now().isoformat(),
                'format_version': '2.0',
                'optimization_features': [
                    'Semantic chunking',
                    'Enhanced searchable content',
                    'Topic extraction',
                    'Question-answer pairs',
                    'Structured headings',
                    'Clean content formatting'
                ]
            },
            'documents': optimized_articles
        }
    
    def _optimize_single_article(self, article: Dict, index: int) -> Dict[str, Any]:
        """
        Optimize a single article for RAG retrieval
        """
        # Extract and clean content
        title = self._clean_text(article.get('title', ''))
        content = self._clean_text(article.get('content', ''))
        excerpt = self._clean_text(article.get('excerpt', ''))
        
        if not title or not content:
            return None
        
        # Create semantic chunks
        chunks = self._create_semantic_chunks(content, title)
        
        # Extract topics and keywords
        topics = self._extract_comprehensive_topics(article)
        keywords = self._extract_keywords(f"{title} {excerpt} {content}")
        
        # Generate searchable content variations
        searchable_content = self._create_searchable_content(title, content, excerpt)
        
        # Create potential Q&A pairs
        qa_pairs = self._generate_qa_pairs(title, content, chunks)
        
        return {
            'id': f"linkedu_{index:04d}",
            'title': title,
            'summary': excerpt or self._create_summary(content),
            'full_content': content,
            'source_url': article.get('source_url', ''),
            'topics': topics,
            'keywords': keywords,
            'semantic_chunks': chunks,
            'searchable_content': searchable_content,
            'qa_pairs': qa_pairs,
            'structure': {
                'headings': self._extract_clean_headings(article.get('headings', [])),
                'sections': self._identify_sections(content)
            },
            'metadata': {
                'content_type': 'educational_article',
                'language': 'zh-HK',
                'source': 'LinkedU',
                'indexed_at': datetime.now().isoformat()
            }
        }
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text for better search
        """
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common formatting artifacts
        text = re.sub(r'[^\w\s\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f\u2b740-\u2b81f\u2b820-\u2ceaf\uf900-\ufaff\u3300-\u33ff\ufe30-\ufe4f\uf900-\ufaff\u2f800-\u2fa1f，。！？；：""''（）【】《》、]', ' ', text)
        
        # Normalize punctuation
        text = re.sub(r'\s*[，。！？；：]\s*', '，', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _create_semantic_chunks(self, content: str, title: str) -> List[Dict[str, str]]:
        """
        Create semantically meaningful chunks for better retrieval
        """
        chunks = []
        
        # Split by headings and paragraphs
        sections = re.split(r'\n##\s+', content)
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            
            # Extract heading if present
            lines = section.split('\n')
            heading = lines[0].strip() if lines else ""
            section_content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else section.strip()
            
            if len(section_content) < 50:  # Skip very short sections
                continue
            
            # Further split long sections into paragraphs
            paragraphs = [p.strip() for p in section_content.split('\n\n') if p.strip()]
            
            for j, paragraph in enumerate(paragraphs):
                if len(paragraph) < 30:  # Skip very short paragraphs
                    continue
                
                chunk_id = f"chunk_{i}_{j}" if j > 0 else f"chunk_{i}"
                
                chunks.append({
                    'id': chunk_id,
                    'heading': heading,
                    'content': paragraph,
                    'context': f"{title} - {heading}" if heading else title,
                    'length': len(paragraph)
                })
        
        return chunks
    
    def _extract_comprehensive_topics(self, article: Dict) -> List[str]:
        """
        Extract comprehensive topics from article
        """
        topics = set()
        
        # From categories
        categories = article.get('categories', '')
        if categories:
            category_topics = re.split(r'[．·,，\s]+', categories)
            topics.update([t.strip() for t in category_topics if t.strip()])
        
        # From title and content
        title = article.get('title', '')
        content = article.get('content', '')
        
        # Educational topic patterns for LinkedU
        education_patterns = [
            r'(大學|學院|學校)',
            r'(學科|專業|課程)',
            r'(入學|申請|錄取)',
            r'(學費|獎學金|資助)',
            r'(海外|留學|遊學)',
            r'(英國|美國|加拿大|澳洲|新西蘭)',
            r'(IELTS|TOEFL|SAT|A-Level|IB)',
            r'(碩士|學士|博士)',
            r'(升學|轉校|銜接)',
            r'(簽證|移民)'
        ]
        
        text_to_analyze = f"{title} {content}".lower()
        
        for pattern in education_patterns:
            matches = re.findall(pattern, text_to_analyze)
            topics.update(matches)
        
        # Clean and filter topics
        cleaned_topics = []
        for topic in topics:
            topic = topic.strip()
            if topic and len(topic) > 1 and topic not in self.stopwords:
                cleaned_topics.append(topic)
        
        return sorted(list(set(cleaned_topics)))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords for search
        """
        # Common educational keywords in Chinese
        important_patterns = [
            r'[A-Z]{2,}',  # Acronyms like IELTS, SAT
            r'\d+年',  # Years
            r'第\d+',   # Rankings
            r'(?:學費|費用)\s*[:：]\s*[^\n]+',  # Fees
            r'(?:入學要求|申請條件)[:：][^\n]+',  # Requirements
            r'(?:截止日期|申請期限)[:：][^\n]+'   # Deadlines
        ]
        
        keywords = set()
        
        for pattern in important_patterns:
            matches = re.findall(pattern, text)
            keywords.update([m.strip() for m in matches])
        
        # Extract high-frequency meaningful terms
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[A-Za-z]{3,}', text)
        word_freq = {}
        
        for word in words:
            if word not in self.stopwords and len(word) > 1:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top frequent words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        keywords.update([word for word, freq in top_words if freq > 2])
        
        return sorted(list(keywords))
    
    def _create_searchable_content(self, title: str, content: str, excerpt: str) -> str:
        """
        Create enhanced searchable content with variations
        """
        searchable_parts = [title, excerpt, content]
        
        # Add variations and synonyms for common terms
        variations = {
            '大學': '大學 學院 高等教育 university college',
            '申請': '申請 報名 入學 application apply',
            '學費': '學費 費用 tuition fee cost',
            '獎學金': '獎學金 資助 助學金 scholarship grant',
            '留學': '留學 海外升學 overseas study abroad',
            '簽證': '簽證 visa 入境許可',
            '英國': '英國 UK 英倫 Britain United Kingdom',
            '美國': '美國 USA 美利堅 America United States'
        }
        
        enhanced_content = ' '.join(searchable_parts)
        
        for term, expanded in variations.items():
            if term in enhanced_content:
                enhanced_content += f" {expanded}"
        
        return self._clean_text(enhanced_content)
    
    def _generate_qa_pairs(self, title: str, content: str, chunks: List[Dict]) -> List[Dict[str, str]]:
        """
        Generate potential question-answer pairs
        """
        qa_pairs = []
        
        # Basic Q&A patterns
        qa_patterns = [
            {
                'question_pattern': f"什麼是{title}？",
                'answer': chunks[0]['content'] if chunks else content[:200] + "..."
            },
            {
                'question_pattern': f"關於{title}的詳細資訊",
                'answer': content[:300] + "..." if len(content) > 300 else content
            }
        ]
        
        # Extract Q&A from content structure
        for chunk in chunks[:5]:  # Limit to first 5 chunks
            if chunk.get('heading'):
                qa_pairs.append({
                    'question': f"{chunk['heading']}是什麼？",
                    'answer': chunk['content'],
                    'context': chunk.get('context', title)
                })
        
        return qa_pairs
    
    def _extract_clean_headings(self, headings: List[Dict]) -> List[str]:
        """
        Extract and clean headings
        """
        if not headings:
            return []
        
        clean_headings = []
        for heading in headings:
            if isinstance(heading, dict) and 'text' in heading:
                text = self._clean_text(heading['text'])
                if text and len(text) > 2:
                    clean_headings.append(text)
        
        return clean_headings
    
    def _identify_sections(self, content: str) -> List[Dict[str, str]]:
        """
        Identify main sections in content
        """
        sections = []
        section_parts = re.split(r'\n##\s+', content)
        
        for i, part in enumerate(section_parts):
            if not part.strip():
                continue
            
            lines = part.split('\n')
            section_title = lines[0].strip() if lines else f"Section {i+1}"
            section_content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else part.strip()
            
            if section_content and len(section_content) > 50:
                sections.append({
                    'title': section_title,
                    'content': section_content[:200] + "..." if len(section_content) > 200 else section_content
                })
        
        return sections
    
    def _create_summary(self, content: str) -> str:
        """
        Create a summary from content
        """
        # Take first meaningful paragraph
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for paragraph in paragraphs:
            if len(paragraph) > 50 and not paragraph.startswith('##'):
                return paragraph[:200] + "..." if len(paragraph) > 200 else paragraph
        
        return content[:200] + "..." if len(content) > 200 else content

def optimize_for_rag(input_file: str, output_file: str):
    """
    Legacy function for backward compatibility
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    optimizer = RAGOptimizer()
    optimized_data = optimizer.optimize_articles_for_rag(data.get('articles', []))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(optimized_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Optimized {optimized_data['metadata']['total_documents']} articles for RAG")
    print(f"📄 Output saved to: {output_file}")

def main():
    """
    Main function for command line usage
    """
    input_file = 'linkedu_articles.json'
    output_file = 'linkedu_articles_rag_optimized.json'
    
    try:
        optimize_for_rag(input_file, output_file)
    except FileNotFoundError:
        print(f"❌ Input file '{input_file}' not found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
