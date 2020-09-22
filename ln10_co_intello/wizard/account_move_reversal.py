from odoo import fields, models, api


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    note_concept_dian = fields.Many2one('ln10_co_intello.diancodes', string='Concept dian', domain=[('type', '=', 'creditnote')])

    def _prepare_default_reversal(self, move):
        """
        Funcion sobrecargada que permite enviar campos del modelo trasient account.move.reversal
        a account.move mediante el metodo reverse_moves.
        @author Julián Valdés - Intello Idea
        @param move: Parametros por default
        @return: Retorna el super que es un diccionario al cual se le agrego el campo reverse_concept
        """
        move_default = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        move_default['reverse_concept'] = self.note_concept_dian.id

        return move_default

    


