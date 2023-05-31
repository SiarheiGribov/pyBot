# -*- coding: utf-8 -*-

import time
import requests
import configparser

"""
See [[Special:BotPassword]]. Credentials.ini syntax:

[bot]
login = Botname@botpasswordname
password = botpassword

[main]
login = Username@botpasswordname
password = botpassword
"""

credentials = configparser.ConfigParser()
credentials.read('pyBot/credentials.ini')
USER_AGENT = {'User-Agent': 'pyBot (iluvatarbot@tools.wmflabs.org); Python 3.x (requests); Login'}
retry_cfg = {'max_times_retry': 30, 'times_retry': 0}


def retry(is_bot: bool, token_type: str, server: str, phase: str, reason: str, delay: int = 300):
    """
    :param phase: execution phase, where an exception occurred.
    :param reason: description of exception.
    :param delay: delay in seconds. Default: 300.
    """
    global retry_cfg
    retry_cfg['times_retry'] += 1
    if retry_cfg['times_retry'] == retry_cfg['max_times_retry']:
        exit()
    print(f'{phase}: {reason}. Retry ({retry_cfg["times_retry"]}) after {delay} sec.')
    time.sleep(delay)
    login(is_bot=is_bot, token_type=token_type, server=server)


def login(is_bot: bool = True, token_type: str = 'csrf', server: str = "ru.wikipedia"):
    """
    :param is_bot: a 'bot' section with credentials in a cfg file or a 'main' section; Default: 'bot'.
    :param token_type: 'createaccount', 'csrf'. deleteglobalaccount', 'login', 'patrol', 'rollback',
    'setglobalaccountstatus', 'userrights', 'watch'. Default: 'csrf'.
    :param server: domain name. E.g., 'en.wikipedia', 'ru.wikinews'. default: 'ru.wikipedia'.
    :return: token and cookies
    """
    acc_type = 'bot' if is_bot else 'main'
    username, password = credentials[acc_type]['login'], credentials[acc_type]['password']

    req = {'action': 'query', 'format': 'json', 'utf8': '', 'meta': 'tokens', 'type': 'login'}
    r1 = requests.post(f'https://{server}.org/w/api.php', data=req, headers=USER_AGENT)

    req = {'action': 'login', 'format': 'json', 'utf8': '', 'lgname': username, 'lgpassword': password,
           'lgtoken': r1.json()['query']['tokens']['logintoken']}
    r2 = requests.post(f'https://{server}.org/w/api.php', data=req, cookies=r1.cookies, headers=USER_AGENT)
    r2_status = r2.json()['login']['result']
    if r2_status != 'Success':
        retry(is_bot=is_bot, token_type=token_type, server=server, phase='Getting cookies', reason=r2_status)

    req = {'action': 'query', 'format': 'json', 'meta': 'tokens', 'type': token_type}
    r3 = requests.post(f'https://{server}.org/w/api.php', data=req, cookies=r2.cookies, headers=USER_AGENT).json()
    token = r3['query']['tokens'][f'{token_type}token']

    if token == "+\\":
        retry(is_bot=is_bot, token_type=token_type, server=server, phase='Getting a token', reason='token is empty')

    if __name__ == '__main__':
        print(token_type, token, r2.cookies)

    return token, r2.cookies


if __name__ == '__main__':
    login()
