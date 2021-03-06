from django.db import models, connection, transaction
from NA_DataLayer.common import (CriteriaSearch, DataType, ResolveCriteria, query,
                                 StatusForm, Data)


class NA_BR_Goods_Return(models.Manager):
    def PopulateQuery(self, columnKey, ValueKey, criteria=CriteriaSearch.Like, typeofData=DataType.VarChar):
        cur = connection.cursor()
        rs = ResolveCriteria(criteria, typeofData, columnKey, ValueKey)
        Query = """SELECT ngr.idapp,ngr.datereturn,ngr.conditions,ngr.iscompleted,ngr.minusDesc,ngr.typeapp,ngr.serialnumber,
        ngr.descriptions, ngr.createddate, ngr.createdby, CONCAT(g.goodsname, ' ',g.brandname,' ',g.typeapp) AS goods,emp1.fromemployee,
        emp2.usedemployee FROM n_a_goods_return ngr INNER JOIN n_a_goods g ON ngr.fk_goods = g.idapp LEFT OUTER JOIN 
        (SELECT idapp, employee_name AS fromemployee FROM employee) AS emp1 ON ngr.fk_fromemployee = emp1.idapp
        LEFT OUTER JOIN (SELECT idapp,employee_name AS usedemployee FROM employee) AS emp2 ON ngr.fk_usedemployee = emp2.idapp
        WHERE """ + columnKey + rs.Sql()
        cur.execute(Query)
        result = query.dictfetchall(cur)
        cur.close()
        return result

    def SaveData(self, statusForm=StatusForm.Input, **data):
        cur = connection.cursor()
        Params = {
            'FK_Goods': data['fk_goods'], 'TypeApp': data['typeApp'], 'SerialNumber': data['serialNumber'],
            'DateReturn': data['datereturn'], 'Conditions': data['conditions'],
            'FK_fromemployee': data['idapp_fromemployee'], 'FK_usedemployee': data['idapp_usedemployee'],
            'IsCompleted': data['iscompleted'], 'MinusDesc': data['minus'],
            'Descriptions': data['descriptions']
        }
        if statusForm == StatusForm.Input:
            Params['CreatedDate'] = data['createddate']
            Params['CreatedBy'] = data['createdby']
            fromgoods = None
            value_fromgoods = None
            if data['fk_goods_outwards'] != 'NULL' and data['fk_goods_outwards'] != '':
                fromgoods = 'FK_goods_outwards'
                value_fromgoods = data['fk_goods_outwards']
            elif data['fk_goods_lend'] != 'NULL' and data['fk_goods_lend'] != '':
                fromgoods = 'FK_goods_lend'
                value_fromgoods = data['fk_goods_lend']
            Params[fromgoods] = value_fromgoods

            with transaction.atomic():
                Query = """INSERT INTO n_a_goods_return 
                (fk_goods,typeapp,serialnumber,datereturn,conditions,fk_fromemployee,fk_usedemployee,iscompleted,minusDesc,
                descriptions,createddate,createdby,""" + fromgoods + ")"
                Query += """VALUES({})""".format(','.join('%(' +
                                                          i+')s' for i in Params))
                cur.execute(Query, Params)
                Query = """INSERT INTO n_a_goods_history (FK_Goods, TypeApp, SerialNumber,FK_RETURN, CreatedDate, CreatedBy)
                VALUES (%(FK_Goods)s,%(TypeApp)s, %(SerialNumber)s, %(FK_Return)s, %(CreatedDate)s, %(CreatedBy)s)"""
                cur.execute("""SELECT last_insert_id()""")
                idapp = cur.fetchone()[0]
                Params = {
                    'FK_Goods': data['fk_goods'], 'TypeApp': data['typeApp'], 'SerialNumber': data['serialNumber'],
                    'FK_Return': idapp, 'CreatedDate': data['createddate'], 'CreatedBy': data['createdby']
                }
                cur.execute(Query, Params)
        elif statusForm == StatusForm.Edit:
            Params['ModifiedDate'] = data['modifieddate']
            Params['ModifiedBy'] = data['modifiedby']
            Params['IDApp'] = data['idapp']
            Query = """UPDATE n_a_goods_return SET fk_goods=%(FK_Goods)s, typeapp=%(TypeApp)s, serialnumber=%(SerialNumber)s,
            datereturn=%(DateReturn)s, conditions=%(Conditions)s, fk_fromemployee=%(FK_fromemployee)s, fk_usedemployee=%(FK_usedemployee)s,
            iscompleted=%(IsCompleted)s, minusDesc=%(MinusDesc)s, descriptions=%(Descriptions)s, modifieddate=%(ModifiedDate)s,
            modifiedby=%(ModifiedBy)s WHERE idapp=%(IDApp)s"""
            cur.execute(Query, Params)
            cur.close()
        return (Data.Success,)

    def DeleteData(self, idapp):
        cur = connection.cursor()
        Query = """DELETE FROM n_a_goods_return WHERE idapp=%(IDApp)s"""
        cur.execute(Query, {'IDApp': idapp})
        return 'success'

    def retrieveData(self, idapp):
        cur = connection.cursor()
        Query = """SELECT ngr.typeApp,ngr.serialNumber,ngr.fk_goods,ngr.datereturn,ngr.conditions,
        ngr.minusDesc AS minus, ngr.iscompleted,ngr.fk_goods_outwards AS idapp_fk_goods_outwards,
        ngr.fk_goods_lend AS idapp_fk_goods_outwards, ngr.descriptions,
        CONCAT(g.goodsname, ' ',g.brandname, ' ',ngr.typeapp) AS goods,g.itemcode,emp1.fromemployee,
        emp1.nik_fromemployee,emp1.idapp_fromemployee,emp2.usedemployee,emp2.nik_usedemployee,
        emp2.idapp_usedemployee FROM n_a_goods_return ngr INNER JOIN n_a_goods g ON ngr.fk_goods = g.idapp 
        LEFT OUTER JOIN 
        (SELECT idapp AS idapp_fromemployee,nik AS nik_fromemployee,employee_name AS fromemployee FROM employee)
        AS emp1 ON ngr.fk_fromemployee = emp1.idapp_fromemployee 
        LEFT OUTER JOIN 
        (SELECT idapp AS idapp_usedemployee, nik AS nik_usedemployee,employee_name AS usedemployee FROM employee) 
        AS emp2 ON ngr.fk_usedemployee = emp2.idapp_usedemployee WHERE ngr.idapp = %(IDApp)s"""
        cur.execute(Query, {'IDApp': idapp})
        result = query.dictfetchall(cur)
        cur.close()
        return result[0]

    def SearchGoods_byForm(self, q):
        cur = connection.cursor()
        Query = """
        (SELECT ngo.idapp,CONCAT(g.goodsname,' ',g.brandname,' ',ngo.typeapp) AS goods,
        ngo.fk_goods, ngo.serialnumber, g.itemcode, ngo.typeapp, @fromgoods := 'GO' AS fromgoods
        FROM n_a_goods_outwards ngo INNER JOIN n_a_goods g ON ngo.fk_goods = g.idapp
        WHERE CONCAT(g.goodsname,' ',g.brandname,' ',ngo.typeapp)
        LIKE \'{q}\' OR g.itemcode LIKE \'{q}\' or ngo.serialnumber LIKE \'{q}\'
        AND NOT EXISTS (SELECT idapp FROM n_a_goods_return WHERE fk_goods_outwards = ngo.idapp))
        UNION
        (SELECT ngl.idapp,CONCAT(g.goodsname,' ',g.brandname,' ',ngl.typeapp) AS goods,
        ngl.fk_goods, ngl.serialnumber, g.itemcode, ngl.typeapp, @fromgoods := 'GL' AS
        fromgoods FROM n_a_goods_lending ngl INNER JOIN n_a_goods g ON ngl.fk_goods = g.idapp
        WHERE CONCAT(g.goodsname,' ',g.brandname,' ',ngl.typeapp)
        LIKE \'{q}\' OR g.itemcode LIKE \'{q}\' or ngl.serialnumber LIKE \'{q}\'
        AND NOT EXISTS (SELECT idapp FROM n_a_goods_return WHERE fk_goods_lend = ngl.idapp))
        """.format(
            q=('%' + q + '%')
        )
        cur.execute(Query)
        result = query.dictfetchall(cur)
        cur.close()
        return result

    def getGoods_data(self, idapp, fromgoods):
        cur = connection.cursor()
        if fromgoods == 'GO':
            Query = """SELECT ngo.idapp,CONCAT(g.goodsname,' ',g.brandname,' ',ngo.typeapp) AS goods, ngo.serialnumber,g.itemcode,
            @fromgoods := 'GO' AS fromgoods,emp1.idapp_used_by,emp1.used_by,emp1.nik_used_by FROM n_a_goods_outwards ngo 
            INNER JOIN n_a_goods g ON ngo.fk_goods = g.idapp LEFT OUTER JOIN (SELECT idapp AS idapp_used_by,nik AS nik_used_by,
            employee_name AS used_by FROM employee) AS emp1 ON ngo.fk_employee = emp1.idapp_used_by WHERE
            ngo.idapp = %(IDApp)s"""
        elif fromgoods == 'GL':
            Query = """SELECT ngl.idapp,CONCAT(g.goodsname,' ',g.brandname,' ',ngl.typeapp) AS goods, ngl.serialnumber,g.itemcode,
            @fromgoods := 'GL' AS fromgoods,emp1.idapp_used_by,emp1.used_by,emp1.nik_used_by FROM n_a_goods_lending ngl 
            INNER JOIN n_a_goods g ON ngl.fk_goods = g.idapp LEFT OUTER JOIN (SELECT idapp AS idapp_used_by,nik AS nik_used_by,
            employee_name AS used_by FROM employee) AS emp1 ON ngl.fk_employee = emp1.idapp_used_by WHERE 
            ngl.idapp = %(IDApp)s"""
        cur.execute(Query, {'IDApp': idapp})
        result = query.dictfetchall(cur)
        cur.close()
        return (Data.Success, result)

    def dataExists(self, **kwargs):
        idapp = kwargs.get('idapp')
        if idapp is not None:
            return super(NA_BR_Goods_Return, self).get_queryset().filter(idapp=idapp).exists()
        serialnumber = kwargs.get('serialnumber')
