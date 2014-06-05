# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 ABF OSIELL (<http://osiell.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, fields


class res_partner(osv.Model):
    _inherit = 'res.partner'

    _columns = {
        'insee_region_id': fields.many2one('insee.region', "INSEE Region"),
        'insee_department_id': fields.many2one(
            'insee.department', "INSEE Department"),
        'insee_city_id': fields.many2one('insee.city', "INSEE City"),
        'cedex': fields.char('Business ZIP code'),
        'insee_city_ncc': fields.char(),
    }

    def create(self, cr, uid, values=None, context=None):
        if context is None:
            context = {}
        if values and 'insee_city_id' in values:
            city_obj = self.pool.get('insee.city')
            city = values['insee_city_id'] and city_obj.browse(
                cr, uid, values['insee_city_id']).nccenr or ""
            values['city'] = city
        res = super(res_partner, self).create(cr, uid, values, context)
        return res

    def write(self, cr, uid, ids, values=None, context=None):
        if context is None:
            context = {}
        if values and 'insee_city_id' in values and \
           not 'city' in values:
            city_obj = self.pool.get('insee.city')
            city = values['insee_city_id'] and city_obj.browse(
                cr, uid, values['insee_city_id']).nccenr or ""
            values['city'] = city
        res = super(res_partner, self).write(cr, uid, ids, values, context)
        return res

    def onchange_insee_city_id(self, cr, uid, ids, insee_city_id, context=None):
        """Return city ZIP code. Search based on INSEE city code."""
        if context is None:
            context = {}

        value = {}
        if insee_city_id:
            city_obj = self.pool.get('insee.city')
            city_browse_record = city_obj.browse(cr, uid, insee_city_id)
            insee_city_ncc = city_browse_record.ncc
            department_id = city_browse_record.department_id.id
            region_id = city_browse_record.region_insee.id

            res_country_obj = self.pool.get('res.country')
            france_id = res_country_obj.search(
                cr, uid, [('name','=','France')])[0]

            zipcode_obj = self.pool.get('insee.zipcode')
            zipcode_ids = zipcode_obj.search(
                cr, uid, [('insee', '=', city_browse_record.city_code)],)
            zipcode = zipcode_ids and zipcode_obj.browse(
                cr, uid, zipcode_ids[0]).codepos or ""

            value.update({
                'zip': zipcode,
                'insee_city_ncc': insee_city_ncc,
                'city': insee_city_ncc != "ETRANGER" and insee_city_ncc or "",
                'country_id':
                        insee_city_ncc != "ETRANGER" and france_id or None,
                'insee_department_id': department_id,
                'insee_region_id': region_id,
            })

        return {
            'value': value,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
