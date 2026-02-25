import streamlit as st
import pandas as pd
import duckdb
from openai import OpenAI
import plotly.express as px

st.set_page_config(page_title="AI Data Analysis Agent", page_icon="📊", layout="wide")

st.title("🤖 AI Data Analysis Agent")
st.markdown("Analyze your data using natural language - No coding required!")

with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.markdown("---")
    st.markdown("### 📖 How to Use")
    st.markdown("""
    1. Get API key from OpenAI
    2. Paste it above
    3. Upload your CSV/Excel file
    4. Ask questions in plain English
    5. Get instant answers!
    """)
    
    st.markdown("---")
    st.markdown("### 🔗 Get API Key")
    st.markdown("[Click here to get OpenAI API Key](https://platform.openai.com/api-keys)")

if api_key:
    client = OpenAI(api_key=api_key)
    
    uploaded_file = st.file_uploader("📤 Upload Your Data File (CSV or Excel)", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns!")
            
            with st.expander("👁️ Click to Preview Your Data"):
                st.dataframe(df.head(10))
            
            with st.expander("📋 Click to See Column Names and Types"):
                col_info = pd.DataFrame({
                    'Column Name': df.columns,
                    'Data Type': df.dtypes.values,
                    'Sample Value': [df[col].iloc[0] if len(df) > 0 else 'N/A' for col in df.columns]
                })
                st.dataframe(col_info)
            
            con = duckdb.connect(':memory:')
            con.register('data', df)
            
            st.markdown("---")
            st.subheader("💬 Ask Questions About Your Data")
            
            st.markdown("**Example questions you can ask:**")
            st.markdown("""
            - What is the total sales?
            - Show me average price by category
            - Which product has the highest sales?
            - Count how many records per region
            """)
            
            user_question = st.text_area("Type your question here:", placeholder="Example: What is the average sales by region?", height=100)
            
            if st.button("🔍 Get Answer", type="primary"):
                if user_question:
                    with st.spinner("🤔 Thinking..."):
                        try:
                            schema_text = "Table name: data\n\nColumns:\n"
                            for col, dtype in zip(df.columns, df.dtypes):
                                schema_text += f"- {col} ({dtype})\n"
                            
                            prompt = f"""You are a SQL expert. Given this database schema:

{schema_text}

Convert this question to a SQL query for DuckDB:
"{user_question}"

Rules:
- Return ONLY the SQL query
- No explanations
- Use table name 'data'
- Make it simple and correct"""

                            response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": "You are a helpful SQL expert. Return only SQL queries."},
                                    {"role": "user", "content": prompt}
                                ]
                            )
                            
                            sql_query = response.choices[0].message.content.strip()
                            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
                            
                            with st.expander("🔧 SQL Query Generated (click to see)"):
                                st.code(sql_query, language='sql')
                            
                            result = con.execute(sql_query).fetchdf()
                            
                            st.success("✅ Here's your answer!")
                            st.subheader("📊 Results:")
                            st.dataframe(result, use_container_width=True)
                            
                            if len(result.columns) == 2 and len(result) > 0 and len(result) <= 50:
                                st.subheader("📈 Visualization:")
                                try:
                                    fig = px.bar(result, x=result.columns[0], y=result.columns[1], title=f"{result.columns[1]} by {result.columns[0]}")
                                    st.plotly_chart(fig, use_container_width=True)
                                except:
                                    pass
                            
                            csv = result.to_csv(index=False)
                            st.download_button(label="📥 Download Results as CSV", data=csv, file_name="analysis_results.csv", mime="text/csv")
                            
                        except Exception as e:
                            st.error(f"❌ Oops! Something went wrong: {str(e)}")
                            st.info("💡 Try rephrasing your question or check your data.")
                else:
                    st.warning("⚠️ Please type a question first!")
                    
        except Exception as e:
            st.error(f"❌ Could not load file: {str(e)}")
            st.info("💡 Make sure your file is a valid CSV or Excel file.")
else:
    st.info("👈 **Please enter your OpenAI API Key in the sidebar to start!**")
    st.markdown("### 🔑 How to get an API Key:")
    st.markdown("""
    1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
    2. Sign up or log in
    3. Click "Create new secret key"
    4. Copy the key and paste it in the sidebar
    """)

st.markdown("---")
st.markdown("Built with ❤️ using Streamlit + OpenAI GPT-4 + DuckDB")
