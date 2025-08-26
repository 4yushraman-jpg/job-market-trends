import streamlit as st
import pandas as pd
import plotly.express as px
import ast
from collections import Counter

# --- Page Configuration ---
st.set_page_config(
    page_title="Job Market Trends Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Load Data ---
@st.cache_data
def load_data():
    """Loads and preprocesses data for the dashboard."""
    try:
        df = pd.read_csv('processed_job_data.csv')
        # Convert the string representation of a list back to an actual list
        df['skills'] = df['skills'].apply(ast.literal_eval)
        return df
    except FileNotFoundError:
        st.error("Error: processed_job_data.csv not found. Please run the data processing scripts first.")
        return pd.DataFrame()

# --- Main Application ---
st.title("📊 Job Market Trends Dashboard")

df = load_data()

if df.empty:
    st.warning("No data to display. Please generate the data files by running the scraper and processor.")
    if st.button("Run Data Processing Pipeline"):
        # This would need to be implemented with subprocess or similar
        st.info("This feature would execute the scraping and processing pipeline")
else:
    # --- Sidebar Filters ---
    st.sidebar.header("Filter Options")
    
    # Get a unique, sorted list of all available skills
    all_skills = sorted(list(set(skill for sublist in df['skills'] for skill in sublist)))
    
    selected_skills = st.sidebar.multiselect(
        'Filter by Skills:',
        options=all_skills,
        help="Select one or more skills to filter the job listings."
    )
    
    # Company filter
    companies = sorted(df['company'].unique())
    selected_companies = st.sidebar.multiselect(
        'Filter by Company:',
        options=companies,
        help="Select one or more companies to filter the job listings."
    )
    
    # Location filter
    locations = sorted(df['location'].unique())
    selected_locations = st.sidebar.multiselect(
        'Filter by Location:',
        options=locations,
        help="Select one or more locations to filter the job listings."
    )

    # --- Filter Data Logic ---
    filtered_df = df.copy()
    
    if selected_skills:
        filtered_df = filtered_df[filtered_df['skills'].apply(
            lambda s: all(item in s for item in selected_skills)
        )]
    
    if selected_companies:
        filtered_df = filtered_df[filtered_df['company'].isin(selected_companies)]
        
    if selected_locations:
        filtered_df = filtered_df[filtered_df['location'].isin(selected_locations)]

    # --- Dashboard Layout ---
    
    # Create columns for layout
    col1, col2 = st.columns([1, 2])

    with col1:
        # --- KPIs ---
        st.subheader("Key Metrics")
        total_jobs = len(df)
        filtered_jobs = len(filtered_df)
        
        st.metric(label="Total Jobs Scraped", value=total_jobs)
        st.metric(label="Jobs Matching Filter", value=filtered_jobs)
        
        if total_jobs > 0:
            percentage_matching = (filtered_jobs / total_jobs) * 100
            st.metric(label="Percentage of Jobs", value=f"{percentage_matching:.1f}%")
        else:
            st.metric(label="Percentage of Jobs", value="0%")
            
        # Top companies in filtered results
        if not filtered_df.empty:
            st.subheader("Top Companies")
            company_counts = filtered_df['company'].value_counts().head(5)
            for company, count in company_counts.items():
                st.write(f"{company}: {count} jobs")

    with col2:
        # --- Top Skills Analysis ---
        st.subheader("Most In-Demand Skills")

        if not filtered_df.empty:
            # Calculate skill frequency
            skills_freq = Counter([skill for sublist in filtered_df['skills'] for skill in sublist])
            skills_df = pd.DataFrame({'Skill': list(skills_freq.keys()), 'Count': list(skills_freq.values())})
            top_skills = skills_df.nlargest(15, 'Count').sort_values(by='Count', ascending=True)

            # Create the bar chart
            fig = px.bar(
                top_skills,
                x='Count',
                y='Skill',
                orientation='h',
                title='Top 15 In-Demand Skills',
                labels={'Skill': 'Skill', 'Count': 'Number of Mentions'},
                template='plotly_white'
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No jobs match the selected filters.")

    # --- Skills Correlation Heatmap (New Feature) ---
    if not filtered_df.empty and len(selected_skills) > 1:
        st.subheader("Skills Co-occurrence Heatmap")
        
        # Create a matrix of skill co-occurrence
        skills_list = list(set([skill for sublist in filtered_df['skills'] for skill in sublist]))
        co_occurrence = pd.DataFrame(0, index=skills_list, columns=skills_list)
        
        for skills in filtered_df['skills']:
            for i in range(len(skills)):
                for j in range(i+1, len(skills)):
                    co_occurrence.loc[skills[i], skills[j]] += 1
                    co_occurrence.loc[skills[j], skills[i]] += 1
        
        # Create heatmap
        fig = px.imshow(co_occurrence, text_auto=True, aspect="auto",
                       title="How often skills appear together in job postings")
        st.plotly_chart(fig, use_container_width=True)

    # --- Display Filtered Job Listings ---
    st.header("Filtered Job Listings")
    st.write(f"Showing {len(filtered_df)} jobs")

    if not filtered_df.empty:
        # Display the filtered dataframe
        display_df = filtered_df[['title', 'company', 'location', 'skills', 'link']].copy()
        display_df['skills'] = display_df['skills'].apply(lambda x: ', '.join(x))
        
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "link": st.column_config.LinkColumn("Apply", display_text="🔗 View Job")
            }
        )
        
        # Add download button
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Download filtered data as CSV",
            data=csv,
            file_name="filtered_jobs.csv",
            mime="text/csv",
        )
    else:
        st.info("No jobs match your current filters. Try adjusting your selection.")