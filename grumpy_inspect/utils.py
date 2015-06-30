"""
Grumpy Inspect common utilities
"""
import logging

from ldap3 import Server, Connection, SIMPLE, SYNC, SUBTREE, ALL

from grumpy_inspect.app import app


def query_emails_for_users(usernames):
    config = app.config
    s = Server(config['LDAP_HOST'], port=int(config['LDAP_PORT']), use_ssl=True, get_info=ALL)
    c = Connection(s, auto_bind=True, client_strategy=SYNC, user=config['LDAP_USER'], password=config['LDAP_PASSWORD'], authentication=SIMPLE, check_names=True)
    results = {}
    for username in usernames:
        c.search(config['LDAP_SEARCH_BASE'], config['LDAP_SEARCH_FILTER'] % username, SUBTREE, attributes=[config['LDAP_SEARCHED_ATTRIBUTE']])
        response = c.response
        mail = None
        if len(response) > 0:
            mail = response[0].get('attributes', {}).get('mail')
        if not mail:
            logging.warn('No email address in LDAP for user %s' % username)
        results[username] = mail
    return results
