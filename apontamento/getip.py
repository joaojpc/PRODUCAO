def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        print "returning FORWARDED_FOR"
        ip = x_forwarded_for.split(',')[-1].strip()
    elif request.META.get('HTTP_X_REAL_IP'):
        print "returning REAL_IP"
        ip = request.META.get('HTTP_X_REAL_IP')
    else:
        print "returning REMOTE_ADDR"
        ip = request.META.get('REMOTE_ADDR')
    return ip
