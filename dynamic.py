import plotly.express as px
import streamlit as st

def graph(df):
    # Aggregate data: count of high layoff risk records by AI_Adoption_Level and Industry
    # Filter to focus on high risk for clearer comparison
    high_risk = df[df['Layoff_Risk'] == 'High']
    grouped = high_risk.groupby(['AI_Adoption_Level', 'Industry']).size().reset_index(name='Count')
    
    fig = px.bar(grouped, 
                 x='AI_Adoption_Level', 
                 y='Count', 
                 color='Industry',
                 barmode='group',
                 title='V2EX热议的AI话题与Kaggle数据趋势一致性分析: 高风险裁员记录分布',
                 labels={'AI_Adoption_Level': 'AI Adoption Level', 'Count': 'Number of High Risk Records', 'Industry': 'Industry'},
                 hover_data={'AI_Adoption_Level': True, 'Industry': True, 'Count': True})
    
    fig.update_layout(xaxis_title='AI Adoption Level', yaxis_title='Number of High Risk Records')
    
    st.plotly_chart(fig, use_container_width=True)