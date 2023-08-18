# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug


class CustomEvent(http.Controller):

    @http.route(['/event/<model("event.event"):event>/updateinformation'], type='json', auth="public", methods=['POST'], website=True)
    def registration_new(self, event, **post):
        values_input = post
        if (values_input['compania'] and values_input['orden']):
            query_data = request.env[
                'event.registration'].sudo().search([('partner_id.company_name',
                                                      '=',
                                                      values_input['compania']),
                                                     ('sale_order_id',
                                                      '=', values_input['orden'].upper()),
                                                     ('event_id', '=', event.id)])
        else:
            query_data = ''
        regsters = {'data_update': query_data,
                    'event': event}

        return request.env['ir.ui.view']._render_template("custom_event.custom_event_modal", regsters)

    @http.route(['/event/<model("event.event"):event>/updateregister'], type='http', auth="public", methods=['POST'], website=True)
    def update_information(self, event, **post):
        if post:
            number_cicl = int(len(post) / 4)
            for line in range(number_cicl):
                visitor = request.env[
                    'event.registration'].search([('id', '=', int(post[str(line+1) + '-id'])),
                                                  ('event_id', '=', event.id)])
                if visitor:
                    if (visitor.name != post[str(line+1) + '-name'] or
                        visitor.email != post[str(line+1) + '-email'] or
                        visitor.phone != post[str(line+1) + '-phone']):
                        visitor.update({
                            'name': post[str(line+1) + '-name'],
                            'email': post[str(line+1) + '-email'],
                            'phone': post[str(line+1) + '-phone']
                        })

        redirect = request.redirect('/event/%s/register' % slug(event))

        return redirect
