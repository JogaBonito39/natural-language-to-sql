import streamlit as st
import pandas as pd
import io
from database_llm import initialize_llm, generate_and_extract_sql, run_remote_script, DB_USER

st.set_page_config(page_title="SQL LLM Interface", layout="wide")

st.title("Natural Language to SQL Dashboard")
st.markdown("Enter a question about the HMDA database below.")

with st.sidebar:
    st.header("Connection Settings")
    netid = st.text_input("NetID", value = DB_USER)
    password = st.text_input("Ilab Password", type="password")
    if st.button("Clear Cache"):
        st.cache_resource.clear()

@st.cache_resource
def get_llm():
    return initialize_llm()

llm = get_llm()

user_query = st.text_input("Ask a question about your data:",
                           placeholder = "e.g., show me the first five rows of the agency table")

if user_query:
    if not password:
        st.error("Please enter your password in the sidebar.")
    else:
        with st.spinner("LLM is thinking and connecting to Ilab..."):
            sql = generate_and_extract_sql(llm, user_query)
            raw_result = run_remote_script(netid, password, sql)
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("User Query")
                st.info(user_query)

                st.subheader("Generated SQL")
                st.code(sql, language="sql")

            with col2:
                st.subheader("LLM Though Process")
                st.text_area("RAW LLM Output", value=f"Generated SQL: {sql}", height=150)

            st.divider()

            st.subheader("Data Output")
            try:
                df = pd.read_csv(io.StringIO(raw_result), sep=r'\s{2,}', engine='python')
                if df.empty:
                    st.warning("No rows returned.")
                else:
                    st.dataframe(df, use_container_width=True)

                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Results as CSV", csv, "results.csv", "text/csv")

            except Exception as e:
                st.error("Could not parse result into a table. Raw output shown below:")
                st.code(raw_result)

st.markdown("---")
st.caption("Connected to postgres.cs.rutgers.edu via Ilab SSH")