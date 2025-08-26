import pandas as pd
import re
from collections import Counter

SKILLS_LIST = [
    'python', 'r', 'sql', 'java', 'c\+\+', 'scala', 'julia',  # Escape special chars
    'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'plotly',
    'scikit-learn', 'sklearn', 'tensorflow', 'keras', 'pytorch', 'torch',
    'spark', 'pyspark', 'hadoop', 'mapreduce',
    'aws', 'azure', 'gcp', 'google cloud',
    'docker', 'kubernetes',
    'git', 'github',
    'tableau', 'power bi', 'powerbi', 'looker',
    'excel', 'statistics', 'machine learning', 'deep learning',
    'nlp', 'natural language processing', 'computer vision',
    'etl', 'data warehousing', 'data modeling', 'data mining'
]

# Create a mapping for skill normalization
SKILL_MAPPING = {
    'sklearn': 'scikit-learn',
    'torch': 'pytorch',
    'powerbi': 'power bi',
    'google cloud': 'gcp',
    'natural language processing': 'nlp'
}

def extract_skills(description):
    """Extracts predefined skills from a job description string."""
    if not isinstance(description, str):
        return []
    
    found_skills = set()
    description_lower = description.lower()
    
    for skill in SKILLS_LIST:
        # Use regex to find whole words
        pattern = r'\b' + skill + r'\b'
        if re.search(pattern, description_lower):
            # Normalize skill names
            normalized_skill = SKILL_MAPPING.get(skill, skill)
            found_skills.add(normalized_skill)
                
    return sorted(list(found_skills))

def main():
    """Loads raw data, processes it, and saves the cleaned data."""
    try:
        df = pd.read_csv('raw_job_data.csv')
        print(f"Successfully loaded raw_job_data.csv with {len(df)} records")
    except FileNotFoundError:
        print("Error: raw_job_data.csv not found. Please run scraper.py first.")
        return

    print("Processing data and extracting skills...")
    
    # Clean data
    df = df.dropna(subset=['description'])
    df = df[df['description'] != 'Description not found.']
    df = df[df['description'] != 'N/A']
    df = df[df['description'] != 'Error loading description']
    
    # Extract skills
    df['skills'] = df['description'].apply(extract_skills)
    
    # Calculate skill frequencies for reporting
    all_skills = [skill for sublist in df['skills'] for skill in sublist]
    skill_counts = Counter(all_skills)
    
    print(f"Processed {len(df)} job listings")
    print("Top 10 skills found:")
    for skill, count in skill_counts.most_common(10):
        print(f"  {skill}: {count}")

    df.to_csv('processed_job_data.csv', index=False)
    print("\nSuccessfully saved processed data to processed_job_data.csv")

if __name__ == "__main__":
    main()