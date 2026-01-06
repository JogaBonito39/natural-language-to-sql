import sys
import re
import getpass
import paramiko
from llama_cpp import Llama
import urllib.parse
import os

MODEL_FILE_PATH = "./models/Phi-3-mini-4k-instruct-q4.gguf"
SSH_HOST = "ilab.cs.rutgers.edu"
SSH_PORT = 22
ILAB_SCRIPT_PATH = "/common/home/<USER>/<OPTIONAL LOCATION FOLDER>/ilab_script.py"
ILAB_VENV_PYTHON = "/common/home/<USER>/<OPTIONAL LOCATION FOLDER>/venv/bin/python3"
DB_HOST = "postgres.cs.rutgers.edu"
DB_PORT = "5432"
DB_NAME = "NETID"
DB_USER = "NETID"


try:
    with open("schema_subset.sql", "r") as f:
        SCHEMA = f.read()

except FileNotFoundError:
    print(f"Error: 'schema_subset.sql' not found. Create this file first, containing all your CREATE TABLE statements.")
    sys.exit(1)

def initialize_llm():
    print(f"Loading LLM from {MODEL_FILE_PATH}...")

    n_cpu_cores = os.cpu_count() or 4
    optimal_threads = max(1, n_cpu_cores // 2)

    try:
        llm = Llama(
                model_path=MODEL_FILE_PATH,
                n_ctx=4096,
                max_tokens=200,
                temperature=0.1,
                verbose=False,
                n_threads = optimal_threads,
        )
        print(f"LLM loaded successfully using {optimal_threads} threads.")
        return llm
    except Exception as e:
        print(f"\nFATAL ERROR: Could not load LLM. Check model path/installation.")
        print(f"Details: {e}")
        sys.exit(1)

def create_sql_prompt(user_question: str) -> str:
    prompt_template = f"""### System:
PostgreSQL expert. Use ONLY provided schema. Result: ONLY SQL.
### Schema:
{SCHEMA}
### User:
{user_question}
### Assistant:
SELECT"""

    return prompt_template
    #final_prompt = prompt_template + "\n"

    #final_prompt += "Generate the rest of the query immediately after SELECT. Query:"

    ##return prompt_template.strip()

def generate_and_extract_sql(llm: Llama, user_question: str) -> str:
    prompt = create_sql_prompt(user_question)

    raw_output = llm(
            prompt,
            max_tokens=200,
            stop=["###", "Schema:", "User:", "Assistant:"],
            echo=False
    )

    generated_text = raw_output['choices'][0]['text'].strip() #added
    #generated_text = raw_output['choices'][0]['text']

    #generated_text = generated_text.replace(":code:", "").replace(":sql:", "").strip()

    full_query = "SELECT " + generated_text

    #clean_query = full_query.strip()
    clean_query = full_query.replace('\n', ' ') #added
    clean_query = re.sub(r'\s+', ' ', clean_query).strip() #added

    clean_query = re.sub(r'```sql|```', '', clean_query, flags=re.IGNORECASE).strip()

    clean_query = re.sub(r'[\s;]+$', '', clean_query)


    if len(clean_query.split()) < 3:
        table_match = re.search(r'\b(of|from|table|rows|columns)\s+the\s+(\w+)\b|\b(\w+)\s+table\b', user_question, re.IGNORECASE)
        table_name = None
        if table_match:
            table_name = table_match.group(3) or table_match.group(2)

        if table_name:
            print(f"DEBUG: LLM failed. Forcing completion for table '{table_name}'.")
            return f"SELECT * FROM {table_name} LIMIT 10"

        return ""

    #if not clean_query.lower().startswith("select"):
    #    return ""

    return clean_query

def run_remote_script(username, password, sql_query):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print("\n--- Connecting to Ilab ---")
        ssh.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=username,
            password=password,
            timeout=10
        )
        PYTHON_EXEC="python3"
        env_vars=(
                f'export DB_USER="{DB_USER}"; '
                f'export DB_PASS="{urllib.parse.quote_plus(password)}"; '
                f'export DB_HOST="{DB_HOST}"; '
                f'export DB_PORT="{DB_PORT}"; '
                f'export DB_NAME="{DB_NAME}";'
        )

        command_to_run = f'{env_vars} {ILAB_VENV_PYTHON} {ILAB_SCRIPT_PATH} \'{sql_query}\''
        command = f'/bin/bash -c "{command_to_run}"'
        #print(f" -> Executing: {command}")
        print(" -> Executing: {command}")
        print(f"-> Executing: python3 {ILAB_SCRIPT_PATH} '{sql_query[:50]}...'")

        stdin, stdout, stderr = ssh.exec_command(command)

        remote_output = stdout.read().decode('utf-8')
        remote_error = stderr.read().decode('utf-8')

        if remote_error:
            return f"\n--- REMOTE SCRIPT ERROR ---\n{remote_error}\n"
        if "--- DATABASE ERROR ---" in remote_output:
            return remote_output

        return remote_output

    except paramiko.AuthenticationException:
        return "\n--- SSH ERROR ---\nAuthentication failed. Check your username/password.\n"
    except Exception as e:
        return f"\n--- CONNECTION ERROR ---\nCould not connect or run command: {e}\n"
    finally:
        if 'ssh' in locals() and ssh.get_transport() is not None:
            ssh.close()

def main():
    llm = initialize_llm()

    print(f"\nUsing NetID: {DB_USER}")
    user_password = getpass.getpass(f"Enter password for {DB_USER}: ")

    print("\n--- Start Query Loop ---")
    while True:
        try:
            user_question = input("\nAsk a question (or type 'exit'): ")
            if user_question.lower() in ('exit', 'quit'):
                break

            sql_query = generate_and_extract_sql(llm, user_question)

            print(f"-> Generated Query: {sql_query}")

            if not sql_query or not sql_query.lower().startswith('select'):
                print("Error: LLM failed to generate a valid SELECT query.")
                continue

            query_result = run_remote_script(DB_USER, user_password, sql_query)

            print("\n--- QUERY RESULT ---")
            print(query_result)

        except KeyboardInterrupt:
            print("\nExiting program.")
            break
        except Exception as e:
            print(f"An unexpected error occured: {e}")
            break

if __name__ == "__main__":
    main()