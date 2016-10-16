/*!
 * execute.js
 *     The client-side javascript code for the Execute plugin.
 *
 * Copyright (C) Damien Churchill 2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 *
 */

Ext.ns('Deluge.ux');

Deluge.ux.ExecuteWindowBase = Ext.extend(Ext.Window, {

    layout: 'fit',
    width: 400,
    height: 130,
    closeAction: 'hide',

    initComponent: function() {
        Deluge.ux.ExecuteWindowBase.superclass.initComponent.call(this);
        this.addButton(_('Cancel'), this.onCancelClick, this);

        this.form = this.add({
            xtype: 'form',
            baseCls: 'x-plain',
            bodyStyle: 'padding: 5px',
            items: [{
                    xtype: 'combo',
                    width: 135,
                    fieldLabel: _('Event'),
                    store: new Ext.data.ArrayStore({
                        fields: ['id', 'text'],
                        data: [
                                ['complete', _('Torrent Complete')],
                                ['added', _('Torrent Added')],
                                ['removed', _('Torrent Removed')],
                                ['copied', _('Torrent Copied')]
                            ]
                    }),
                    name: 'event',
                    mode: 'local',
                    editable: false,
                    triggerAction: 'all',
                    valueField:    'id',
                    displayField:  'text'
                }, {
                    xtype: 'textfield',
                    fieldLabel: _('Command'),
                    name: 'command',
                    width: 135
                }, {
                    xtype: 'combo',
                    width: 135,
                    fieldLabel: _('Type'),
                    store: new Ext.data.ArrayStore({
                        fields: ['id', 'text'],
                        data: [
                                ['script', _('Script')],
                                ['url', _('URL')]
                            ]
                    }),
                    name: 'type',
                    mode: 'local',
                    editable: false,
                    triggerAction: 'all',
                    valueField:    'id',
                    displayField:  'text'
                }, {
                    xtype: 'textfield',
                    fieldLabel: _('TorrentLabel'),
                    name: 'torrentlabel',
                    width: 85
                }, {
                    xtype: 'textfield',
                    fieldLabel: _('Delay'),
                    name: 'delay',
                    width: 50
                }]
        });
    },

    onCancelClick: function() {
        this.hide();
    }
});

Deluge.ux.EditExecuteCommandWindow = Ext.extend(Deluge.ux.ExecuteWindowBase, {

    title: _('Edit Command'),

    initComponent: function() {
        Deluge.ux.EditExecuteCommandWindow.superclass.initComponent.call(this);
        this.addButton(_('Save'), this.onSaveClick, this);
        this.addEvents({
            'commandedit': true
        });
    },

    show: function(command) {
        Deluge.ux.EditExecuteCommandWindow.superclass.show.call(this);
        this.command = command;
        this.form.getForm().setValues({
            event: command.get('event'),
            command: command.get('name'),
            type: command.get('type'),
            torrentlabel: command.get('torrentlabel'),
            delay: command.get('delay')
        });
    },

    onSaveClick: function() {
        var values = this.form.getForm().getFieldValues();
        deluge.client.execute.save_command(this.command.id, values.event, values.command, {
            success: function() {
                this.fireEvent('commandedit', this, values.event, values.command);
            },
            scope: this
        });
        this.hide();
    }

});

Deluge.ux.AddExecuteCommandWindow = Ext.extend(Deluge.ux.ExecuteWindowBase, {

    title: _('Add Command'),

    initComponent: function() {
        Deluge.ux.AddExecuteCommandWindow.superclass.initComponent.call(this);
        this.addButton(_('Add'), this.onAddClick, this);
        this.addEvents({
            'commandadd': true
        });
    },

    onAddClick: function() {
        var values = this.form.getForm().getFieldValues();
        deluge.client.execute.add_command(values.event, values.command, {
            success: function() {
                this.fireEvent('commandadd', this, values.event, values.command);
            },
            scope: this
        });
        this.hide();
    }

});

Ext.ns('Deluge.ux.preferences');

/**
 * @class Deluge.ux.preferences.ExecutePage
 * @extends Ext.Panel
 */
Deluge.ux.preferences.ExecutePage = Ext.extend(Ext.Panel, {

    title: _('Execute'),
    header: false,
    layout: 'fit',
    border: false,

    initComponent: function() {
        Deluge.ux.preferences.ExecutePage.superclass.initComponent.call(this);
        var event_map = this.event_map = {
                'complete': _('Torrent Complete'),
                'added': _('Torrent Added'),
                'removed': _('Torrent Removed'),
                'copied': _('Torrent Copied')
            };

        var type_map = this.type_map = {
                'script': _('Script'),
                'url': _('URL')
            };

        this.list = new Ext.list.ListView({
            store: new Ext.data.SimpleStore({
                fields: [
                    {name: 'event', mapping: 1},
                    {name: 'name', mapping: 2}
                    ],
                id: 0
            }),
            columns: [{
                    width: .3,
                    header: _('Event'),
                    sortable: true,
                    dataIndex: 'event',
                    tpl: new Ext.XTemplate('{[this.getEvent(values.event)]}', {
                        getEvent: function(e) {
                            return (event_map[e]) ? event_map[e] : e;
                        }
                    })
                }, {
                    id: 'name',
                    header: _('Command'),
                    sortable: true,
                    dataIndex: 'name'
                },{
                    width: .3,
                    header: _('Type'),
                    sortable: true,
                    dataIndex: 'type',
                    tpl: new Ext.XTemplate('{[this.getType(values.type)]}', {
                        getType: function(e) {
                            return (type_map[e]) ? type_map[e] : e;
                        }
                    })
                }, {
                    id: 'torrentlabel',
                    header: _('TorrentLabel'),
                    sortable: true,
                    dataIndex: 'torrentlabel'
                }, {
                    id: 'delay',
                    header: _('Delay'),
                    sortable: true,
                    dataIndex: 'delay'
                }],
            singleSelect: true,
            autoExpandColumn: 'name'
        });
        this.list.on('selectionchange', this.onSelectionChange, this);

        this.panel = this.add({
            items: [this.list],
            bbar: {
                items: [{
                        text: _('Add'),
                        iconCls: 'icon-add',
                        handler: this.onAddClick,
                        scope: this
                    }, {
                        text: _('Edit'),
                        iconCls: 'icon-edit',
                        handler: this.onEditClick,
                        scope: this,
                        disabled: true
                    }, '->', {
                        text: _('Remove'),
                        iconCls: 'icon-remove',
                        handler: this.onRemoveClick,
                        scope: this,
                        disabled: true
                    }]
            }
        });

        this.on('show', this.onPreferencesShow, this);
    },

    updateCommands: function() {
        deluge.client.execute.get_commands({
            success: function(commands) {
                this.list.getStore().loadData(commands);
            },
            scope: this
        });
    },

    onAddClick: function() {
        if (!this.addWin) {
            this.addWin = new Deluge.ux.AddExecuteCommandWindow();
            this.addWin.on('commandadd', function() {
                this.updateCommands();
            }, this);
        }
        this.addWin.show();
    },

    onCommandAdded: function(win, evt, cmd, typ, lbl, dly) {
        var record = new this.list.getStore().recordType({
            event: evt,
            command: cmd,
            type: typ,
            torrentlabel: lbl,
			delay: dly
        });
    },

    onEditClick: function() {
        if (!this.editWin) {
            this.editWin = new Deluge.ux.EditExecuteCommandWindow();
            this.editWin.on('commandedit', function() {
                this.updateCommands();
            }, this);
        }
        this.editWin.show(this.list.getSelectedRecords()[0]);
    },

    onPreferencesShow: function() {
        this.updateCommands();
    },

    onRemoveClick: function() {
        var record = this.list.getSelectedRecords()[0];
        deluge.client.execute.remove_command(record.id, {
            success: function() {
                this.updateCommands();
            },
            scope: this
        });
    },

    onSelectionChange: function(dv, selections) {
        if (selections.length) {
            this.panel.getBottomToolbar().items.get(1).enable();
            this.panel.getBottomToolbar().items.get(3).enable();
        } else {
            this.panel.getBottomToolbar().items.get(1).disable();
            this.panel.getBottomToolbar().items.get(3).disable();
        }
    }
});

Deluge.plugins.ExecutePlugin = Ext.extend(Deluge.Plugin, {

    name: 'Execute',

    onDisable: function() {
        deluge.preferences.removePage(this.prefsPage);
    },

    onEnable: function() {
        this.prefsPage = deluge.preferences.addPage(new Deluge.ux.preferences.ExecutePage());
    }
});
Deluge.registerPlugin('Execute', Deluge.plugins.ExecutePlugin);
