from flask import Flask
import psycopg2
import config
import sys
import json
import collections
import requests
import hashlib
import lxml
from lxml.html.clean import Cleaner

def get_connection():
    '''
    Returns a connection to the database\
    '''
    connection = None
    try:
        connection = psycopg2.connect(database=config.database,
                                      user=config.user,
                                      password=config.password)
    except Exception as e:
        print(e, file=sys.stderr)
    return connection

def get_select_query_results(connection, query, parameters=None):
    '''
    Executes the specified query with the specified tuple of
    parameters. Returns a cursor for the query results.
    Raises an exception if the query fails for any reason.
    '''
    cursor = connection.cursor()
    if parameters is not None:
        cursor.execute(query, parameters)
    else:
        cursor.execute(query)
    connection.commit()
    return cursor

def remove_script_tags(file):
    '''
    Input: string to remove script tags from
    Return: string with script tags removed
    '''
    cleaner = Cleaner(kill_tags = ['script'])
    result = cleaner.clean_html(file)
    return result

def is_url_in_database(url):
    '''
    Checks if a url is contained in the database
    '''
    
    query = "select * from site_hashes"
    found = False
    connection = get_connection()
    if connection is not None:
        try:
            for row in get_select_query_results(connection, query):
                if url == row[1]:
                    found = True
                    break
        except Exception as e:
            print(e, file=sys.stderr)
        connection.close()
    return found

def get_old_hash(url):
    '''
    Gets the current hash of a page in the database,
    if page not in database returns false
    '''
    query = "select hash from site_hashes where url = %s;"
    old_hash = ""
    connection = get_connection()
    if connection is not None:
        try:
            for row in get_select_query_results(connection, query, (url, )):
                old_hash = row[0]
            return old_hash
        except Exception as e:
            print(e, file=sys.stderr)
        connection.close()
    return False

def update_hash(new_hash, url):
    '''
    we update the hash of the url in the table
    '''
    query = '''update site_hashes
                set hash = %s
                where url = %s;
            '''
    connection = get_connection()
    if connection is not None:
        try:
            get_select_query_results(connection, query, (new_hash, url, ))
        except Exception as e:
            print(e, file=sys.stderr)
        connection.close()
        return True
    return False

def add_url_to_database(new_hash, url):
    '''
    we create an entry in the table, containing the url and hash
    '''
    query = '''insert into site_hashes(url, hash)
                values (%s, %s);
            '''
    connection = get_connection()
    if connection is not None:
        try:
            get_select_query_results(connection, query, (url, new_hash, ))
        except Exception as e:
            print(e, file=sys.stderr)
        connection.close()
        return True
    return False


def html_has_changed(url):
    '''
    Input: url- a string containing a url
    Return: a boolean stating whether the website's html has changed
            True if website was never seen before
    '''
    
    new_file = requests.get(url).text
    new_file = remove_script_tags(new_file)
    new_hash = hashlib.md5(new_file.encode("utf-8")).hexdigest()
    
    #add url and hash to the database if no entry
    in_database = is_url_in_database(url)
    if not in_database:
        add_url_to_database(new_hash, url)
        return True
    
    #otherwise we check whether hash has changed
    old_hash = get_old_hash(url)
    if old_hash == new_hash:
        has_changed = False
    else:
        has_changed = True
        # update entry in database
        update_hash(new_hash, url)
    return has_changed


app = Flask(__name__)

@app.route("/testdb")
def testdb():
    query = "SELECT * FROM site_hashes"
    hashes = []
    
    connection = get_connection()
    if connection is not None:
        try:
            for row in get_select_query_results(connection, query):
                if row[2] not in hashes:
                    hashes.append(row[2])
        except Exception as e:
            print(e, file=sys.stderr)
        connection.close()
    
    return json.dumps(hashes)
    

@app.route("/indb")
def hello():
    #indb = is_url_in_database('https://apps.carleton.edu/campus/registrar/schedule/proposed/')
    indb = is_url_in_database('https://fivethirtyeight.com')
    if indb:
       return "in db"
    else:
       return "not in db"

@app.route("/check_page")
def check_page():
    changed = html_has_changed('https://apps.carleton.edu/campus/registrar/schedule/proposed/')
    #changed = html_has_changed('https://fivethirtyeight.com')
    #print(url)
    #changed = html_has_changed(url)
    if changed:
        return "Page has changed since last visit"
    else:
        return "Page has not changed"
    
if __name__ == "__main__":
    app.run()