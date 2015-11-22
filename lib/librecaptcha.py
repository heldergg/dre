#    Copyright (c) 2007 Renzo Carbonara <gnuk0001 at gmail dot com>
#    Based on the original implementation by Ben Maurer <support at recaptcha net>
#
#    MIT/X11 License:
#
#    Permission is hereby granted, free of charge, to any person
#    obtaining a copy of this software and associated documentation
#    files (the "Software"), to deal in the Software without
#    restriction, including without limitation the rights to use,
#    copy, modify, merge, publish, distribute, sublicense, and/or sell
#    copies of the Software, and to permit persons to whom the
#    Software is furnished to do so, subject to the following
#    conditions:
#
#    The above copyright notice and this permission notice shall be
#    included in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#    OTHER DEALINGS IN THE SOFTWARE.

import urllib2, urllib

API_SERVER = "//www.google.com/recaptcha/api"
VERIFY_SERVER = "www.google.com"

# customization (first value is used as fallback)
VALID_THEMES = ('red', 'white', 'blackglass', 'clean', 'custom')
VALID_LANGS = ('en', 'nl', 'fr', 'de', 'pt', 'ru', 'es', 'tr')

##
# TEMPLATES
##

WIDGET_TEMPLATE_CAPTCHA = '''
<script type="text/javascript">
  var RecaptchaOptions={
      theme:'%(theme)s',
      lang:'%(lang)s',
      tabindex:'%(tabindex)s',
      custom_theme_widget:'%(custom_theme_widget)s'
  };
</script>
<script type="text/javascript" src="%(ApiServer)s/challenge?k=%(PublicKey)s&hl=%(lang)s%(ErrorParam)s"></script>
<noscript>
  <iframe src="%(ApiServer)s/noscript?k=%(PublicKey)s&hl=%(lang)s%(ErrorParam)s" height="300" width="500" frameborder="0"></iframe><br/>
  <textarea name="recaptcha_challenge_field" rows="3" cols="40"></textarea>
  <input type='hidden' name='recaptcha_response_field' value='manual_challenge' />
</noscript>
'''

WIDGET_TEMPLATE = WIDGET_TEMPLATE_CAPTCHA

##
# Lib
##

class RecaptchaResponse(object):
    def __init__(self, is_valid, error_code=None):
        self.is_valid = is_valid
        self.error_code = error_code

def displayhtml (public_key, error=None, theme='red',lang='en', tabindex=0,
                 custom_theme_widget='null'):
    '''Gets the HTML to display for reCAPTCHA

    public_key -- The public api key
    error -- An error message to display (from RecaptchaResponse.error_code)
    theme -- Color Theme
    lang -- Language Code
    tabindex -- Tabindex to use for the field
    custom_theme_widge -- Custom theme widget (A string with the ID of a DOM element)
    '''

    error_param = ''
    if error:
        error_param = '&error=%s' % error

    server = API_SERVER
    theme = (VALID_THEMES[0], theme) [ theme in VALID_THEMES ]
    labg = (VALID_LANGS[0], lang) [ lang in VALID_LANGS ]

    html = WIDGET_TEMPLATE % {
        'ApiServer'          : server,
        'PublicKey'          : public_key,
        'ErrorParam'         : error_param,
        'theme'              : theme,
        'lang'               : lang,
        'tabindex'           : tabindex,
        'custom_theme_widget': custom_theme_widget }

    return html

def submit (recaptcha_challenge_field,
            recaptcha_response_field,
            private_key,
            remoteip):
    """
    Submits a reCAPTCHA request for verification. Returns RecaptchaResponse
    for the request

    recaptcha_challenge_field -- The value of recaptcha_challenge_field from the form
    recaptcha_response_field -- The value of recaptcha_response_field from the form
    private_key -- your reCAPTCHA private key
    remoteip -- the user's ip address
    """

    if not (recaptcha_response_field and recaptcha_challenge_field and
            len (recaptcha_response_field) and len (recaptcha_challenge_field)):
        return RecaptchaResponse (is_valid = False, error_code = 'incorrect-captcha-sol')

    params = urllib.urlencode ({
        'privatekey': private_key,
        'remoteip'  : remoteip,
        'challenge' : recaptcha_challenge_field,
        'response'  : recaptcha_response_field.encode('utf-8'),
        })

    verify_url = 'https://%s/recaptcha/api/verify' % VERIFY_SERVER

    request = urllib2.Request (
        url = verify_url,
        data = params,
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "User-agent": "reCAPTCHA Python"
            }
        )

    httpresp = urllib2.urlopen (request)
    return_values = httpresp.read ().splitlines ();
    httpresp.close();

    return_code = return_values [0]

    if (return_code == "true"):
        return RecaptchaResponse (is_valid=True)
    else:
        return RecaptchaResponse (is_valid=False, error_code = return_values [1])

