from django.db import models
from NA_DataLayer.common import *
from django.db import transaction;
from django.db import connection
from decimal import Decimal
from django.db.models import Q
from NA_DataLayer.common import commonFunct
from distutils.util import strtobool
class NA_BR_Goods_Disposal(models.Manager):
	def PopulateQuery(self,orderFields,sortIndice,pageSize,PageIndex,userName,columnKey,ValueKey,criteria=CriteriaSearch.Like,typeofData=DataType.VarChar):
		colkey = ''
		rs = ResolveCriteria(criteria,typeofData,columnKey,ValueKey)
		#datedisposal,afterrepair,lastrepairFrom,issold,sellingprice,proposedby,acknowledgeby,approvedby
		if columnKey == 'goods':
			colKey = 'g.goodsname'
		elif columnKey == 'goodstype':
			colKey = 'ngd.typeApp'
		elif columnKey == 'serialnumber':
			colKey = 'ngd.serialnumber'
		elif columnKey == 'datedisposal':
			colKey = 'ngds.datedisposal'
		elif columnKey == 'afterrepair':
			colKey = 'CONVERT((CASE WHEN(ngds.fk_maintenance IS NULL) THEN 0 ELSE 1 END),INT)'
		elif columnKey == 'lastrepairfrom':
			colKey = '(CASE WHEN (ngds.fk_maintenance IS NOT NULL) THEN(SELECT CONCAT(IFNULL(PersonalName,' '),', ',IFNULL(MaintenanceBy,'')) FROM n_a_maintenance WHERE idapp = ngds.fk_maintenance) ELSE '' END)'
		elif columnKey == 'issold':
			colKey = 'ngds.issold'
		elif columnKey == 'sellingprice':
			colKey = 'ngds.sellingprice'
		elif columnKey == 'proposedby':
			colKey = 'ngds.proposedby'
		elif columnKey == 'createdby':
			colKey = 'ngds.createdby'
		elif columnKey == 'createddate':
			colKey = 'ngds.ceateddate'
		Query = "DROP TEMPORARY TABLE IF EXISTS T_Disposal_Manager_" + userName
		cur = connection.cursor()
		cur.execute(Query)
		#idapp,goods,type,serialnumber,bookvalue,datedisposal,afterrepair,lastrepairFrom,issold,sellingprice,proposedby,acknowledgeby,approvedby,descriptions,createdby,createddate	
		Query = """  CREATE TEMPORARY TABLE T_Disposal_Manager_""" + userName  + """ ENGINE=MyISAM AS (SELECT ngds.idapp,g.goodsname AS goods,ngd.typeApp AS goodstype,ngd.serialnumber,
				ngds.bookvalue,CASE WHEN(ngds.fk_maintenance IS NULL) THEN 0 ELSE 1 END AS afterrepair, 
				CASE WHEN (ngds.fk_maintenance IS NOT NULL) THEN(SELECT CONCAT(IFNULL(PersonalName,' '),', ',IFNULL(MaintenanceBy,'')) FROM n_a_maintenance WHERE idapp = ngds.fk_maintenance) ELSE '' END AS lastrepairfrom,
				ngds.issold,ngds.sellingprice,IFNULL(emp.responsible_by,'') AS proposedby,CONCAT(IFNULL(emp1.employee_name,''), ', ',IFNULL(emp2.employee_name,'')) AS acknowledgeby,IFNULL(emp3.employee_name,'') AS approvedby 
				,ngds.descriptions,ngds.createdby,ngds.createddate		       
		        FROM n_a_disposal ngds INNER JOIN n_a_goods g ON g.IDApp = ngds.FK_Goods 
		        INNER JOIN n_a_goods_receive ngr ON ngr.FK_goods = ngds.FK_Goods
		        INNER JOIN n_a_goods_receive_detail ngd ON ngd.FK_App = ngr.IDApp
		        AND ngds.SerialNumber = ngd.SerialNumber
		        LEFT OUTER JOIN (SELECT idapp,employee_name AS responsible_by FROM employee) emp ON emp.idapp = ngds.FK_ResponsiblePerson
				LEFT OUTER JOIN(SELECT idapp,employee_name FROM employee) emp1 ON emp1.idapp = ngds.FK_Acknowledge1
				LEFT OUTER JOIN(SELECT idapp,employee_name FROM employee) emp2 ON emp2.idapp = ngds.FK_Acknowledge2
				LEFT OUTER JOIN(SELECT idapp,employee_name FROM employee) emp3 ON emp3.idapp = ngds.FK_ApprovedBy
		        WHERE """ + colKey + rs.Sql() + ")"
		cur.execute(Query)
		strLimit = '300'
		if int(PageIndex) <= 1:
			strLimit = '0'
		else:
			strLimit = str(int(PageIndex)*int(pageSize))
		if orderFields != '':
			#Query = """SELECT * FROM T_Receive_Manager """ + (("ORDER BY " + ",".join(orderFields)) if len(orderFields) > 1 else " ORDER BY " + orderFields[0]) + (" DESC" if sortIndice == "" else sortIndice) + " LIMIT " + str(pageSize*(0 if PageIndex <= 1 else PageIndex)) + "," + str(pageSize)
			Query = """SELECT * FROM T_Disposal_Manager_""" + userName + """ ORDER BY """ + orderFields + (" DESC" if sortIndice == "" else ' ' + sortIndice) + " LIMIT " + strLimit + "," + str(pageSize)
		else:			
			Query = """SELECT * FROM T_Disposal_Manager_""" + userName + """ ORDER BY IDApp LIMIT """ + strLimit + "," + str(pageSize)
		cur.execute(Query)
		result = query.dictfetchall(cur)
		#get countRows
		Query = """SELECT COUNT(*) FROM T_Disposal_Manager_""" + userName
		cur.execute(Query)
		row = cur.fetchone()
		totalRecords = row[0]
		cur.close()
		return (result,totalRecords)
	def getBrandForOutwards(self,searchText,orderFields,sortIndice,pageSize,PageIndex,userName):
		cur = connection.cursor()
		Query =  "DROP TEMPORARY TABLE IF EXISTS Temp_T_History_Disposal_" + userName		
		cur.execute(Query)
				#Query new items
		Query = "CREATE TEMPORARY TABLE Temp_T_Receive_Outwards_" + userName  + """ ENGINE=MyISAM AS (SELECT g.idapp,g.itemcode as fk_goods,g.goodsname,IFNULL(ngd.BrandName,g.BrandName) AS brandname,ngd.typeapp AS type,ngd.serialnumber, '' AS fk_usedemployee,'' AS usedemployee, '' as lastinfo,ngd.idapp as fk_receive, \
					0 AS fk_outwards,0 as fk_lending,0 AS fk_return,0 AS fk_maintenance,0 AS fk_disposal,0 AS fk_lost FROM n_a_goods g INNER JOIN n_a_goods_receive ngr ON ngr.fk_goods = g.IDApp INNER JOIN n_a_goods_receive_detail ngd ON ngr.IDApp = ngd.FK_App \
					WHERE NOT EXISTS(SELECT IDApp FROM n_a_goods_history WHERE fk_goods = ngr.fk_goods AND serialnumber = ngd.serialnumber)) """
		cur.execute(Query)
	    # Query get last trans in history 		
		Query = "CREATE TEMPORARY TABLE Temp_T_History_Outwards_" + userName  + """ ENGINE=MyISAM AS (SELECT gh.idapp,gh.fk_goods,gh.goodsname,gh.brandname,gh.type,gh.serialnumber, \
                    CASE 
                        WHEN (gh.fk_return IS NOT NULL) THEN (SELECT e.NIK FROM employee e INNER JOIN n_a_goods_return ngn ON ngn.fk_usedemployee = e.idapp WHERE ngn.idapp = gh.fk_return) \
                        WHEN (gh.fk_lending IS NOT NULL) THEN ((SELECT e.NIK FROM employee e INNER JOIN n_a_goods_lending ngl ON ngl.fk_employee = e.idapp WHERE ngl.idapp = gh.fk_lending)) \
						--tambahan join ke outwards
						END AS fk_usedemployee,
                    CASE 
                    WHEN (gh.fk_return IS NOT NULL) THEN (SELECT e.employee_name FROM employee e INNER JOIN n_a_goods_return ngn ON ngn.fk_usedemployee = e.idapp WHERE ngn.idapp = gh.fk_return) \
                    END AS usedemployee,
					CASE \
						WHEN (gh.fk_maintenance IS NOT NULL) THEN (SELECT CONCAT('Maintenance by ', IFNULL(maintenanceby,''), ' ',	IFNULL(PersonalName,''), \
							(CASE \
								WHEN (isfinished = 1 AND issucced = 1) THEN (CONCAT(' Date Returned  ',DATE_FORMAT(enddate,'%d %B %Y'),' (goods is able to dispose/delete)')) \
								WHEN (isfinished = 1 AND issucced = 0) THEN (CONCAT(' Date Returned ',DATE_FORMAT(enddate,'%d %B %Y'),' (goods is able to dispose/delete )')) \
								WHEN (isfinished = 0) THEN (CONCAT(' Date maintenance ',DATE_FORMAT(enddate,'%d %B %Y'),' (goods is still in maintenance)')) \
								END)) FROM n_a_maintenance WHERE IDApp = gh.fk_maintenance) \
						WHEN(gh.fk_lending IS NOT NULL) THEN((CASE \
																WHEN ((SELECT `status` FROM n_a_goods_lending WHERE idapp = gh.fk_lending) = 'L') THEN 'good is still lent' \
																ELSE ('goods is able to use') \
																END)) \
						--lastrepairfrom,
						WHEN(gh.fk_outwards IS NOT NULL) THEN 'goods is still in use by other employee' \
						WHEN (gh.fk_return IS NOT NULL) THEN '(goods is able to dispose/delete )' \
						WHEN (gh.fk_disposal IS NOT NULL) THEN '(goods has been disposed/deleted )' \
						WHEN (gh.fk_lost IS NOT NULL) THEN 'goods has lost' \
						ELSE 'Unknown or uncategorized last goods position' \
						END AS lastinfo,
                        gh.fk_receive,gh.fk_outwards,gh.fk_lending,gh.fk_return,gh.fk_maintenance,gh.fk_disposal,gh.fk_lost  \
						FROM(			\
							SELECT g.idapp,g.itemcode as  fk_goods,g.goodsname,IFNULL(ngd.brandName,g.brandName) AS brandName,ngd.typeapp as 'type',ngd.serialnumber,ngd.idapp AS fk_receive,ngh.fk_outwards,ngh.fk_lending, \
							ngh.fk_return,ngh.fk_maintenance,ngh.fk_disposal,ngh.fk_lost FROM \
							n_a_goods g INNER JOIN n_a_goods_receive ngr ON g.idapp = ngr.fk_goods INNER JOIN n_a_goods_receive_detail ngd ON ngd.fk_app = ngr.idapp \
							INNER JOIN n_a_goods_history ngh ON ngh.fk_goods = g.idapp AND ngh.serialnumber = ngd.serialnumber \
							WHERE ngh.createddate = (SELECT Max(CreatedDate) FROM n_a_goods_history WHERE fk_goods = g.idapp AND serialnumber = ngd.serialnumber))gh
                             )				
				"""
		cur.execute(Query)
		strLimit = '300'
		if int(PageIndex) <= 1:
			strLimit = '0'
		else:
			strLimit = str(int(PageIndex)*int(pageSize))