# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.http import request


class DemoController(WebsiteForm):

    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        if model_name == 'crm.lead':
            # Add the ip_address to the request in order to add this to the lead
            # that will be created. With this, we avoid to create a lead from
            # reveal if a lead is already created from the contact form.

            request.params['reveal_ip'] = request.httprequest.remote_addr

            if request.httprequest.referrer.find("demo") >= 0:
                request.params['name'] = "Solicitud DEMO desde WebSite"
                description = "Contacto: " + request.params['partner_name'] + ", " + request.params[
                    'contact_name'] + '\n\n'

                if request.params.get('modules', False):
                    description = description + "Se solicita para el demo los siguientes módulos: \n"
                    modules = request.params['modules'].split(',')
                    for module in modules:
                        description = description + "\t- " + module.capitalize() + "\n"
                    del request.params['modules']

                if request.params.get('others', False):
                    description = description + "\nOtros módulos solicitados: " + "\n" + request.params['others']
                    del request.params['others']

                request.params['description'] = description

        return super(DemoController, self).website_form(model_name, **kwargs)


class RoutesWebSite(http.Controller):

    @http.route('/contactus-thank-you', type='http', auth='public', website=True)
    def show_tranks_form_web_page(self):
        return http.request.render('theme_intello.thi_contactus_thanks', {})

