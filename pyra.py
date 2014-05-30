from wsgiref.simple_server import make_server
from pyramid.config        import Configurator
from pyramid.renderers     import render_to_response, JSONP
from pyramid.response      import Response
from pyramid.session       import SignedCookieSessionFactory

from pyramid.view          import view_config
from pyramid.view          import view_defaults

from libs.pi    import Pi
from libs.utils import Utils



def shipping_calc_form(request):

    session = request.session

    if 'items' not in session or 'clear' in request.GET:
        session['items'] = {}

    if 'set_rate' in request.GET:
        session['shipping_rate'] = request.GET['shipping_rate']

    else:
        session['shipping_rate'] = 0

    if 'add' in request.GET:
        if 'item_to_add' in request.GET:
            item_to_add = request.GET['item_to_add']

        if 'quantity' in request.GET:
            quantity = request.GET['quantity']

        else:
            quantity = 1

        if 'unit_price' in request.GET:
            unit_price = request.GET['unit_price'].strip()

            if not unit_price:
                return render_to_response('error.jinja2', {'error':'No unit price entered'})

            try:
                unit_price = float(unit_price)
            except Exception:
                return render_to_response('error.jinja2', {'error':'Unit price needs to be a number'})



        # [quantity,unit_price]
        session['items'][item_to_add] = {'quantity':quantity,'unit_price':unit_price}

    return render_to_response('shipping_calc_form.jinja2', 
                             {'items':session['items'],
                              'shipping_rate':session['shipping_rate']
                             })



def pi_lookup_form(request):
    return render_to_response('pi_lookup_form.jinja2', [])


def pi_lookup(request):
    utils = Utils()
    pi    = Pi()


    system = utils.search_system(request.GET['system'].strip())

    items = pi.lookup_prices(int(request.GET['tier']), 
                                 system=system[0][1])

    keys = list(items.keys())
    keys.sort()
    keys.reverse()


    
    return render_to_response('pi_lookup.jinja2',
                             {'system':system[0][0],
                              'tier':request.GET['tier'],
                              'keys':keys,
                              'items':items})

def manual_item_lookup(request):
    if 'query' not in request.GET:
        return {}

    results = {}
    utils   = Utils()

    results = utils.search_item(request.GET['query'])

    return render_to_response('manual_item_lookup.jinja2', {'results':results})

def item_autocomplete(request):
    
    if 'term' not in request.GET:
        return {}

    results = {}
    utils   = Utils()

    
    results = utils.search_item(request.GET['term'])

    # translate 

    t_results = []
    for item in results:
        t_results.append(item[0])


    return t_results



if __name__ == '__main__':
    config = Configurator()

    config.add_renderer('jsonp', JSONP(param_name='callback'))
    config.add_route('pi_lookup',      '/pi_lookup')
    config.add_route('pi_lookup_form', '/pi_lookup_form')
    config.add_route('shipping_calc_form', '/shipping_calc_form')
    config.add_route('item_autocomplete',  '/item_autocomplete')
    config.add_route('manual_item_lookup', '/manual_item_lookup')

    config.add_view(pi_lookup,      route_name='pi_lookup')
    config.add_view(pi_lookup_form, route_name='pi_lookup_form')
    config.add_view(shipping_calc_form, route_name='shipping_calc_form')
    config.add_view(item_autocomplete,  route_name='item_autocomplete', renderer='jsonp')


    session_factory = SignedCookieSessionFactory('secret')

    config.set_session_factory(session_factory)

    config.include('pyramid_jinja2')
    config.add_jinja2_search_path('templates')

    config.add_static_view(name='static', 
                           path='/home/stealth/programming/spearmint/static')

    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()
