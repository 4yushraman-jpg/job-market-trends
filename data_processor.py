import pandas as pd
import re
from collections import Counter
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SKILLS_LIST = [
    'python', 'r', 'sql', 'java', 'c\+\+', 'scala', 'julia',
    'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'plotly',
    'scikit-learn', 'sklearn', 'tensorflow', 'keras', 'pytorch', 'torch',
    'spark', 'pyspark', 'hadoop', 'mapreduce', 'hive',
    'aws', 'azure', 'gcp', 'google cloud', 's3', 'ec2', 'lambda',
    'docker', 'kubernetes', 'container',
    'git', 'github', 'gitlab',
    'tableau', 'power bi', 'powerbi', 'looker', 'superset',
    'excel', 'statistics', 'machine learning', 'deep learning',
    'nlp', 'natural language processing', 'computer vision', 'cv',
    'etl', 'data warehousing', 'data modeling', 'data mining',
    'regression', 'classification', 'clustering', 'neural network', 'cnn', 'rnn',
    'big data', 'distributed system', 'api', 'rest', 'json', 'xml'
]

SKILL_MAPPING = {
    'sklearn': 'scikit-learn',
    'torch': 'pytorch',
    'powerbi': 'power bi',
    'google cloud': 'gcp',
    'natural language processing': 'nlp',
    'computer vision': 'cv',
    'deep learning': 'machine learning',
    'neural network': 'machine learning'
}

def extract_skills(description):
    """Extracts predefined skills from a job description string."""
    if not isinstance(description, str) or description in ['N/A', 'Description not found.', 'Error loading description']:
        return []
    
    found_skills = set()
    description_lower = description.lower()
    
    for skill in SKILLS_LIST:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, description_lower):
            normalized_skill = SKILL_MAPPING.get(skill, skill)
            found_skills.add(normalized_skill)
                
    return sorted(list(found_skills))

def clean_data(df):
    """Clean and preprocess the job data."""
    # Remove rows with missing critical data
    df = df.dropna(subset=['title', 'company', 'description'])
    
    # Remove rows with placeholder descriptions
    invalid_descriptions = ['N/A', 'Description not found.', 'Error loading description']
    df = df[~df['description'].isin(invalid_descriptions)]
    
    # Clean text fields
    text_columns = ['title', 'company', 'location', 'description']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    return df

def main():
    """Loads raw data, processes it, and saves the cleaned data."""
    try:
        df = pd.read_csv('raw_job_data.csv')
        logging.info(f"Successfully loaded raw data with {len(df)} records")
    except FileNotFoundError:
        logging.error("raw_job_data.csv not found. Please run scraper.py first.")
        return

    # Clean the data
    logging.info("Cleaning data...")
    df_clean = clean_data(df)
    logging.info(f"After cleaning: {len(df_clean)} records remaining")
    
    # Extract skills
    logging.info("Extracting skills from descriptions...")
    df_clean['skills'] = df_clean['description'].apply(extract_skills)
    
    # Calculate skill statistics
    all_skills = [skill for sublist in df_clean['skills'] for skill in sublist]
    skill_counts = Counter(all_skills)
    
    logging.info("Top 10 skills found:")
    for skill, count in skill_counts.most_common(10):
        logging.info(f"  {skill}: {count}")
    
    # Add skill count column
    df_clean['skill_count'] = df_clean['skills'].apply(len)
    
    # Save processed data
    output_file = 'processed_job_data.csv'
    df_clean.to_csv(output_file, index=False)
    logging.info(f"Processed data saved to {output_file}")
    
    # Generate summary report
    summary = {
        'total_jobs': len(df),
        'cleaned_jobs': len(df_clean),
        'unique_companies': df_clean['company'].nunique(),
        'unique_skills': len(skill_counts),
        'avg_skills_per_job': df_clean['skill_count'].mean(),
        'top_skills': dict(skill_counts.most_common(5))
    }
    
    logging.info("Processing complete!")
    logging.info(f"Summary: {summary}")

if __name__ == "__main__":
    main()