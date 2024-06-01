import openai
import sqlite3

openai.api_key = 'sample'

table ="""
Table name: users
Columns:
    id (INTEGER): Primary key for the table.
    name (TEXT): Name of the user.
    email (TEXT): Email address of the user.

Table name: orders 
Columns:
    id (INTEGER): Primary key for the table.
    user_id (INTEGER): Foreign key referencing the id column of the users table.
    product_id (INTEGER): Foreign key referencing the id column of the products table.
    quantity (INTEGER): Quantity of the product ordered.

Table name: products
Columns:
    id (INTEGER): Primary key for the table.
    name (TEXT): Name of the product.
    price (REAL): Price of the product.

Relationships:
- The orders table has a foreign key user_id referencing the id column of the users table, establishing a one-to-many relationship between users and orders.
- The orders table has a foreign key product_id referencing the id column of the products table, establishing a one-to-many relationship between products and orders.

"""

def classify_query(question):
    prompt = f"""
You are a helpful assistant that determines if a query is related to a database or not.
If the query is related to the database, return "database".
If the query is not related to the database, return "generic".

Query: {question}
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that determines if a query is related to a database or not."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10
    )
    classification = response.choices[0].message['content'].strip().lower()
    return classification

def natural_language_to_sql(question):
    prompt = f"""
You are a helpful assistant that converts natural language questions to SQL queries.
Here are the details of the database:
{table}
Convert the following question to an SQL query based on the above table details. Return only the SQL query without any extra text or formatting:

Question: {question}
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that converts natural language questions to SQL queries."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )
    query = response.choices[0].message['content'].strip()
    return query

def validate_sql(query):
    disallowed_keywords = ["DROP", "DELETE", "INSERT", "UPDATE"]
    for keyword in disallowed_keywords:
        if keyword in query.upper():
            raise ValueError("Unsafe SQL query detected!")
    return True

def execute_sql_query(query):
    conn = sqlite3.connect('product_sample.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

def generate_natural_language_response(question, results):
    result_str = ", ".join([str(result) for result in results])
    prompt = f"""
You are a helpful assistant that converts SQL query results into natural language responses.
Here are the details of the database:
{table}
Based on the question "{question}" and the SQL query results "{result_str}", generate a natural language response.

Response should not mention anything like `Based on the query` or `SQL refers to` or any reffering statment, it should only give the response as mentioned in the examples.
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that converts SQL query results into natural language responses."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )
    natural_language_response = response.choices[0].message['content'].strip()
    return natural_language_response

def bot(question):
    try:
        query_type= classify_query(question)
        print(query_type)
        if query_type == "database":
            sql_query = natural_language_to_sql(question)
            print(f"Generated SQL Query: {sql_query}")
            if validate_sql(sql_query):
                results = execute_sql_query(sql_query)
                return generate_natural_language_response(question, results)
        else:
            return "Unable to find the data"        
    except Exception as e:
        return str(e)


