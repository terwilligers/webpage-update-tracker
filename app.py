import flask
import psycopg2
import config
import sys
import json
import collections
import requests
import hashlib
import lxml
import time
import datetime
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

def get_date():
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%m/%d/%Y')
    return timestamp

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
    Updates the hash of the url in the table
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
    Creates an entry in the site_hashes table, containing the url and hash
    '''
    query = '''insert into site_hashes(url, hash, last_update)
                values (%s, %s, %s);
            '''
    connection = get_connection()
    if connection is not None:
        try:
            get_select_query_results(connection, query, (url, new_hash, get_date(), ))
        except Exception as e:
            return False
            print(e, file=sys.stderr)
        connection.close()
        return True
    return False

def remove_url_from_database(url):
    '''
    Removes the row corresonding to the url from the database
    '''
    query = '''delete from site_hashes where url=%s
            '''
    connection = get_connection()
    if connection is not None:
        try:
            get_select_query_results(connection, query, (url, ))
        except Exception as e:
            return False
            print(e, file=sys.stderr)
        connection.close()
        return True
    return False

def get_file_hash(url):
    '''
    Calcultes the md5 hash of the html file, located at the specified url
    '''
    try:
        new_file = requests.get(url).text
        new_file = remove_script_tags(new_file)
        new_hash = hashlib.md5(new_file.encode("utf-8")).hexdigest()
    except Exception as e:
        return False
    return new_hash


def html_has_changed(url):
    '''
    Input: url- a string containing a url
    Return: a boolean stating whether the website's html has changed
            True if website was never seen before
    '''
    new_hash = get_file_hash(url)
    
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

def check_pages(urls):
    '''
    Creates a list of booleans corresponding to web pages that have changed
    '''
    results = []
    for url in urls:    
        changed = html_has_changed(url)
        results.append(changed)
    return results







app = flask.Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/') 
def get_main_page():
    ''' Main page of the pagetracker website'''
    return flask.render_template('index.html')

@app.route("/update_values")
def get_update_values():
    query = "SELECT * FROM site_hashes"
    results = {}
    
    connection = get_connection()
    if connection is not None:
        try:
            for row in get_select_query_results(connection, query):
                url = row[1]
                updated = html_has_changed(url)
                timestamp = str(row[3])
                results[url] = (updated, timestamp)
        except Exception as e:
            print(e, file=sys.stderr)
        connection.close()
    
    return json.dumps(results)


@app.route("/add_url/<path:url>")
def add_url(url):
    if url == "null":
        return json.dumps("")
    message = ""
    if is_url_in_database(url):
        message = "You are already tracking this website"
    else:
        new_hash = get_file_hash(url)
        if not new_hash:
            message = "Sorry, you entered an invaled url"
        add_url_to_database(new_hash, url)
    return json.dumps(message)

@app.route("/remove_url/<path:url>")
def remove_url(url):
    message = ""
    if is_url_in_database(url):
        result = remove_url_from_database(url)
        if not result:
            message = "Oops, there was an error with your request"
    return json.dumps(message)

@app.route("/urls")
def get_urls1():
    query = "SELECT * FROM site_hashes"
    urls = []
    
    connection = get_connection()
    if connection is not None:
        try:
            for row in get_select_query_results(connection, query):
                if row[1] not in urls:
                    urls.append(row[1])
        except Exception as e:
            print(e, file=sys.stderr)
        connection.close()
    
    return json.dumps(urls)
    
if __name__ == "__main__":
    app.run()