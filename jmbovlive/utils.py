from django.shortcuts import render

def pml_redirect_timer_view(request,  redirect_url,  redirect_time = 20,  redirect_message = 'Thank you.', template_name = 'redirect.html'):
    return render(request, template_name,
                                {'redirect_url': redirect_url,
                                'redirect_time': redirect_time,
                                'redirect_message': redirect_message}, 
                                content_type='text/xml')