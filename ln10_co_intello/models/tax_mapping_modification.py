# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions, _
import inspect


def get_class_from_frame(fr):
    """
    Función que permite obtener la clase que genera el llamado al método map_tax. Así determinar si es una compra o una
    venta en el cálculo de los impuestos.
    :param fr: Execution Frame
    :return: Object Class
    """

    args, _, _, value_dict = inspect.getargvalues(fr)
    # we check the first parameter for the frame function is
    # named 'self'
    if len(args) and args[0] == 'self':
        # in that case, 'self' will be referenced in value_dict
        instance = value_dict.get('self', None)
        if instance:
            # return its class
            return getattr(instance, '__class__', None)
    # return None otherwise
    return None


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    key_dian = fields.Many2one('ln10_co_intello.diancodes', ondelete='cascade', string='DIAN Code', required=True,
                               domain=[('type', '=', 'fiscalposition')])

    def map_tax(self, taxes, product=None, partner=None):
        """
        Sobreescritura del método para cambio funcional de Locaclización Colombiana.
        Se busca establecer los impuestos de acuerdo a la Relación entre la Posición Fiscal de la Compañía y el Partner,
        definidos en el modelo ln10_co_intello.relationfiscalpositions

        :param taxes: Impuestos que son suceptibles de ser aplicados
        :param product: Producto registrado en la línea.
        :param partner: Partner (Cliente/Proveedor) registrado en la operación.
        :return: Lista de impuestos a aplicar.
        """

        """
        Se determina la operación (Ventas/Compras) de acuerdo a la clase que invoca el método.
        """
        frame = inspect.stack()[1][0]
        class_name = str(get_class_from_frame(frame)).split(".")[2]
        # print(class_name)

        if class_name in ('purchase', 'stock'):
            type = 'P'
        else:
            type = 'S'

        """
        Se válida que todos los posibles impuestos estén correctamente parametrizados en Tipo de impuesto.
        """
        for tax in taxes:
            if not (tax.tax_type):
                raise exceptions.ValidationError(
                    "Por favor verificar\nImpuestos asosciados al Producto no tiene un tipo de impuesto válido")

        """
        Se válida la Posición Fiscal de la compañía a traves del partner asociado a la misma. 
        """
        fpos_company = self.company_id.partner_id.property_account_position_id
        if not fpos_company:
            raise exceptions.ValidationError("Por favor verificar\nPosición Fiscal de la Compañia no ha sido asignada")

        """
        Se válida la Posición Fiscal del Tercero (Cliente/Proveedor)
        """
        fpos_partner = partner.property_account_position_id
        if not fpos_partner:
            raise exceptions.ValidationError("Por favor verificar\nPosición Fiscal del Tercero no ha sido asignada")

        """
        Se consulta y almacena la realción entre posiciones fiscales para determinar los impuestos por su
        Tipo de Impuesto asociado. En caso de no encontrar, generará un error.
        """
        relation_fpos = self.env['ln10_co_intello.relationfiscalpositions']
        relation_fpos_id = relation_fpos.findRelation(type, fpos_partner, fpos_company)

        if not relation_fpos_id:
            raise exceptions.ValidationError(
                "Por favor verificar\nLa definición de Impuestos entre la Compañia y el Tercero no está definida")

        return relation_fpos_id.map_tax(taxes)


class TaxesType(models.Model):
    _name = 'ln10_co_intello.taxestype'
    _description = "Colombian Taxes Type defined by DIAN"

    code = fields.Char(required=True, string="Code")
    type = fields.Selection([('01', 'Impuesto Valor Agregado'),
                             ('02', 'Impuesto al Consumo'),
                             ('03', 'Impuesto de Industria, Comercio y Avisos'),
                             ('04', 'Impuesto Nacional al Consumo'),
                             ('05', 'Retención sobre el IVA'),
                             ('06', 'Retención en la Fuente"'),
                             ('07', 'Retención sobre el ICA"'),
                             ('20', 'Fomento Horticultura'),
                             ('21', 'Impuesto de Timbre'),
                             ('22', 'Impuesto al Consumo de Bolsa Plástica'),
                             ('23', 'Impuesto Nacional al Carbono'),
                             ('24', 'Impuesto Nacional al Combustible'),
                             ('25', 'SobreTasa al Combustible'),
                             ('26', 'Contribución Minoristas Combustiles'),
                             ('ZZ', 'Otros Tributos, Tasas y Contribuciones')], string="DIAN Type")

    name = fields.Char(required=True, index=True, string="Name")
    operation = fields.Selection([('S', 'Sum'),
                                  ('R', 'Substraction')], string="Operation")

    _sql_constraints = [('code_uniq', 'UNIQUE(code)', 'Duplicate Code value is not allowed!'),
                        ('name_uniq', 'UNIQUE(name)', 'Duplicate Name value is not allowed!')]


class RealitonFiscalPositions(models.Model):
    _name = 'ln10_co_intello.relationfiscalpositions'
    _description = 'Define Fiscal Position Relations'

    name = fields.Char(required=True)
    src_fiscal_position = fields.Many2one('account.fiscal.position', string='Origin Fiscal Position', required=True,
                                          ondelete='cascade')
    dst_fiscal_position = fields.Many2one('account.fiscal.position', string='Destination Fiscal Position',
                                          required=True, ondelete='cascade')

    tax_types_ids = fields.One2many('ln10_co_intello.aplicationtaxestype', 'relation_fiscal_position_id',
                                    string='Tax Type Application')

    _sql_constraints = [('name_uniq', 'UNIQUE(name)', 'Duplicate Name value is not allowed!')]

    @api.model
    def findRelation(self, type, fpos_partner, fpos_company):
        """
        Busca la Relación de acuerdo a los parámetros recibidos.

        :param type: Tipo de Operación (S - Sale(Compra), P - Purchase(Compras))
        :param fpos_partner: Posición Fiscal del Tercero (Clinete/Proveedor)
        :param fpos_company: Posisicón Fiscal de la Compañía
        :return: Devuelve la relación solicitada si la encuentra
        """
        if type != 'S' and type != 'P':
            raise exceptions.ValidationError("Please verify, Type is not allowed, S or P are the possible values")

        if type == 'S':
            return self.search(
                [("src_fiscal_position", "=", fpos_company.id), ("dst_fiscal_position", "=", fpos_partner.id)])
        else:
            return self.search(
                [("src_fiscal_position", "=", fpos_partner.id), ("dst_fiscal_position", "=", fpos_company.id)])

    @api.model
    def map_tax(self, taxes):
        """
        Determina de acuerdo a los impuestos (taxes) recibidos y la parametrización realizada por el usuario para la
        Relación entre las Posiciones Fiscales, cuales son los impuestos que realmente debe aplicar según su
        Tipo de Impuesto parametrizado.

        :param taxes: Lista de Objetos de impuestos (account.tax) suceptibles de ser aplicados.
        :return: Lista de Impuestos que deben ser aplicados, de acuerdo a la definición de la Relación.
        """
        result = self.env['account.tax'].browse()

        if not self.tax_types_ids:
            raise exceptions.ValidationError(
                _("Please verify, Tax Type is not assigned in tax definition between Partner and Company Fiscal Position "))

        for tax_type in self.tax_types_ids:
            if tax_type.apply_tax:
                taxes_to_apply = taxes.filtered(lambda r: r.tax_type.id == tax_type.tax_type.id)
                for tax in taxes_to_apply:
                    result |= tax

        return result


class TaxesTypeAplication(models.Model):
    _name = 'ln10_co_intello.aplicationtaxestype'
    _description = 'Define Tax Type application for Fiscal Position Relations'

    relation_fiscal_position_id = fields.Many2one('ln10_co_intello.relationfiscalpositions', 'Fiscal Position Relation')
    tax_type = fields.Many2one('ln10_co_intello.taxestype', 'Tax Type', required=True)
    apply_account = fields.Boolean(string="Apply Account", default=False)
    apply_tax = fields.Boolean(string="Apply Tax", default=False)


class AccountMoveTaxes(models.Model):
    _name = 'account.move.taxes'
    _description = 'Resume of taxes applied in move'

    move_id = fields.Many2one('account.move')
    tax_type_id = fields.Many2one('ln10_co_intello.taxestype')
    percent = fields.Float()
    amount = fields.Float()
    base = fields.Float()
    line_ids = fields.One2many('account.move.taxes.line', 'move_tax_id')

    _sql_constraints = [('MoveType_uniq', 'UNIQUE(move_id,tax_type_id,percent)',
                         'Duplicate Tax Type value in the same Move is not allowed!')]


class AccountMoveTaxesLine(models.Model):
    _name = 'account.move.taxes.line'
    _description = 'Resume of Taxes applied in move'
    _order = 'move_id, tax_type_id'

    move_tax_id = fields.Many2one('account.move.taxes')
    move_id = fields.Many2one('account.move')
    move_line_id = fields.Many2one('account.move.line')
    tax_type_id = fields.Many2one('ln10_co_intello.taxestype')
    percent = fields.Float()
    amount = fields.Float()
    base = fields.Float()

    @api.model
    def create(self, vals_list):
        """
        Sobreescritura del método que permite actualizar o crear el resumen en el modelo account.move.taxes
        :param vals_list: Lista de valores a crear
        :return: Objeto de Línea recién creado
        """

        move_tax = self.env['account.move.taxes'].search(
            ['&', ('id', '=', vals_list['move_tax_id']), ('move_id', '=', vals_list['move_id']),
             ('tax_type_id', '=', vals_list['tax_type_id']), ('percent', '=', vals_list['percent'])])

        if move_tax:
            move_tax.update({
                'amount': move_tax.amount + vals_list['amount'],
                'base': move_tax.base + vals_list['base'],
            })

        return super(AccountMoveTaxesLine, self).create(vals_list)

    def unlink(self):
        """
        Sobreescritura del método que permite actualizar el resumen en el modelo account.move.taxes
        :return: Objeto de línea recién eliminado
        """
        move_tax = self.env['account.move.taxes'].search(
            ['&', '&', ('id', '=', self.move_tax_id.id), ('move_id', '=', self.move_id.id),
             ('tax_type_id', '=', self.tax_type_id.id), ('percent', '=', self.percent)])

        if move_tax:
            move_tax.update({
                'amount': move_tax.amount - self.amount,
                'base': move_tax.base - self.base,
            })

        return super(AccountMoveTaxesLine, self).unlink()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange('tax_ids')
    def validate_tax_type(self):
        """
        Valida que el impuesto seleccionado en el movimineto tenga el Tipo de Impuesto seleccionado
        """
        for tax in self.tax_ids:
            if not tax.tax_type:
                raise exceptions.ValidationError("Impuesto no tiene un Tipo de Impuesto válido.")

    def _get_computed_taxes(self):
        """
        Valida que el Tercero (Cliente/Proveedor) tenga correctamente asignada la Posición Fiscal, si no es Movimiento Contable
        """
        if self.move_id.type != 'entry':
            if not (self.move_id.fiscal_position_id):
                raise exceptions.ValidationError("Tercero no tiene una posición fiscal válida.")

        return super(AccountMoveLine, self)._get_computed_taxes()

    def store_amount_taxes_line(self, only_delete=False):
        """
        Determina por cada impuesto aplicado en la linea, el corresponidente Valor a sumar o restar y su respectiva Base.
        Con estos datos, se almacena en el modelo account.move.taxes.line, que a su vez lo resume por Documento,
        Tipo de Impuesto y Porcentaje en el modelo account.move.taxes.line con los métodos create y unlink.

        :param only_delete: Determina si solamente debe borrar, evita crear en caso de modificación
        """

        for line in self:
            price_unit_wo_discount = line.price_unit * (1 - (line.discount / 100.0))

            # Con cada iteración elimina todos los registros del detalle y los crea de nuevo.
            move_taxes_line = self.env['account.move.taxes.line'].search(
                ['&', ('move_id', '=', line.move_id.id), ('move_line_id', '=', line.id)])
            for move_tax_line in move_taxes_line:
                move_tax_line.unlink()

            if not (only_delete):
                if line.tax_ids:
                    taxes_res = line.tax_ids._origin.compute_all(price_unit_wo_discount,
                                                                 quantity=line.quantity, currency=line.currency_id,
                                                                 product=line.product_id, partner=line.partner_id,
                                                                 is_refund=line.move_id.type in (
                                                                     'out_refund', 'in_refund'))

                    for applied_tax in taxes_res['taxes']:
                        if applied_tax['amount'] != 0:
                            # print(applied_tax)
                            tax = self.env['account.tax'].browse(applied_tax['id'])
                            # print(tax)
                            if tax:
                                move_tax = self.env['account.move.taxes'].search(
                                    ['&', ('move_id', '=', line.move_id.id), ('tax_type_id', '=', tax.tax_type.id),
                                     ('percent', '=', tax.amount)])

                                if not (move_tax):
                                    move_tax = self.env['account.move.taxes'].create({
                                        'move_id': line.move_id.id,
                                        'tax_type_id': tax.tax_type.id,
                                        'percent': tax.amount,
                                        'amount': 0,
                                        'base': 0,
                                    })

                                self.env['account.move.taxes.line'].create({
                                    'move_tax_id': move_tax.id,
                                    'move_id': line.move_id.id,
                                    'move_line_id': line.id,
                                    'tax_type_id': tax.tax_type.id,
                                    'percent': tax.amount,
                                    'amount': applied_tax['amount'],
                                    'base': applied_tax['base'],
                                })

    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobreescritura del método que permite calcular y almacenar los cálculos correspondientes a impuestos para
        presentar en Factura Electrónica.
        :return: Objeto de línea recién creado
        """
        account_move_line = super(AccountMoveLine, self).create(vals_list)

        if account_move_line:
            account_move_line.store_amount_taxes_line()

        return account_move_line

    def write(self, vals):
        """
        Sobreescritura del método que permite calcular, actualizar y almacenar los cálculos correspondientes a
        impuestos para presentar en Factura Electrónica.
        :return: Objeto de línea recién modificado
        """
        account_move_line = super(AccountMoveLine, self).write(vals)

        self.store_amount_taxes_line()

        return account_move_line

    def unlink(self):
        """
        Sobreescritura del método que permite actualizar y eliminar los cálculos correspondientes a
        impuestos para presentar en Factura Electrónica.
        :return: Objeto de línea recién eliminado
        """
        self.store_amount_taxes_line(only_delete=True)

        return super(AccountMoveLine, self).unlink()

