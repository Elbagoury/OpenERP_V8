
// this file contains the screens definitions. Screens are the
// content of the right pane of the pos, containing the main functionalities. 
// screens are contained in the PosWidget, in pos_widget.js
// all screens are present in the dom at all time, but only one is shown at the
// same time. 
//
// transition between screens is made possible by the use of the screen_selector,
// which is responsible of hiding and showing the screens, as well as maintaining
// the state of the screens between different orders.
//
// all screens inherit from ScreenWidget. the only addition from the base widgets
// are show() and hide() which shows and hides the screen but are also used to 
// bind and unbind actions on widgets and devices. The screen_selector guarantees
// that only one screen is shown at the same time and that show() is called after all
// hide()s

function saicoms_pos_screens(instance, module){ //module is instance.point_of_sale
    console.log('In new screen.js');
    var QWeb = instance.web.qweb,
    _t = instance.web._t;

    var round_pr = instance.web.round_precision
    module.ClientListScreenWidget.include({
        template: 'ClientListScreenWidget',
        init: function(parent, options){
            this._super(parent, options);
        },
        save_client_details: function(partner) {
            var self = this;

            var fields = {}
            this.$('.client-details-contents .detail').each(function(idx,el){
                fields[el.name] = el.value;
            });

            if (!fields.name) {
                this.pos_widget.screen_selector.show_popup('error',{
                    message: _t('A Customer Name Is Required'),
                });
                return;
            }

            if (this.uploaded_picture) {
                fields.image = this.uploaded_picture;
            }

            fields.id           = partner.id || false;
            fields.country_id   = fields.country_id || false;
            fields.vi_district_id   = fields.vi_district_id || false;
            fields.vi_city_id   = fields.vi_city_id || false;
            fields.customer_type_id   = fields.customer_type_id || false;
            fields.saicoms_dob   = fields.saicoms_dob || false;
            fields.occupation_id   = fields.occupation_id || false;
            fields.customer_source_id   = fields.customer_source_id || false;
            fields.ean13        = fields.ean13 ? this.pos.barcode_reader.sanitize_ean(fields.ean13) : false;

            new instance.web.Model('res.partner').call('create_from_ui',[fields]).then(function(partner_id){
                self.saved_client_details(partner_id);
            },function(err,event){
                event.preventDefault();
                self.pos_widget.screen_selector.show_popup('error',{
                    'message':_t('Error: Could not Save Changes'),
                    'comment':_t('Your Internet connection is probably down.'),
                });
            });
        },
    });


}
