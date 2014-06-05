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

import csv
import os

from openerp.osv import osv, fields


class insee_installer(osv.TransientModel):
    _name = 'insee.installer'
    _inherit = 'res.config'

    def _import_insee_region(self, cr, uid, ids, data_dir, context=None):
        """Import regions from the reg2011.csv file."""
        if context is None:
            context = {}
        filepath = os.path.abspath(os.path.join(data_dir, 'reg2011.csv'))
        region_obj = self.pool.get('insee.region')
        with open(filepath, 'rb') as regfile:
            reader = csv.DictReader(regfile)
            for row in reader:
                values = {
                    'region': row['REGION'],
                    'cheflieu': row['CHEFLIEU'],
                    'tncc': row['TNCC'],
                    'ncc': row['NCC'],
                    'nccenr': row['NCCENR'],
                }
                region_obj.create(cr, uid, values, context=context)

    def _import_insee_department(self, cr, uid, ids, data_dir, context=None):
        """Import departments from the depts2011.csv file.
        Link the department to its region (m2o field: region_id)
        """
        if context is None:
            context = {}
        filepath = os.path.abspath(os.path.join(data_dir, 'depts2011.csv'))
        department_obj = self.pool.get('insee.department')
        region_obj = self.pool.get('insee.region')
        with open(filepath, 'rb') as departmentsfile:
            reader = csv.DictReader(departmentsfile)
            for row in reader:
                args = [('region', '=', row['REGION'])]
                region_id = region_obj.search(cr, uid, args, context=context)[0]
                values = {
                    'region_id': region_id,
                    'region': row['REGION'],
                    'dep': row['DEP'],
                    'cheflieu': row['CHEFLIEU'],
                    'tncc': row['TNCC'],
                    'ncc': row['NCC'],
                    'nccenr': row['NCCENR'],
                }
                department_obj.create(cr, uid, values, context=context)

    def _import_insee_zipcode(self, cr, uid, ids, data_dir, context=None):
        """Import ZIP codes from the insee_codes_postaux.csv file.
        The delimiter is a semi-colon not a coma.
        """
        if context is None:
            context = {}
        filepath = os.path.abspath(os.path.join(
            data_dir, 'insee_codes_postaux.csv'))
        zipcode_obj = self.pool.get('insee.zipcode')
        with open(filepath, 'rb') as zipcode_file:
            reader = csv.DictReader(zipcode_file, delimiter=';')
            for row in reader:
                values = {
                    'commune': row['COMMUNE'],
                    'codepos': row['CODEPOS'],
                    'dep': row['DEP'],
                    'insee': row['INSEE'],
                }
                zipcode_obj.create(cr, uid, values, context=context)

    def _import_insee_city(self, cr, uid, ids, data_dir, context=None):
        """Import cities from the comsimp2011.csv file, and link them to their
        associated departments.
        """
        if context is None:
            context = {}
        filepath = os.path.abspath(os.path.join(data_dir, 'comsimp2011.csv'))
        city_obj = self.pool.get('insee.city')
        department_obj = self.pool.get('insee.department')
        with open(filepath, 'rb') as cityfile:
            reader = csv.DictReader(cityfile)
            for row in reader:
                args = [('dep', '=', row['DEP'])]
                department_ids = department_obj.search(cr, uid, args)
                department_id = department_ids and department_ids[0] or None
                ncc = row['ARTMAJ'] and row['ARTMAJ'].strip("()") + \
                      row['NCC'] or row['NCC']
                nccenr = row['ARTMIN'] and row['ARTMIN'].strip("()") + \
                         row['NCCENR'] or row['NCCENR']
                values = {
                    'cdc': row['CDC'],
                    'cheflieu': row['CHEFLIEU'],
                    'reg': row['REG'],
                    'dep': row['DEP'],
                    'department_id': department_id,
                    'com': row['COM'],
                    'ar': row['AR'],
                    'ct': row['CT'],
                    'tncc': row['TNCC'],
                    'artmaj': row['ARTMAJ'],
                    'ncc': ncc,
                    'artmin': row['ARTMIN'],
                    'nccenr': nccenr,
                }
                city_obj.create(cr, uid, values, context=context)

    # Method called by the "apply" button from res.config object
    def execute(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        # get data directory path (containing csv files)
        dirname = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.abspath(os.path.join(dirname, "data"))
        # import data
        self._import_insee_region(cr, uid, ids, data_dir, context=context)
        self._import_insee_department(cr, uid, ids, data_dir, context=context)
        self._import_insee_zipcode(cr, uid, ids, data_dir, context=context)
        self._import_insee_city(cr, uid, ids, data_dir, context=context)


class insee_region(osv.Model):
    _name = 'insee.region'
    _description = 'INSEE regions'

    _columns = {
        'region': fields.char('Region', size=64, required=True),
        'department_ids': fields.one2many(
            'insee.department', 'region_id', 'Departments'),
        'cheflieu': fields.char('Administrative Center', size=64),
        'tncc': fields.char('tncc', size=64),
        'ncc': fields.char('ncc', size=64, required=True),
        'nccenr': fields.char('nccenr', size=64),
    }
    _rec_name = 'ncc'
    _order = 'ncc'


class insee_department(osv.Model):
    _name = 'insee.department'
    _description = "INSEE departments"

    _columns = {
        'region_id': fields.many2one('insee.region', 'Region', required=True),
        'region': fields.char('Region', size=64, required=True),
        'dep': fields.char('Department', size=64, required=True),
        'cheflieu': fields.char('Administrative Center', size=64),
        'tncc': fields.char('tncc', size=64),
        'ncc': fields.char('ncc', size=64, required=True),
        'nccenr': fields.char('nccenr', size=64),
        'region_insee': fields.related(
            'region_id', 'ncc', type='char', string='INSEE Region', size=64),
    }

    _rec_name = 'dep'

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = [(r['id'], r['dep'] + ' ' + r['ncc'])
                for r in self.read(cr, uid, ids, ['dep', 'ncc'], context)]
        return res


class insee_zipcode(osv.Model):
    _name = 'insee.zipcode'
    _description = "INSEE ZIP code"

    _columns = {
        'commune': fields.char('City', size=128, required=True),
        'codepos': fields.char('ZIP', size=128, required=True),
        'dep': fields.char('Department', size=128,),
        'insee': fields.char('INSEE Code', size=128, required=True),
    }

    _order = 'codepos'
    _rec_name = 'codepos'


class insee_city(osv.Model):
    _name = 'insee.city'
    _description = "INSEE city"

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = [(r['id'], r['ncc'] + " (" + r['dep'] + ")")
               for r in self.read(cr, uid, ids, ['dep', 'ncc'], context)]
        return res

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
               context=None, count=False):
        if context is None:
            context = {}
        pos = 0
        while pos < len(args):
            if args[pos][0] == 'ncc' and \
               args[pos][1] in ('like', 'ilike') and args[pos][2]:
                args[pos] = ('ncc', '=ilike',
                             str(args[pos][2].replace('%', '')) + '%')
            pos += 1

        return super(insee_city, self).search(
            cr, uid, args, offset, limit, order, context=context, count=count)

    def _city_code(self, cr, uid, ids, field_name, arg, context=None):
        """City code (mainland France) = Dep (1 or 2 digits) + Com (3 digits)
        City code (overseas) = Dep (3 digits) + Com (2 digits)
        """
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = len(line.dep) < 3 and \
                (line.dep + ((3 - len(line.com)) * "0") + line.com) or \
                (line.dep + ((2 - len(line.com)) * "0") + line.com)
        return res

    _columns = {
        'ncc': fields.char('Name', size=128, required=True),
        'cdc': fields.char('CDC', size=64, required=True),
        'cheflieu': fields.char('Administrative Center', size=64, required=True),
        'reg': fields.char('REG', size=64, required=True),
        'dep': fields.char('DEP', size=64, required=True),
        'department_id': fields.many2one(
            'insee.department', string='Department'),
        'com': fields.char('COM', size=64, required=True),
        'ar': fields.char('AR', size=64, required=True),
        'ct': fields.char('CT', size=64, required=True),
        'tncc': fields.char('TNCC', size=64, required=True),
        'artmaj': fields.char('ARTMAJ', size=64),
        'artmin': fields.char('ARTMIN', size=64),
        'nccenr': fields.char('NCCENR', size=64, required=True),
        'department_insee':fields.related(
            'department_id', 'dep', type='char', string='INSEE Department'),
       'region_insee':fields.related(
            'department_id', 'region_id', type='many2one',
            relation='insee.region', string='INSEE Region'),
        'city_code': fields.function(
            _city_code, method=True, string='City Code',
            type='char', size=128, store=True),
    }

    _rec_name = 'ncc'
    _order = 'ncc'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
