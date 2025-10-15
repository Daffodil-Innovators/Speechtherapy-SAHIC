odoo.define('dsl_hms_physiotherapy_extension.SessionTimer', function (require) {
    "use strict";

    const AbstractField = require('web.AbstractField');
    const fieldRegistry = require('web.field_registry');
    const moment = window.moment;

    const SessionTimer = AbstractField.extend({
        supportedFieldTypes: ['float'],

        start: function () {
            this._super.apply(this, arguments);
            console.log("✅ SessionTimer widget loaded");
            this._startInterval();
        },

        _formatTime: function (diffSeconds, isFinal=false) {
            let minutes = Math.floor(diffSeconds / 60);
            let seconds = diffSeconds % 60;
            if (minutes < 60) {
                return (
                    String(minutes).padStart(2, '0') + ":" +
                    String(seconds).padStart(2, '0') + " min" + (isFinal ? " (Final)" : "")
                );
            }
            let hours = Math.floor(minutes / 60);
            minutes = minutes % 60;
            return (
                String(hours).padStart(2, '0') + ":" +
                String(minutes).padStart(2, '0') + ":" +
                String(seconds).padStart(2, '0') + " hr" + (isFinal ? " (Final)" : "")
            );
        },

        _render: function () {
            if (!this.record.data.session_start_time) {
                this.$el.text("00:00 min");
                return;
            }

            if (this.record.data.state === 'in_progress') {
                // 🔄 immediate refresh before ticking
                let start = moment(this.record.data.session_start_time);
                let now = moment();
                let diffSeconds = now.diff(start, 'seconds');
                this.$el.text(this._formatTime(diffSeconds, false));
            }
            else if (this.record.data.state === 'done' && this.record.data.session_end_time) {
                let start = moment(this.record.data.session_start_time);
                let end = moment(this.record.data.session_end_time);
                let diffSeconds = end.diff(start, 'seconds');
                this.$el.text(this._formatTime(diffSeconds, true));
            }
            else {
                this.$el.text("00:00 min");
            }
        },

        _startInterval: function () {
            // ⏱️ refresh immediately once before scheduling
            this._render();
            this.interval = setInterval(this._render.bind(this), 1000);
        },

        destroy: function () {
            if (this.interval) {
                clearInterval(this.interval);
            }
            this._super.apply(this, arguments);
        },
    });

    fieldRegistry.add('session_timer', SessionTimer);
    return SessionTimer;
});
