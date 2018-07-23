from django.db import models
from NA_DataLayer.common import *
from django.db import transaction;
from django.db import connection
from decimal import Decimal
from django.db.models import Q
from NA_DataLayer.common import commonFunct
from distutils.util import strtobool
import math
import datetime
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
				ngds.bookvalue,	ngds.datedisposal,ngds.islost,	
				CASE					
					WHEN (ngds.FK_Return IS NOT NULL) THEN 'Returned Eks Employee'
					WHEN (ngds.fk_maintenance IS NOT NULL) THEN 'After Service(Maintenance)'
					WHEN (ngds.FK_Lending IS NOT NULL) THEN '(After being Lent)'
					WHEN (ngds.FK_Outwards IS NOT NULL) THEN '(Direct Return)'
					ELSE 'Other (Uncategorized)'
					END AS refgoodsfrom,							
				ngds.issold,ngds.sellingprice,IFNULL(emp.responsible_by,'') AS proposedby,CONCAT(IFNULL(emp1.employee_name,''), ', ',IFNULL(emp2.employee_name,'')) AS acknowledgeby,IFNULL(emp3.employee_name,'') AS approvedby 
				,ngds.descriptions,ngds.createdby,ngds.createddate		       
		        FROM n_a_disposal ngds INNER JOIN n_a_goods g ON g.IDApp = ngds.FK_Goods 
		        INNER JOIN n_a_goods_receive ngr ON ngr.FK_goods = ngds.FK_Goods
		        INNER JOIN n_a_goods_receive_detail ngd ON ngd.FK_App = ngr.IDApp
		        AND ngds.SerialNumber = ngd.SerialNumber

		        LEFT OUTER JOIN (SELECT idapp,employee_name AS responsible_by FROM employee) emp ON emp.idapp = ngds.fk_proposedby
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
	def getBookValue(self,cur,**kwargs):
			"""Function untuk mengambil nilai buku
			:param int idapp = idapp_fk_goods
			:param SerialNo
			:param DateDisposal
			return [int fk_acc_fa,float bookvalue]
			"""
			fk_goods = 0
			serialno = ''
			datedisposal = None
			fk_goods = int(kwargs['idapp'])
			serialno = kwargs['SerialNo'];
			datedisposal = kwargs['DateDisposal']
			isNewCur = False
			Query = """SELECT EXISTS(SELECT fk_goods FROM n_a_acc_fa WHERE fk_goods = %(FK_Goods)s AND SerialNumber = %(SerialNO)s)"""
			if cur is None:
				cur = connection.cursor()
				isNewCur = True
			cur.execute(Query,{'FK_Goods':fk_goods,'SerialNO':kwargs['SerialNo']})
			row = cur.fetchone()
			if int(row[0]) > 0:
				Query = """SELECT idapp, bookvalue FROM n_a_acc_fa WHERE fk_goods = %(FK_Goods)s AND SerialNumber = %(SerialNO)s AND (DateDepreciation >= %(DateDisposal)s AND DateDepreciation <= (DATE_ADD((DATE_ADD(%(DateDisposal)s , INTERVAL 2 day)),INTERVAL -1 DAY)))"""
				cur.execute(Query,{'FK_Goods':fk_goods,'SerialNO':serialno,'DateDisposal':datedisposal})
				row = cur.fetchone()
				if row is not None:
					if isNewCur:
						cur.close()
					return [int(row[0]),float(row[1])]
				else:
					if isNewCur:
						cur.close()
					return None
			else:
				cur.close()
				raise Exception(r"Can not find asset's book value")
	def getBrandForDisposal(self,searchText,orderFields,sortIndice,pageSize,PageIndex,userName):
		cur = connection.cursor()
		Query =  "DROP TEMPORARY TABLE IF EXISTS Temp_T_History_Disposal_" + userName		
		cur.execute(Query)
		Query = " DROP TEMPORARY TABLE IF EXISTS Temp_F_Disposal_" + userName
		cur.execute(Query)
	    # Query get last trans in history 		
		Query = "CREATE TEMPORARY TABLE Temp_T_History_Disposal_" + userName  + """ ENGINE=MyISAM AS (SELECT gh.idapp,gh.fk_goods,gh.goodsname,gh.brandname,gh.type,gh.serialnumber, \
                    CASE 
                        WHEN (gh.fk_return IS NOT NULL) THEN (SELECT e.NIK FROM employee e INNER JOIN n_a_goods_return ngn ON ngn.fk_usedemployee = e.idapp WHERE ngn.idapp = gh.fk_return) \
                        WHEN (gh.fk_lending IS NOT NULL) THEN (SELECT e.NIK FROM employee e INNER JOIN n_a_goods_lending ngl ON ngl.fk_employee = e.idapp WHERE ngl.idapp = gh.fk_lending) \
						WHEN (gh.fk_lost IS NOT NULL) THEN (SELECT e.NIK FROM employee e INNER JOIN n_a_goods_lost ngls on ngls.FK_UsedBy = e.idapp WHERE ngls.idapp = gh.fk_lost) \
						END AS fk_usedemployee,
                   CASE 
						WHEN (gh.fk_return IS NOT NULL) THEN (SELECT e.employee_name FROM employee e INNER JOIN n_a_goods_return ngn ON ngn.fk_usedemployee = e.idapp WHERE ngn.idapp = gh.fk_return) \
						END AS usedemployee,
					CASE \
						WHEN (gh.fk_maintenance IS NOT NULL) THEN (SELECT CONCAT('Maintenance by ', IFNULL(maintenanceby,''), ' ',	IFNULL(PersonalName,''), \
							(CASE \
								WHEN (isfinished = 1 AND issucced = 1) THEN (CONCAT(' Date Returned  ',DATE_FORMAT(enddate,'%d %B %Y'),'goods is able to dispose/delete')) \
								WHEN (isfinished = 1 AND issucced = 0) THEN (CONCAT(' Date Returned ',DATE_FORMAT(enddate,'%d %B %Y'),'goods is able to dispose/delete')) \
								WHEN (isfinished = 0) THEN (CONCAT(' Date maintenance ',DATE_FORMAT(enddate,'%d %B %Y'),'goods is still in maintenance')) \
								END)) FROM n_a_maintenance WHERE IDApp = gh.fk_maintenance) \
						WHEN(gh.fk_lending IS NOT NULL) THEN((CASE \
																WHEN ((SELECT `status` FROM n_a_goods_lending WHERE idapp = gh.fk_lending) = 'L') THEN 'good is still lent' \
																ELSE ('goods is able to dispose/delete') \
																END)) \
						WHEN(gh.fk_outwards IS NOT NULL) THEN 'goods is still in use by other employee' \
						WHEN (gh.fk_return IS NOT NULL) THEN 'goods is able to dispose/delete' \
						WHEN (gh.fk_disposal IS NOT NULL) THEN 'goods has been disposed/deleted' \
						WHEN (gh.fk_lost IS NOT NULL) THEN 'goods has lost' \
						ELSE 'Unknown or uncategorized last goods position' \
						END AS lastinfo,
                        gh.fk_receive,gh.fk_outwards,gh.fk_lending,gh.fk_return,gh.fk_maintenance,gh.fk_lost  \
						FROM(\
							SELECT g.idapp,g.itemcode as  fk_goods,g.goodsname,IFNULL(ngd.brandName,g.brandName) AS brandName,ngd.typeapp as 'type',ngd.serialnumber,ngd.idapp AS fk_receive,ngh.fk_outwards,ngh.fk_lending, \
							ngh.fk_return,ngh.fk_maintenance,ngh.fk_disposal,ngh.fk_lost FROM \
							n_a_goods g INNER JOIN n_a_goods_receive ngr ON g.idapp = ngr.fk_goods INNER JOIN n_a_goods_receive_detail ngd ON ngd.fk_app = ngr.idapp \
							INNER JOIN n_a_goods_history ngh ON ngh.fk_goods = g.idapp AND ngh.serialnumber = ngd.serialnumber \
							WHERE ngh.createddate = (SELECT Max(CreatedDate) FROM n_a_goods_history WHERE fk_goods = g.idapp AND serialnumber = ngd.serialnumber)\
							UNION \
							SELECT g.idapp,g.itemcode as  fk_goods,g.goodsname,IFNULL(nggr.Brand,g.BrandName) AS BrandName,nggr.typeapp as 'type',nggr.Machine_No AS serialnumber,nggr.idapp AS fk_receive,ngh.fk_outwards,ngh.fk_lending, \
							ngh.fk_return,ngh.fk_maintenance,ngh.fk_disposal,ngh.fk_lost FROM \
							n_a_goods g INNER JOIN n_a_ga_receive nggr ON g.idapp = nggr.fk_goods \
							INNER JOIN n_a_goods_history ngh ON ngh.fk_goods = g.idapp AND ngh.serialnumber = nggr.Machine_No \
							WHERE ngh.createddate = (SELECT Max(CreatedDate) FROM n_a_goods_history WHERE fk_goods = g.idapp AND serialnumber = nggr.Machine_No) \
							)gh
                      )				
				"""
		cur.execute(Query)
		strLimit = '300'
		if int(PageIndex) <= 1:
			strLimit = '0'
		else:
			strLimit = str(int(PageIndex)*int(pageSize))
		#gabungkan jadi satu
		Query = "CREATE TEMPORARY TABLE Temp_F_Disposal_" + userName + """ ENGINE=MyISAM AS (
				 SELECT * FROM Temp_T_History_Disposal_""" + userName + """\
				  WHERE (goodsname LIKE %s OR brandname LIKE %s) OR (serialnumber = %s))"""
		cur.execute(Query,['%'+searchText+'%','%'+searchText+'%',searchText])
		if orderFields == '':
			Query  = "SELECT *,CONVERT((CASE lastinfo WHEN '(goods has been disposed/deleted)' THEN 1 \
								ELSE 0),INT) AS Ready FROM Temp_F_Disposal_" + userName + " ORDER BY goodsname " + (" DESC" if sortIndice == "" else ' ' + sortIndice) + " LIMIT " + strLimit + "," + str(pageSize)	
		else:
			Query  = "SELECT * FROM Temp_F_Disposal_" + userName + " ORDER BY " + orderFields + (" DESC" if sortIndice == "" else ' ' + sortIndice) + " LIMIT " + strLimit + "," + str(pageSize)				
		cur.execute(Query)
		result = query.dictfetchall(cur)

		Query = "SELECT COUNT(*) FROM Temp_F_Disposal_" + userName
		cur.execute(Query)
		row = cur.fetchone()
		totalRecords = row[0]
		cur.close()
		return (result,totalRecords)
	def getLastTrans(self,SerialNO):
		idapp_fk_goods = 0
		itemcode = ''		
		goodsname = ''
		typeapp = ''
		brandname = ''
		serialnumber = ''
		lastinfo = 'unknown'
		islost = False
		bookvalue = 0
		fk_acc_fa = 0
		fk_usedemployee = 'NIK';usedemployee = 'unknown';fkaccfa = 0;fkreturn = 0;fklending = 0;fkoutwards = 0;fkmaintenance = 0;
		Query = """SELECT g.idapp,g.itemcode,g.goodsname,IFNULL(ngd.BrandName,g.BrandName) AS BrandName,ngd.typeapp FROM n_a_goods_receive_detail ngd INNER JOIN n_a_goods_receive ngr ON ngr.IDApp = ngd.FK_App \
						LEFT OUTER JOIN n_a_goods g ON g.IDApp = ngr.FK_Goods WHERE ngd.serialnumber = %s AND g.typeapp = 'IT' """
		cur = connection.cursor()
		cur.execute(Query,[SerialNO])
		recCount =  cur.rowcount
		##idapp_fk_goods,itemcode,islost,fidapp_fk_usedemployee,fk_acc_fa,fk_maintenance,fk_return,fk_lending,fk_outwards,goods,brandname,typeapp,bookvalue,lastinfo

		row = []
		if recCount > 0:
			row = cur.fetchone()
			typeapp = row[4]
			brandname = row[3]
			goodsname = row[2]
			itemcode = row[1]
			idapp_fk_goods = row[0]
		else:
			Query = """SELECT g.idapp,g.itemcode,g.goodsname,IFNULL(nggr.Brand,g.BrandName) AS BrandName,nggr.typeapp FROM n_a_ga_receive nggr INNER JOIN n_a_goods g ON g.IDApp = nggr.fk_goods \
				WHERE nggr.Machine_No = %s AND g.typeapp = 'GA'"""
			cur = connection.cursor()
			cur.execute(Query,[SerialNO])
			recCount =  cur.rowcount
			if recCount > 0:
				row = cur.fetchone()
				typeapp = row[4]
				brandname = row[3]
				goodsname = row[2]
				itemcode = row[1]
				idapp_fk_goods = row[0]
			else:
				cur.close()
				raise Exception('no such data')
		#ambil nilai buku,default ambil tanggal akhir = sekarang
		bkData = self.getBookValue(cur,idapp=idapp_fk_goods,SerialNo=SerialNO,DateDisposal=datetime.date.today())
		if bkData is not None:
			bookvalue = bkData[0]
			fk_acc_fa = bkData[1]
		#cek apakah data sudah di disposed sebelumnya
		Query = """SELECT EXISTS(SELECT SerialNumber FROM n_a_disposal WHERE serialnumber =  %s AND fk_goods = %s)"""
		cur.execute(Query,[SerialNO,idapp_fk_goods])
		row = cur.fetchone()
		if int(row[0]) >0:
			cur.close()
			raise Exception('asset has been disposed/deleted')
		#cek apakah sudah ada transaksi untuk barang dengan serial number tsb
		Query = """SELECT EXISTS(SELECT serialnumber FROM n_a_goods_history WHERE serialnumber = %s AND fk_goods = %s)"""
		cur.execute(Query,[SerialNO,idapp_fk_goods])
		row = cur.fetchone()
		if int(row[0]) > 0:
			#cek apakah data sudah di 
			#jika ada ambil data transaksi terakhir yang mana transaksi ada 4 kelompok,lending,outwards,return,maintenance
			Query = """SELECT FK_Lending,FK_Outwards,FK_Return,FK_Maintenance,fk_lost FROM n_a_goods_history WHERE serialnumber = %s AND fk_goods = %s ORDER BY createddate DESC LIMIT 1 """
			cur.execute(Query,[SerialNO,idapp_fk_goods])
			row = cur.fetchone()
			if cur.rowcount > 0:
				if row[0] is not None:
					fklending = row[0]
				if row[1] is not None:
					fkoutwards =row[1]
				if row[2] is not None:
					fkreturn = row[2]
				if row[3] is not None:
					fkmaintenance = row[3]
				if row[4] is not None:
					fklost = row[4]
			if int(fklending)>0:#fklending hanya di goods IT 
				Query = """SELECT e.nik,e.employee_name,ngl.datelending,ngl.interests FROM n_a_goods_lending ngl INNER JOIN employee e ON e.idapp = ngl.FK_Employee
							WHERE ngl.IDApp = %s"""
				cur.execute(Query,[fklending])
				if cur.rowcount > 0:
					row = cur.fetchone()
					lastInfo = 'Last used by ' + str(row[0]) + '|' +  str(row[1]) + ', date lent ' + parse(str(row[2])).strftime('%d %B %Y') + ', interests ' + str(row[3])
					fk_usedemployee = str(row[0])
					usedemployee = str(row[1])
			elif int(fkoutwards) > 0:
				if Category == 'IT':
					Query = """SELECT e.nik,e.employee_name,ngo.datereleased,ngo.descriptions FROM n_a_goods_outwards ngo INNER JOIN employee e ON e.idapp = ngo.FK_Employee
							WHERE ngo.IDApp = %s"""
				else :
					Query = """SELECT e.nik,e.employee_name,nggo.datereleased,nggo.descriptions FROM n_a_ga_outwards nggo INNER JOIN employee e ON e.idapp = nggo.FK_Employee
							WHERE nggo.IDApp = %s"""
				cur.execute(Query,[fkoutwards])
				if cur.rowcount > 0:
					row = cur.fetchone()
					lastInfo = 'Last used by ' + str(row[0]) + '|' + str(row[1]) + ', date released ' + parse(str(row[2])).strftime('%d %B %Y') + ', ' + str(row[3]) + ' (goods is still in use)'
					fk_usedemployee = str(row[0])
					usedemployee = str(row[1])
			elif int(fkreturn) > 0:
				if Category == 'IT':
					Query = """SELECT e.NIK,e.employee_name,ngt.datereturn,ngt.descriptions FROM n_a_goods_return ngt INNER JOIN employee e ON e.idapp = ngt.FK_FromEmployee
							WHERE ngt.IDApp = %s"""
				else:
					Query = """SELECT E.NIK,e.employee_name,nggt.datereturn,nggt.descriptions FROM n_a_goods_return nggt INNER JOIN employee e ON e.idapp = nggt.FK_FromEmployee
							WHERE ngt.IDApp = %s"""
				cur.execute(Query,[fkreturn])
				if cur.rowcount > 0:
					row = cur.fetchone()
					lastInfo = 'Last used by ' + str(row[0]) + '|' + str(row[1]) + ', date returned ' + parse(str(row[2]).strftime('%d %B %Y')) + ', ' + str(row[3]) + ' (goods is already returned)'
					fk_usedemployee = str(row[0])
					usedemployee = str(row[1])
			elif int(fkmaintenance) > 0:#nadisposal tidak ada reference dari maintenance, karena barang di hapus harus hanya hilang/sesudah ada fisiknya(direturn dari pegawai ke kantor atau dari daerah pegawai langsung di jual)/di return dari bengkel ke kantor
				Query = """SELECT CONCAT(IFNULL(maintenanceby,''), ' ',	IFNULL(PersonalName,'')) as maintenanceby,StartDate,EndDate, IsFinished,IsSucced FROM n_a_maintenance WHERE IDApp  = %s"""
				cur.execute(Query,[fkmaintenance])
				if cur.rowcount > 0:
					row = cur.fetchone()
					isFinished = False;isSucced = False;starDate = datetime.now();endDate = datetime.now()
					if row[3] is not None:
						isFinished = strtobool(row[3])
					if row[4] is not None:
						isSucced = strtobool(row[4])
					if row[1] is not None:
						starDate =  parse(str(row[1])).strftime('%d %B %Y')
					if row[2] is not None:
						endDate =  parse(str(row[2])).strftime('%d %B %Y')
					if isFinished and isSucced:
						lastInfo = 'Last maintenance by ' + str(row[0]) + ', date returned ' + endDate + ', ' +  ' (goods is able to use)'
					elif isFinished == True and isSucced == false:
						lastInfo = 'Last maintenance by ' + str(row[0]) + ', date returned ' + endDate + ', ' +  ' (goods is unable to use )'
					elif not isFInished:
						lastInfo = 'Last maintenance by ' + str(row[0]) + ', start date maintenance ' + starDate + ', ' +  ' (goods is still in maintenance)'
			elif int(fklost) > 0:
				Query = """SELECT fk_goods_lending,fk_goods_outwards,fk_maintenance,Reason,status FROM n_a_goods_lost WHERE idapp = %s"""
				cur.execute(Query,[fklost])
				lastInfo = "goods has lost "
				if cur.rowcount > 0:
					islost = True
					row = cur.fetchone()
					fk_lost_lending = 0;fk_lost_outwards = 0;fk_lost_maintenance = 0;
					if row[0] is not None:
						fk_lost_lending = row[0]
					if  row[1] is not None:
						fk_lost_outwards = row[1]
					if row[2] is not None:
						fk_lost_maintenance = row[2]
					reason = row[3]
					lost_status = row[4]
					if lost_status == "F":
						if int(fk_lost_lending) > 0:#fklending hanya di goods IT 
							Query = """SELECT e.NIK,e.employee_name,ngl.datelending,ngl.interests FROM n_a_goods_lending ngl INNER JOIN employee e ON e.idapp = ngl.FK_Employee
									WHERE ngl.IDApp = %s"""
							cur.execute(Query,[fk_lost_lending])
							if cur.rowcount > 0:
								row = cur.fetchone()
								lastInfo = 'Last used by ' + str(row[0]) + '|' + str(row[1]) + ', date lent ' + parse(str(row[2])).strftime('%d %B %Y') + ', interests ' + str(row[3])
								fk_usedemployee = str(row[0])
								usedemployee = str(row[1])
						elif int(fk_lost_outwards) > 0:
							if Category == 'IT':
								Query = """SELECT e.nik,e.employee_name,ngo.datereleased,ngo.descriptions FROM n_a_goods_outwards ngo INNER JOIN employee e ON e.idapp = ngo.FK_Employee
									WHERE ngo.IDApp = %s"""
							else :
								Query = """SELECT e.nik,e.employee_name,nggo.datereleased,nggo.descriptions FROM n_a_ga_outwards nggo INNER JOIN employee e ON e.idapp = nggo.FK_Employee
									WHERE nggo.IDApp = %s"""
							cur.execute(Query,[fk_lost_outwards])
							if cur.rowcount > 0:
								row = cur.fetchone()
								lastInfo = 'Last used by ' + str(row[0]) + '|' + str(row[1]) + ', date released ' + parse(str(row[2])).strftime('%d %B %Y') + ', ' + str(row[3]) + ' (goods is still in use)'
								fk_usedemployee = str(row[0])
								usedemployee = str(row[1])
						elif int(fk_lost_maintenance) > 0:#nadisposal tidak ada reference dari maintenance, karena barang di hapus harus hanya hilang/sesudah ada fisiknya(direturn dari pegawai ke kantor atau dari daerah pegawai langsung di jual)/di return dari bengkel ke kantor
							Query = """SELECT CONCAT(IFNULL(maintenanceby,''), ' ',	IFNULL(PersonalName,'')) as maintenanceby,StartDate,EndDate, IsFinished,IsSucced FROM n_a_maintenance WHERE IDApp  = %s"""
							cur.execute(Query,[fk_lost_maintenance])
							if cur.rowcount > 0:
								row = cur.fetchone()
								isFinished = False;isSucced = False;starDate = datetime.now();endDate = datetime.now()
								if row[3] is not None:
									isFinished = strtobool(row[3])
									if row[4] is not None:
										isSucced = strtobool(row[4])
								if row[1] is not None:
									starDate =  parse(str(row[1])).strftime('%d %B %Y')
								if row[2] is not None:
									endDate =  parse(str(row[2])).strftime('%d %B %Y')
							if isFinished and isSucced:
								lastInfo = 'Last maintenance by ' + str(row[0]) + ', date returned ' +endDate + ', ' +  ' (goods is able to use)'
							elif isFinished == True and isSucced == false:
								lastInfo = 'Last maintenance by ' + str(row[0]) + ', date returned ' + endDate + ', ' +  ' (goods is unable to use)'
							elif not isFInished:
								lastInfo = 'Last maintenance by ' + str(row[0]) + ', start date maintenance ' +starDate + ', ' +  ' (goods is still in maintenance)'
						#elif fk_lost_outwards
						else:
							lastInfo = "goods has lost, but has been found "
		else:
			if Category == 'IT':
				Query = """SELECT ngl.idapp as fk_receive,ngl.brandname,ngl.typeapp,ngr.datereceived FROM n_a_goods_receive_detail ngl INNER JOIN n_a_goods_receive ngr ON ngr.IDApp = ngl.FK_App WHERE ngl.serialnumber = %s"""
			else:
				Query = """SELECT nggr.idapp as fk_receive,nggr.brand,nggr.typeapp,nggr.datereceived FROM n_a_ga_receive nggr WHERE nggr.serialnumber = %s AND nggr.fk_goods = %"""
			cur.execute(Query,[SerialNO,idapp_fk_goods])
			dt = datetime.now()
			row = []
			if cur.rowcount > 0:
				dt = datetime.date(row[2])
				cur.close()
				raise Exception('goods has not been used (probably is still new, date received' + dt.strftime('%d %B %Y') + ')')
			else:
				cur.close()
				raise Exception('no such data')
		###idapp_fk_goods,itemcode,goods,brandname,typeappp,islost,idapp_fk_usedemployee,usedemployee,fk_acc_fa,lastinfo,bookvalue,fk_maintenance,fk_return,fk_lending,fk_outwards
		return(idapp_fk_goods,itemcode,goodsname,brandname,typeapp,islost,fk_usedemployee, usedemployee,fk_acc_fa,bookvalue,lastInfo,fkmaintenance,fkreturn,fklending,fkoutwards)