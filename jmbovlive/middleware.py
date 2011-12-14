from jmbovlive.utils import pml_redirect_timer_view

class PMLFormActionMiddleware(object):
    """
    Friendlier access to device / request info that Vodafone Live makes 
    available to us via HTTP Headers
    """
    def process_request(self, request):
        msisdn = request.META.get('HTTP_X_UP_CALLING_LINE_ID', None)
        
        if (request.GET.get('_action',  None) == 'POST' and msisdn != None):
            request.method = "POST"
            request.POST = request.GET


class ModifyPMLResponseMiddleware(object):
    def process_response(self, request,  response):
        msisdn = request.META.get('HTTP_X_UP_CALLING_LINE_ID', None)
        if (msisdn != None):
            if response.status_code == 301 or response.status_code == 302:
                return pml_redirect_timer_view(request, response['Location'],
                    redirect_time = 0,
                    redirect_message = 'Submitted successfully.')
            
            response['Content-type'] = 'text/xml'
        
        return response
