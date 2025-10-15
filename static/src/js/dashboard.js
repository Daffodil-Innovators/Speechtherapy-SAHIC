odoo.define('dsl_physio_dashboard.Dashboard', function (require) {
    'use strict';

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');
    const rpc = require('web.rpc');
    const QWeb = core.qweb;
    var _t = core._t;

    const Dashboard = AbstractAction.extend({
        template: 'dsl_physio_dashboard.Dashboard',

        events: {
            // filters
            'submit .js-search-form': '_onSearchSubmit',
            'click .js-search-btn': '_onSearchSubmit',

            // my statistics navigation
            'click .js-my-today': '_openMyToday',
            'click .js-my-total': '_openMyTotal',
            'click .js-my-collection': '_openMyCollection',

            // global statistics navigation
            'click .js-global-today': '_openGlobalToday',
            'click .js-global-total': '_openGlobalTotal',
            'click .js-global-collection': '_openGlobalCollection',
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);

            // Date defaults (current year range)
            var today = new Date();
            var firstDay = new Date(today.getFullYear(), 0, 1);
            var lastDay = new Date(today.getFullYear(), 11, 31);

            function formatDate(d) {
                let month = (d.getMonth() + 1).toString().padStart(2, '0');
                let day = d.getDate().toString().padStart(2, '0');
                return `${d.getFullYear()}-${month}-${day}`;
            }

            this.search = {
                date_from: formatDate(firstDay),
                date_to: formatDate(lastDay),
            };

            this.metrics = {
                my_today: 0, my_total: 0, my_collected: 0,
                global_today: 0, global_total: 0, global_collected: 0,
                is_physio: false,
                current_physio_id: false,
            };
            this.results = {
                rows: [],
                totals: {total_sessions: 0, total_patients: 0, total_amount: 0, total_collected: 0}
            };
        },

        willStart: function () {
            var def = this._super.apply(this, arguments);
            var self = this;

            var lMetrics = rpc.query({
                route: '/dsl_physio/dashboard/metrics'
            }).then(function (res) {
                if (res) self.metrics = res;
            });

            return Promise.all([def, lMetrics]);
        },

        start: function () {
            this._render();
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._render();
                return self._onSearchSubmit(); // run default search
            });
        },

        _render: function () {
            this.$el.html(QWeb.render(this.template, {
                metrics: this.metrics,
                search: this.search,
                results: this.results,
            }));
        },

        // -------- filters ----------
        _onSearchSubmit: function (ev) {
            if (ev) ev.preventDefault();
            this.search = {
                date_from: this.$('.js-date-from').val() || '',
                date_to: this.$('.js-date-to').val() || '',
            };

            var self = this;
            var payload = {
                date_from: self.search.date_from || false,
                date_to: self.search.date_to || false,
            };
            return rpc.query({route: '/dsl_physio/physiotherapist/summary', params: payload})
                .then(function (res) {
                    self.results = res || self.results;
                })
                .then(this._render.bind(this));
        },

        // -------- navigation (open dsl.physiotherapy) ----------
        _openMyToday: function () {
            var today = new Date().toISOString().split('T')[0];
            var domain = [
                ['physiotherapist_id', '=', this.metrics.current_physio_id],
                ['date', '>=', today + ' 00:00:00'],
                ['date', '<=', today + ' 23:59:59']
            ];
            this.do_action({
                type: 'ir.actions.act_window',
                name: _t("My Speechtherapy Today"),
                res_model: 'dsl.physiotherapy',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
                target: 'current',
            });
        },

        _openMyTotal: function () {
            var domain = [['physiotherapist_id', '=', this.metrics.current_physio_id]];
            this.do_action({
                type: 'ir.actions.act_window',
                name: _t("My Total Speechtherapy"),
                res_model: 'dsl.physiotherapy',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
                target: 'current',
            });
        },

        _openMyCollection: function () {
            var self = this;
            rpc.query({
                route: '/dsl_physio/invoice_ids',
                params: {kind: 'my_posted', physio_id: self.metrics.current_physio_id},
            }).then(function (res) {
                self.do_action({
                    type: 'ir.actions.act_window',
                    name: _t("My Collections"),
                    res_model: 'account.move',
                    views: [[false, 'list'], [false, 'form']],
                    domain: [['id', 'in', (res && res.ids) || []]],
                    target: 'current',
                });
            });
        },

        _openGlobalToday: function () {
            var today = new Date().toISOString().split('T')[0];
            this.do_action({
                type: 'ir.actions.act_window',
                name: _t("Global Speechtherapy Today"),
                res_model: 'dsl.physiotherapy',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['date', '>=', today + ' 00:00:00'],
                    ['date', '<=', today + ' 23:59:59']
                ],
                target: 'current',
            });
        },

        _openGlobalTotal: function () {
            this.do_action({
                type: 'ir.actions.act_window',
                name: _t("All Speechtherapy Sessions"),
                res_model: 'dsl.physiotherapy',
                views: [[false, 'list'], [false, 'form']],
                domain: [],
                target: 'current',
            });
        },

        _openGlobalCollection: function () {
            var self = this;
            rpc.query({
                route: '/dsl_physio/invoice_ids',
                params: {kind: 'all_posted', physio_id: null},
            }).then(function (res) {
                self.do_action({
                    type: 'ir.actions.act_window',
                    name: _t("All Collections"),
                    res_model: 'account.move',
                    views: [[false, 'list'], [false, 'form']],
                    domain: [['id', 'in', (res && res.ids) || []]],
                    target: 'current',
                });
            });
        },
    });

    core.action_registry.add('dsl_physio_dashboard', Dashboard);
    return Dashboard;
});
