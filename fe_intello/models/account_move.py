import werkzeug
from odoo import api, fields, models, _, exceptions
import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    method = fields.Many2many('ln10_co_intello.diancodes')
    payment_type = fields.Selection(string='Payment Type', selection=[('1', 'Debito'), ('2', 'Credito')], default='1',
                                    states={'draft': [('readonly', False)]}, readonly=True)
    payment_method = fields.Many2one('ln10_co_intello.diancodes', string='Payment Method',
                                     domain=[('type', '=', 'paymentmethod')], states={'draft': [('readonly', False)]},
                                     readonly=True)
    export_bill = fields.Boolean('Export bill', copy=False, states={'draft': [('readonly', False)]}, readonly=True)
    send_status = fields.Boolean('Send status', default=False, copy=False)
    partner_response = fields.Char('Partner response',
                                   help="This field is to mark the acknowledgment of receipt of the invoice")
    send_registry = fields.Many2one('electronic.document.dian', string="Send registry", copy=False)
    fe_qr_code = fields.Text('QR Code', copy=False)

    validate_status = fields.Boolean('Validate status', copy=False)

    check_is_active = fields.Boolean(compute="_compute_active", default=False)
    check_is_online = fields.Boolean(compute="_compute_online", default=False)
    electronic_document_status = fields.Selection(string='Electronic document status',
                                                  selection=[('0', 'Start'), ('1', 'Attachment'), ('2', 'Send'),
                                                             ('3', 'Valid'), ('4', 'Graphic Representation'),
                                                             ('5', 'Mail'), ('6', 'Delivered')], default='0')

    # Method for notification messages
    def notification(self, tittle, message):
        """Crea la notificación en forma de sticker"""

        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'danger',
                'title': _(tittle),
                'message': _(message),
                'sticky': False,
            }
        }
        return notification

    # Compute Methods
    def _compute_active(self):
        parameter = self.env['ir.config_parameter'].sudo()
        fe_active = parameter.get_param('res.config.settings.fe_active')

        if fe_active:
            self.check_is_active = True
        else:
            self.check_is_active = False

    def _compute_online(self):
        parameter = self.env['ir.config_parameter'].sudo()
        fe_online = parameter.get_param('res.config.settings.fe_online')

        if fe_online:
            self.check_is_online = True
        else:
            self.check_is_online = False

    @api.onchange('value_footer_discount')
    def validation_percent_discount(self):
        """Valida que el Campo  value_footer_discount no sobre pase el 100%
            y si es asi lo devuelve a 100"""
        if self.invoice_footer_discount == '1':
            if self.value_footer_discount > 100:
                self.value_footer_discount = 100

    # Validations Methods
    @api.constrains('journal_id')
    def _validation_invoice_resolution(self):
        parameter = self.env['ir.config_parameter'].sudo()
        fe_active = parameter.get_param('res.config.settings.fe_active')

        if fe_active:
            if self.journal_id:
                if self.journal_id.type == 'sale':

                    if self.type == 'out_invoice':
                        if not self.journal_id.invoice_resolution.type == 'electronic':
                            raise exceptions.Warning(_("The type of invoice resolution must be electronic"))

                    if self.type == 'out_refund':
                        if self.journal_id.note_resolution:
                            if not self.journal_id.note_resolution.type == 'electronic':
                                raise exceptions.Warning(_("The type of invoice resolution must be electronic"))
                        else:
                            raise exceptions.Warning(_("The journal must have a resolution of credit note"))

    def _validate_resolution_data(self, next_number):
        resolution_data = super(AccountMove, self)._validate_resolution_data(next_number)
        self._validation_invoice_resolution()

        return resolution_data

    def validate_fields_document(self):
        message = ""
        if not self.payment_type:
            if message == "":
                message = "<ul><li>" + "Payment Type" + "</li></ul>"
            else:
                message = message + "<li>" + "Payment Type" + "</li>"
        if not self.payment_method:
            if message == "":
                message = "<ul><li>" + "Payment Method" + "</li></ul>"
            else:
                message = message + "<ul><li>" + "Payment Method" + "</li></ul>"
        if not self.invoice_payment_term_id:
            if message == "":
                message = "<ul><li>" + "Invoice Payment Term" + "</li></ul>"
            else:
                message = message + "<ul><li>" + "Invoice Payment Term" + "</li></ul>"

        else:
            if not message == "":
                message = _(message)
                return message

    def validate_fields_country(self):
        message = ""
        if not self.partner_id.country_id:
            if message == "":
                message = "<ul><li>" + _('Country of Customer') + "</li></ul>"
            else:
                message = message + "<ul><li>" + _('Country of Customer') + "</li></ul>"
        if not self.partner_id.country_id.code:
            if message == "":
                message = "<ul><li>" + _('Country Code of Customer') + "</li></ul>"
            else:
                message = message + "<ul><li>" + _('Country Code of Customer') + "</li></ul>"
        if not self.partner_id.city:
            if message == "":
                message = "<ul><li>" + _('City of Customer') + "</li></ul>"
            else:
                message = message + "<ul><li>" + _('City of Customer') + "</li></ul>"
        if not self.partner_id.state_id:
            if message == "":
                message = "<ul><li>" + _('Department of Customer') + "</li></ul>"
            else:
                message = message + "<ul><li>" + _('Department of Customer') + "</li></ul>"
        if not self.partner_id.zip:
            if message == "":
                message = "<ul><li>" + _('Postal Code of Customer') + "</li></ul>"
            else:
                message = message + "<ul><li>" + _('Postal Code of Customer') + "</li></ul>"

        if not message == "":
            message = _(message)
            return message

    def validate_unite_measure(self):
        message = ""

        for verify in self.invoice_line_ids:
            if not verify.product_uom_id.dian_code:
                message = _("Please check the approval of the unit of measure")

        if not message == "":
            return message

    @api.depends('partner_id')
    def partner_fields(self):
        """Completa los campos cuando el partner_id sea seleccionado"""

        self.method = self.partner_id.payment_method
        self.invoice_payment_term_id = self.partner_id.property_payment_term_id.id
        self.payment_type = self.partner_id.payment_type

    # Inherit Buttons
    def action_post(self):
        if self.type in ['out_invoice', 'out_refund']:
            parameter = self.env['ir.config_parameter'].sudo()
            fe_online = parameter.get_param('res.config.settings.fe_online')
            fe_active = parameter.get_param('res.config.settings.fe_active')

            validate = self.validate_fields_document()
            if validate:
                return self.notification('The following fields are invalid:', validate)

            validate_country = self.validate_fields_country()
            if validate_country:
                return self.notification('The following fields are invalid:', validate_country)

            if fe_online and fe_active:
                self.partner_id.validate_fields_invoice()
                validate_unit_measure = self.validate_unite_measure()
                if validate_unit_measure:
                    return self.notification("Error:", validate_unit_measure)

            super(AccountMove, self).action_post()

            if fe_online and fe_active:
                self.process_document()
        else:
            super(AccountMove, self).action_post()

    def button_draft(self):
        if self.send_status:
            return self.notification('Error', "No se pudo completar la acción por que la factura ya se envio a la DIAN")
        return super(AccountMove, self).button_draft()

    # Methods for fe_invoice
    def send_document(self):
        """Metodo dummie para la creación de la data del documento"""
        send_registry = self.cu_electronic_document_dian(self.id, {'cufe': "", 'document_key': "", 'status_date': ""},
                                                         0)
        self.update({'send_registry': send_registry.id})

    def process_document(self):
        """Procesa el documento y hace el envio a la DIAN"""
        parameter = self.env['ir.config_parameter'].sudo()
        fe_email = parameter.get_param('res.config.settings.fe_send_mail')

        for posted_document in self:
            posted_document.send_document()
            posted_document.create_qr_code()
            posted_document.attach_pdf_invoice()

            if fe_email:
                posted_document.action_send_email(posted_document)

    def update_electronic_document_status(self, status):
        """
        Función que actualiza el estado del electronic document en la factura (account.move)
        @author Julián Valdés - Intello Idea
        @param status: Campo representado como una barra de estados, estados posibles
                        ('1', 'Attachment'), ('2', 'Send'),
                        ('3', 'Graphic Representation'),
                        ('4', 'Valid'), ('5', 'Mail')
        """
        self.update({
            'electronic_document_status': str(status)
        })

    def cu_electronic_document_dian(self, invoice_id, parameters, status=None):
        """
        Función que crea un nuevo registro o lo actualiza si ya exite en el modelo electronic.document.dian
        @author Julián Valdés - Intello Idea
        @param invoice_id: Id de la factura a la cual se le agregara el documento electronico
        @param parameters: Diccionario con los parametros para un nuevo documento electronico
            {
                'cufe': "",
                'document_key': "",
                'status_date': ""
            }
        """
        electronic_document = self.env['electronic.document.dian'].search([('invoice', '=', invoice_id)])
        if electronic_document.invoice.id == invoice_id:
            electronic_document.update({
                'cufe': parameters['cufe'] if 'cufe' in parameters else "",
                'document_key': parameters['document_key'] if 'document_key' in parameters else "",
                'status_date': parameters['status_date'] if 'status_date' in parameters else "",
            })
            self.update_electronic_document_status(status)
            return electronic_document
        else:
            e_document = self.env['electronic.document.dian'].create({
                'invoice': invoice_id,
                'cufe': parameters['cufe'],
                'document_key': parameters['document_key'],
                'status_date': parameters['status_date']
            })
            self.update_electronic_document_status(status)
            return e_document

    def cu_electronic_document_detail_dian(self, invoice_id, parameters, status=None):
        """
        Función que crea un nuevo registro en el modelo electronic.document.detail.dian, si ya
        existe una cabecera en electronic.document.detail.dian
        @author Julián Valdés - Intello Idea
        @param invoice_id: Id de la factura a la cual se le agregara la transacción
        @param parameters: Diccionario con los parametros para una nueva transacción
            {
                'electronic_document': 0,
                'date': '00/00/0000',
                'code_response': 000,
                'message_response': '',
                'type_action': '',
                'type_document': '',
                'document_filename': '',
                'document': 0,
                'is_attachment': False,
            }
        """
        electronic_document = self.env['electronic.document.dian'].search([('invoice', '=', invoice_id)])
        if electronic_document.invoice.id == invoice_id:
            e_document = self.env['electronic.document.detail.dian'].create({
                'electronic_document': electronic_document.id,
                'date': parameters['date'],
                'code_response': parameters['code_response'],
                'message_response': parameters['message_response'],
                'type_action': parameters['type_action'],
                'type_document': parameters['type_document'],
                'document_filename': parameters['document_filename'],
                'document': parameters['document'],
                'is_attachment': parameters['is_attachment'],
            })
            self.update_electronic_document_status(status)
        else:

            print("create an electronic document first")

    def create_qr_code(self):
        account_move_taxes = self.env['account.move.taxes'].search([('move_id', '=', self.id)])
        val_iva = 0
        val_otro_im = 0

        for account_move_tax in account_move_taxes:
            if account_move_tax.tax_type_id.type == "01":
                val_iva += account_move_tax.amount
            else:
                val_otro_im += account_move_tax.amount

        qr_code = "NumFac: " + str(self.name) + "\n" + \
                  "FecFac: " + str(self.invoice_date) + "\n" + \
                  "NitFac: " + str(self.company_id.partner_id.vat) + "\n" + \
                  "DocAdq: " + str(self.partner_id.vat) + "\n" + \
                  "ValFac: " + str(self.amount_untaxed) + "\n" + \
                  "ValIva: " + str(val_iva) + "\n" + \
                  "ValOtroIm: " + str(val_otro_im) + "\n" + \
                  "ValFacIm: " + str(self.amount_total) + "\n" + \
                  "CUFE: " + str(self.send_registry.cufe) + "\n" + \
                  "https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=" + str(self.send_registry.cufe)

        self.update({
            "fe_qr_code": qr_code,
        })

    @api.model
    def build_fe_qr_code(self):
        qr_code_string = self.fe_qr_code
        qr_code_url = '/report/barcode/?type=%s&value=%s&width=%s&height=%s&humanreadable=1' % (
            'QR', werkzeug.url_quote_plus(qr_code_string), 128, 128)

        return qr_code_url

    def attach_pdf_invoice(self):
        pdf = self.env.ref('account.account_invoices').render_qweb_pdf(self.ids)
        b64_pdf = base64.b64encode(pdf[0])
        parameter = self.env['ir.config_parameter'].sudo()
        fe_own_gr = parameter.get_param('res.config.settings.fe_own_gr')
        if fe_own_gr:
            self.send_gr_document(b64_pdf)
        return b64_pdf

    def send_gr_document(self, b64):
        detail = {
            'electronic_document': 0,
            'date': '00/00/0000',
            'code_response': 000,
            'message_response': '',
            'type_action': '',
            'type_document': '',
            'document_filename': '',
            'document': 0,
            'is_attachment': False,
        }

    def action_send_email(self, posted_document):
        mail_template = self.env.ref('fe_intello.fe_email_template', raise_if_not_found=False)
        attach_document = self.env['ir.attachment'].search(
            [('res_id', '=', posted_document.id), ('res_model', '=', posted_document._name)])

        if attach_document:
            for attach in attach_document:
                mail_template.attachment_ids = [(6, 0, [attach.id])]

        mail_template.send_mail(posted_document.id, force_send=True)
