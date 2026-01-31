import os
import sys
import shutil
import argparse
from datetime import datetime
from scraper import OptiSignsScraper
from vector_store_manager import VectorStoreManager
from dotenv import load_dotenv

load_dotenv()

def main():
    """Main pipeline: Scrape -> Detect changes -> Upload delta"""
    
    print("=" * 70)
    print(" " * 20 + "OptiBot Scraper & Uploader")
    print("=" * 70)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    # Step 1: Scrape articles
    print("STEP 1: Scraping Articles")
    print("-" * 70)
    
    try:
        scraper = OptiSignsScraper()
        stats, new_articles = scraper.scrape_all(limit=50)
    except Exception as e:
        print(f"✗ Scraping failed: {e}")
        print("\nNote: Using existing articles from previous run")
        stats = {'added': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        new_articles = []
    
    print()
    
    # Step 2: Upload to vector store (only if there are changes)
    print("STEP 2: Vector Store Upload")
    print("-" * 70)
    
    if new_articles:
        print(f"Found {len(new_articles)} new/updated articles to upload")
        print()
        
        try:
            manager = VectorStoreManager()
            result = manager.upload_delta_files(new_articles)
            
            if result:
                print()
                print("-" * 70)
                print(f"Upload Results: {result['uploaded']} succeeded, {result['failed']} failed")
                print("-" * 70)
            
        except Exception as e:
            print(f"✗ Upload failed: {e}")
            return 1
    else:
        print("No new or updated articles to upload (all skipped)")
        print("Vector store is up to date ✓")
        print("-" * 70)
    
    print()
    
    # Step 3: Summary
    print("SUMMARY")
    print("=" * 70)
    print(f"Articles processed:  {stats.get('added', 0) + stats.get('updated', 0) + stats.get('skipped', 0)}")
    print(f"  - Added:           {stats.get('added', 0)}")
    print(f"  - Updated:         {stats.get('updated', 0)}")
    print(f"  - Skipped:         {stats.get('skipped', 0)}")
    print(f"  - Failed:          {stats.get('failed', 0)}")
    
    if new_articles:
        print(f"Files uploaded:      {len(new_articles)}")
    else:
        print(f"Files uploaded:      0 (no changes detected)")
    
    print("=" * 70)
    print()
    print("✓ Job completed successfully")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OptiBot Scraper & Uploader")
    parser.add_argument('--reset', action='store_true', help='Remove cached articles and metadata before running')
    args = parser.parse_args()

    if args.reset:
        # Remove metadata file and articles directory to force a full fresh run
        metadata_file = 'articles_metadata.json'
        articles_dir = 'articles'

        if os.path.exists(metadata_file):
            try:
                os.remove(metadata_file)
                print(f"Removed metadata file: {metadata_file}")
            except Exception as e:
                print(f"Warning: failed to remove {metadata_file}: {e}")

        if os.path.exists(articles_dir):
            try:
                shutil.rmtree(articles_dir)
                print(f"Removed articles directory: {articles_dir}")
            except Exception as e:
                print(f"Warning: failed to remove {articles_dir}: {e}")

    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n✗ Job interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)