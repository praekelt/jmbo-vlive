import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'jmbovlive.settings'

from django.test import TestCase
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.http import QueryDict
from jmbovlive.middleware import PMLFormActionMiddleware, ModifyPMLResponseMiddleware

class TestCase(TestCase):
    
    def test_form_action_middleware(self):
        request = HttpRequest()
        request.method = 'GET'
        request.META = {'HTTP_X_UP_CALLING_LINE_ID': '0123456789'}
        request.GET = QueryDict('_action=POST')
        
        middleware = PMLFormActionMiddleware()
        middleware.process_request(request)
        
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.POST, request.GET)
        
    def test_form_action_middleware(self):
        middleware = ModifyPMLResponseMiddleware()
        
        request = HttpRequest()
        request.method = 'GET'
        request.META = {'HTTP_X_UP_CALLING_LINE_ID': '0123456789'}
        request.GET = QueryDict('_action=POST')
        
        response = HttpResponse('Hello world')        
        middleware.process_response(request, response)
        
        self.assertEqual(response['Content-type'], 'text/xml')
        
        response = middleware.process_response(request, HttpResponseRedirect('/home/'))
        
        self.assertEqual(response['Content-type'], 'text/xml')
        self.assertContains(response, '<TIMER href="/home/')
        self.assertContains(response, 'Please wait while we automatically redirect you.')
        

