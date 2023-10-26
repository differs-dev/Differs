odoo.define('ALTANMYA_base_unit_price.website_cookies', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
const {_t, qweb} = require('web.core');
const session = require('web.session');

publicWidget.registry.portalDetails.include({
    start: function () {
        document.addEventListener('cookiebarConsent', (e) => {
            console.log(e.detail.consent);
            console.log('HERE')
        });
        var def = this._super.apply(this, arguments);
        this.$state = this.$('select[name="state_id"]');
        this.$stateOptions = this.$state.filter(':enabled').find('option:not(:first)');
        this._adaptAddressForm();
        return def;
    },
})
})