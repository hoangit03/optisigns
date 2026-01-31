import os
import requests
from dotenv import load_dotenv
import time

load_dotenv()

class VectorStoreManager:
    """Vector Store Manager using direct API calls"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        
        self.vector_store_id = os.getenv('VECTOR_STORE_ID')
        self.assistant_id = os.getenv('ASSISTANT_ID')
        self.base_url = "https://api.openai.com/v1"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "assistants=v2"
        }
        
        print(f"Vector Store ID: {self.vector_store_id}")
        print(f"Assistant ID: {self.assistant_id}")
    
    def upload_file(self, file_path):
        """Upload a file to OpenAI"""
        url = f"{self.base_url}/files"
        
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(file_path), f, 'text/markdown'),
                    'purpose': (None, 'assistants')
                }
                
                response = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"Exception: {e}")
            return None
    
    def add_file_to_vector_store(self, file_id):
        """Add file to vector store"""
        url = f"{self.base_url}/vector_stores/{self.vector_store_id}/files"
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json={"file_id": file_id}
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Exception: {e}")
            return None
    
    def upload_all_articles(self, articles_dir="articles"):
        """Upload all markdown files"""
        if not os.path.exists(articles_dir):
            print(f"✗ Directory '{articles_dir}' not found!")
            return None
        
        file_paths = []
        for filename in os.listdir(articles_dir):
            if filename.endswith('.md'):
                file_paths.append(os.path.join(articles_dir, filename))
        
        if not file_paths:
            print("✗ No markdown files found!")
            return None
        
        print(f"\nFound {len(file_paths)} markdown files")
        print(f"Uploading to vector store...\n")
        
        uploaded_count = 0
        failed_count = 0
        
        for i, file_path in enumerate(file_paths, 1):
            filename = os.path.basename(file_path)
            print(f"[{i}/{len(file_paths)}] {filename}...", end=" ")
            
            # Upload file
            file_response = self.upload_file(file_path)
            
            if not file_response:
                print("✗ Upload failed")
                failed_count += 1
                continue
            
            file_id = file_response.get('id')
            
            # Add to vector store
            vs_response = self.add_file_to_vector_store(file_id)
            
            if vs_response:
                print(f"✓ Success")
                uploaded_count += 1
            else:
                print("✗ Failed to add to vector store")
                failed_count += 1
            
            time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("Upload Summary")
        print("=" * 60)
        print(f"✓ Uploaded: {uploaded_count}")
        print(f"✗ Failed:   {failed_count}")
        print(f"━ Total:    {len(file_paths)}")
        print("=" * 60)
        
        # Get vector store info with file/chunk counts
        if uploaded_count > 0:
            print("\nFetching vector store statistics...")
            vs_info = self.get_vector_store_info()
        
        return {
            'uploaded': uploaded_count,
            'failed': failed_count,
            'total': len(file_paths)
        }
    
    def upload_delta_files(self, new_filenames, articles_dir="articles"):
        """Upload only new/updated files"""
        if not new_filenames:
            print("No new files to upload")
            return {'uploaded': 0, 'failed': 0, 'total': 0}
        
        file_paths = [os.path.join(articles_dir, f) for f in new_filenames]
        
        uploaded_count = 0
        failed_count = 0
        
        for i, file_path in enumerate(file_paths, 1):
            filename = os.path.basename(file_path)
            print(f"[{i}/{len(file_paths)}] {filename}...", end=" ")
            
            # Upload file
            file_response = self.upload_file(file_path)
            
            if not file_response:
                print("✗ Failed")
                failed_count += 1
                continue
            
            file_id = file_response.get('id')
            
            # Add to vector store
            vs_response = self.add_file_to_vector_store(file_id)
            
            if vs_response:
                print(f"✓ Success")
                uploaded_count += 1
            else:
                print("✗ Failed")
                failed_count += 1
            
            time.sleep(0.5)
        
        return {
            'uploaded': uploaded_count,
            'failed': failed_count,
            'total': len(file_paths)
        }
    
    def get_vector_store_info(self):
        """Get vector store information with file and chunk counts"""
        url = f"{self.base_url}/vector_stores/{self.vector_store_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                file_counts = data.get('file_counts', {})
                
                print(f"\n" + "=" * 60)
                print("Vector Store Statistics")
                print("=" * 60)
                print(f"ID:              {data.get('id')}")
                print(f"Name:            {data.get('name')}")
                print(f"Status:          {data.get('status')}")
                print(f"\nFile Counts:")
                print(f"  - Total:       {file_counts.get('total', 0)}")
                print(f"  - Completed:   {file_counts.get('completed', 0)}")
                print(f"  - In Progress: {file_counts.get('in_progress', 0)}")
                print(f"  - Failed:      {file_counts.get('failed', 0)}")
                
                # Estimate chunks (OpenAI uses ~800 tokens per chunk)
                # Average article ~2000 tokens = ~2-3 chunks per article
                total_files = file_counts.get('completed', 0)
                estimated_chunks = total_files * 2.5  # Conservative estimate
                
                print(f"\nEstimated Chunks: ~{int(estimated_chunks)} chunks")
                print(f"  (Based on {total_files} files × ~2.5 chunks/file)")
                print(f"  Chunk size: 800 tokens, overlap: 400 tokens")
                print("=" * 60)
                
                return data
            else:
                print(f"Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Exception: {e}")
            return None

if __name__ == "__main__":
    print("=" * 60)
    print("OptiSigns Vector Store Manager")
    print("=" * 60)
    print()
    
    try:
        manager = VectorStoreManager()
        
        # Upload all articles
        result = manager.upload_all_articles()
        
        if result and result['uploaded'] > 0:
            print("\n✓ Upload completed!")
            
            # Show vector store info
            print()
            manager.get_vector_store_info()
            
            print("\nNext steps:")
            print("1. Go to https://platform.openai.com/playground/assistants")
            print("2. Select your Assistant")
            print('3. Test: "How do I add a YouTube video?"')
            print("4. Take screenshot showing citations")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("1. Run: python scraper.py")
        print("2. Run: python setup_assistant.py")
        print("3. Valid OPENAI_API_KEY in .env")