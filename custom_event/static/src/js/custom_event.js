odoo.define('custom_event.custom_event', function (require) {

    var ajax = require('web.ajax');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var publicWidget = require('web.public.widget');

    var EventCustomForm = Widget.extend({

        /**
         * @override
         */
        start: function () {
            var self = this;
            var res = this._super.apply(this.arguments).then(function () {
                $('#custom_event_form .a-submit-custom')
                    .off('click')
                    .click(function (env) {
                        self.on_clink(env);
                    })
            });
            return res;
        },
        on_clink: function (env) {
            env.preventDefault();
            env.stopPropagation();
            var $form = $(env.currentTarget).closest('form');
            var $button = $(env.currentTarget).closest('[type="submit"]');
            var post = {
                compania: $form.find('input[type="text"][name="compañia"]').val(),
                orden: $form.find('input[type="text"][name="orden"]').val(),
            };
            $button.attr('disabled', true);
            return ajax.jsonRpc($form.attr('action'), 'call', post).then(function (modal){
                var $modal = $(modal);
                $modal.modal({backdrop: 'static', keyboard: false});
                $modal.find('.modal-body > div').removeClass('container');
                $modal.appendTo('body').modal();
                $modal.on('click', '.enable_button_event', function () {
                    $modal.modal('hide');
                    $button.prop('disabled', false);
                });
                $modal.on('click', '.close', function () {
                    $button.prop('disabled', false);
                });
            });
        },
    });

    publicWidget.registry.EventCustomFormInstance = publicWidget.Widget.extend({
        selector: '#custom_event_form',
        /**
        * @override
        */
        start: function () {
            var def = this._super.apply(this, arguments);
            this.instance = new EventCustomForm(this);
            return Promise.all([def, this.instance.attachTo(this.$el)]);
        },
        /**
        * @override
        */
        destroy: function () {
            this.instance.setElement(null);
            this._super.apply(this, arguments);
            this.instance.setElement(this.$el);
        },
    })

    return EventCustomForm;

});
