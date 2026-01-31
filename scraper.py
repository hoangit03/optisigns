import requests
from bs4 import BeautifulSoup
import html2text
import os
import json
import hashlib
from datetime import datetime
import time

class OptiSignsScraper:
    """Real scraper using Zendesk API"""
    
    def __init__(self):
        self.base_url = "https://support.optisigns.com"
        self.api_base = f"{self.base_url}/api/v2/help_center"
        self.articles_dir = "articles"
        self.metadata_file = "articles_metadata.json"
        
        # Setup HTML to Markdown converter
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.body_width = 0
        self.h2t.ignore_images = False
        
        os.makedirs(self.articles_dir, exist_ok=True)
    
    def load_metadata(self):
        """Load existing articles metadata"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_metadata(self, metadata):
        """Save articles metadata"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def get_article_hash(self, content):
        """Generate hash for article content"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def fetch_articles_list(self, per_page=100):
        """Fetch list of articles from Zendesk API"""
        articles = []
        page = 1
        
        print("Fetching articles list from Zendesk API...")
        
        while True:
            try:
                url = f"{self.api_base}/en-us/articles.json?page={page}&per_page={per_page}"
                print(f"  Fetching page {page}...", end=" ")
                
                response = requests.get(url, timeout=30)
                
                if response.status_code != 200:
                    print(f"✗ Error {response.status_code}")
                    break
                
                data = response.json()
                page_articles = data.get('articles', [])
                
                if not page_articles:
                    print("✓ No more articles")
                    break
                
                articles.extend(page_articles)
                print(f"✓ Got {len(page_articles)} articles")
                
                # Check if there's a next page
                if not data.get('next_page'):
                    break
                
                page += 1
                time.sleep(0.5)  # Be polite to the API
                
            except Exception as e:
                print(f"✗ Error: {e}")
                break
        
        print(f"\nTotal articles found: {len(articles)}")
        return articles
    
    def fetch_article_content(self, article_id):
        """Fetch single article content from Zendesk API"""
        try:
            url = f"{self.api_base}/en-us/articles/{article_id}.json"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json().get('article')
            else:
                print(f"✗ Error {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    def clean_html_to_markdown(self, html_content, article_url):
        """Convert HTML to clean Markdown"""
        if not html_content:
            return ""
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style tags
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.decompose()
        
        # Convert to markdown
        markdown = self.h2t.handle(str(soup))
        
        # Clean up excessive newlines
        lines = []
        prev_empty = False
        
        for line in markdown.split('\n'):
            is_empty = not line.strip()
            
            if is_empty:
                if not prev_empty:
                    lines.append(line)
                prev_empty = True
            else:
                lines.append(line)
                prev_empty = False
        
        markdown = '\n'.join(lines).strip()
        
        # Add article URL at the top
        markdown = f"Article URL: {article_url}\n\n{markdown}"
        
        return markdown
    
    def scrape_article(self, article_info):
        """Scrape a single article"""
        article_id = article_info['id']
        
        # Fetch full article content via API
        article = self.fetch_article_content(article_id)
        
        if not article:
            return None
        
        # Convert HTML body to Markdown
        html_body = article.get('body', '')
        article_url = article.get('html_url', '')
        
        markdown = self.clean_html_to_markdown(html_body, article_url)
        
        if not markdown or markdown == f"Article URL: {article_url}\n\n":
            return None
        
        return {
            'markdown': markdown,
            'hash': self.get_article_hash(markdown),
            'url': article_url,
            'title': article.get('title', 'Untitled'),
            'updated_at': article.get('updated_at', ''),
            'scraped_at': datetime.now().isoformat()
        }
    
    def save_article(self, article_data, filename):
        """Save article to file"""
        filepath = os.path.join(self.articles_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(article_data['markdown'])
        return filepath
    
    def scrape_all(self, limit=30):
        """Scrape articles and detect changes"""
        print("=" * 70)
        print("OptiSigns Article Scraper (Zendesk API)")
        print("=" * 70)
        print()
        
        # Fetch articles list
        all_articles = self.fetch_articles_list()
        
        if not all_articles:
            print("✗ No articles found!")
            return {'added': 0, 'updated': 0, 'skipped': 0, 'failed': 0}, []
        
        # Limit articles
        articles_to_scrape = all_articles[:limit]
        print(f"\nProcessing {len(articles_to_scrape)} articles...")
        print()
        
        metadata = self.load_metadata()
        stats = {'added': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        new_articles = []
        
        for i, article_info in enumerate(articles_to_scrape, 1):
            title = article_info.get('title', 'Untitled')[:50]
            article_id = str(article_info['id'])
            
            print(f"[{i}/{len(articles_to_scrape)}] {title}...", end=" ")
            
            # Scrape article
            article_data = self.scrape_article(article_info)
            
            if not article_data:
                print("✗ Failed")
                stats['failed'] += 1
                continue
            
            filename = f"{article_id}.md"
            
            # Check if article exists and has changed
            if article_id in metadata:
                if metadata[article_id]['hash'] != article_data['hash']:
                    print("↻ Updated")
                    stats['updated'] += 1
                    self.save_article(article_data, filename)
                    metadata[article_id].update({
                        'hash': article_data['hash'],
                        'last_updated': article_data['scraped_at']
                    })
                    new_articles.append(filename)
                else:
                    print("✓ Unchanged")
                    stats['skipped'] += 1
            else:
                print("+ Added")
                stats['added'] += 1
                self.save_article(article_data, filename)
                metadata[article_id] = {
                    'hash': article_data['hash'],
                    'url': article_data['url'],
                    'title': article_data['title'],
                    'filename': filename,
                    'last_updated': article_data['scraped_at']
                }
                new_articles.append(filename)
            
            time.sleep(0.5)  # Be polite to API
        
        self.save_metadata(metadata)
        
        print()
        print("=" * 70)
        print("Scraping Summary")
        print("=" * 70)
        print(f"✓ Added:    {stats['added']}")
        print(f"↻ Updated:  {stats['updated']}")
        print(f"- Skipped:  {stats['skipped']}")
        print(f"✗ Failed:   {stats['failed']}")
        print(f"━ Total:    {len(articles_to_scrape)}")
        print("=" * 70)
        
        return stats, new_articles

if __name__ == "__main__":
    scraper = OptiSignsScraper()
    stats, new_files = scraper.scrape_all(limit=30)
    
    if stats['added'] > 0 or stats['updated'] > 0:
        print(f"\n✓ {len(new_files)} files ready for upload")
        print("\nNext step: python vector_store_manager.py")