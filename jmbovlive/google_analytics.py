import time
import uuid
import random
import urllib
import httplib2
import re
from hashlib import md5
from django.conf import settings

from jmbo_analytics import CAMPAIGN_TRACKING_PARAMS
from celery.task import task


def get_ip(remote_address):
    if not remote_address:
        return ''
    matches = re.match('^([^.]+\.[^.]+\.[^.]+\.).*', remote_address)
    if matches:
        return matches.groups()[0] + "0"
    else:
        return ''


def get_visitor_id(guid, account, user_agent, cookie):
    """Generate a visitor id for this hit.
    If there is a visitor id in the cookie, use that, otherwise
    use the guid if we have one, otherwise use a random number.
    """
    if cookie:
        return cookie
    message = ""
    if guid:
        # create the visitor id using the guid.
        message = guid + account
    else:
        # otherwise this is a new user, create a new random id.
        message = user_agent + str(uuid.uuid4())
    md5String = md5(message).hexdigest()
    return "0x" + md5String[:16]


def gen_utma(domain_name):
    domain_hash = 0
    g = 0
    i = len(domain_name) - 1
    while i >= 0:
        c = ord(domain_name[i])
        domain_hash = ((domain_hash << 6) & 0xfffffff) + c + (c << 14)
        g = domain_hash & 0xfe00000
        if g != 0:
            domain_hash = domain_hash ^ (g >> 21)
            i = i - 1
            rnd_num = str(random.randint(1147483647, 2147483647))
            time_num = str(time.time()).split('.')[0]
            _utma = '%s.%s.%s.%s.%s.%s' % (domain_hash, rnd_num, time_num,
                time_num, time_num, 1)
    return _utma


def google_analytics(request, response):
    VERSION = '4.4sh'
    COOKIE_NAME = '__utmmobile'
    COOKIE_PATH = '/'
    COOKIE_USER_PERSISTENCE = 63072000
    CAMPAIGN_PARAMS_KEY = 'ga_campaign_params'

    # Trivial case
    try:
        assert settings.JMBO_ANALYTICS['google_analytics_id']
    except:
        return

    # pass on the referer if present
    referer = request.META.get('HTTP_REFERER', None)
    path = request.path
    meta = request.META

    try:
        account = settings.JMBO_ANALYTICS['google_analytics_id']
    except:
        raise Exception("No Google Analytics ID configured")

    """Sends a request to google analytics."""
    meta = request.META
    time_tup = time.localtime(time.time() + COOKIE_USER_PERSISTENCE)

    # determine the domian
    domain = meta.get('HTTP_HOST', '')

    # try and get visitor cookie from the request
    user_agent = meta.get('HTTP_USER_AGENT', 'Unknown')
    cookie = request.COOKIES.get(COOKIE_NAME)
    visitor_id = get_visitor_id(meta.get('HTTP_X_DCMGUID', ''),
                    account, user_agent, cookie)
    # build the parameter collection
    params = {
        'utmwv': VERSION,
        'utmn': str(random.randint(0, 0x7fffffff)),
        'utmhn': domain,
        'utmsr': '',
        'utme': '',
        'utmr': referer,
        'utmp': path,
        'utmac': account,
        'utmcc': '__utma=%s;' % gen_utma(domain),
        'utmvid': visitor_id,
        'utmip': meta.get('REMOTE_ADDR', ''),
    }

    # retrieve campaign tracking parameters from session
    campaign_params = request.session.get(CAMPAIGN_PARAMS_KEY, {})

    # update campaign params from request
    for param in CAMPAIGN_TRACKING_PARAMS:
        if param in request.GET:
            campaign_params[param] = request.GET[param]

    # store campaign tracking parameters in session
    request.session[CAMPAIGN_PARAMS_KEY] = campaign_params
    # add campaign tracking parameters if provided
    params.update(campaign_params)
    # construct the gif hit url
    utm_gif_location = "http://www.google-analytics.com/__utm.gif"
    utm_url = utm_gif_location + "?" + urllib.urlencode(params)

    # always try and add the cookie to the response
    response.set_cookie(
        COOKIE_NAME,
        value=visitor_id,
        expires=time.strftime('%a, %d-%b-%Y %H:%M:%S %Z', time_tup),
        path=COOKIE_PATH,
    )

    #use celery to send google analytics tracking
    send_ga_tracking.delay(utm_url, user_agent, meta)

    return response


@task(ignore_result=True)
def send_ga_tracking(utm_url, user_agent, meta):
    # send the request
    http = httplib2.Http()
    try:
        resp, content = http.request(
            utm_url, 'GET',
            headers={
                'User-Agent': user_agent,
                'Accepts-Language:': meta.get('HTTP_ACCEPT_LANGUAGE', '')
            }
        )
    except httplib2.HttpLib2Error:
        pass
