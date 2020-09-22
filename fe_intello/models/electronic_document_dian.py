# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ElectronicDocument(models.Model):
    _name = 'electronic.document.dian'
    _description = 'Electronic document DIAN for integration electronic invoice'

    name = fields.Char('Name document', compute='get_invoice_data')
    invoice = fields.Many2one('account.move', string='Invoice', required='True')
    partner = fields.Many2one('res.partner', strint='Client', compute='get_invoice_data')
    cufe = fields.Text('CUFE')
    document_key = fields.Char('Document key')
    electronic_document_detail = fields.One2many('electronic.document.detail.dian', 'electronic_document',
                                                 string='Electronic document detail')
    status_date = fields.Char('Issue date')

    _sql_constraints = [
        ('uniq_invoice', 'unique(invoice)', "Default code already exists invoice!"),
    ]

    @api.depends('invoice')
    def get_invoice_data(self):
        self.partner = self.invoice.partner_id
        self.name = self.invoice.name


class ElectronicDocumentDetail(models.Model):
    _name = 'electronic.document.detail.dian'
    _description = 'Electronic document DIAN detail'

    electronic_document = fields.Many2one('electronic.document.dian', string="Electronic document")
    date = fields.Datetime('Date')
    code_response = fields.Char('Code response')
    message_response = fields.Char('Message response')
    type_action = fields.Selection(string='Type action',
                                   selection=[('send', 'Send'), ('validation', 'Validation'), ('response', 'Response'),
                                              ('document', 'Document'), ('attachment', 'Attachment'), ('gr', 'Graphic Representation')])
    type_document = fields.Selection(string='Type document',
                                     selection=[('xml', 'XML'), ('json', 'JSON'), ('pdf', 'PDF')])
    document = fields.Binary('Document')
    document_filename = fields.Char()
    is_attachment = fields.Boolean('Attachment', default=False)

    @api.model
    def create(self, values):
        create_line = super(ElectronicDocumentDetail, self).create(values)
        create_line.attachment_document()
        return create_line

    def attachment_document(self):
        if self.is_attachment:
            name = "Fe_" + self.electronic_document.invoice.name + "." + self.type_document
            attachment = self.env['ir.attachment'].create({
                'name': name,
                'description': self.message_response[:100],
                'type': 'binary',
                'datas': self.document,
                'store_fname': name,
                'res_model': self.electronic_document.invoice._name,
                'res_id': self.electronic_document.invoice.id,
                'mimetype': 'application/' + self.type_document,
            })
            return attachment
