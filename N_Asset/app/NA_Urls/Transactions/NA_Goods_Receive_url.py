from django.conf.urls import url
from app.NA_Views.Transactions import NA_Goods_Receive_View

urlpatterns = [
	url(r'^$',NA_Goods_Receive_View.NA_Goods_Receive,name='GoodsReceive'),
	url(r'^NA_Goods_Receive_Search/$',NA_Goods_Receive_View.NA_Goods_Receive_Search,name='GoodsReceiveManager'),
	url(r'^ShowEntry_Receive',NA_Goods_Receive_View.ShowEntry_Receive,name='ShowEntryReceivey'),
	url(r'^getGoods/$',NA_Goods_Receive_View.getGoods,name='getGoods'),
	url(r'^Delete/$',NA_Goods_Receive_View.Delete,name='delete'),
	url(r'^HasExists/$',NA_Goods_Receive_View.HasExists,name='HasExists'),
	url(r'^getSuplier/$',NA_Goods_Receive_View.getSuplier,name='getSuplier'),
	url(r'^getEmployee/$',NA_Goods_Receive_View.getEmployee,name='getEmployee'),
	url(r'^SearchGoodsbyForm/$',NA_Goods_Receive_View.SearchGoodsbyForm,name='SearchGoodsbyForm'),
	url(r'^SearchSuplierbyForm/$',NA_Goods_Receive_View.SearchSuplierbyForm,name='SearchSuplierbyForm'),
	url(r'^SearchEmployeebyform/$',NA_Goods_Receive_View.SearchEmployeebyform,name='SearchEmployeebyform'),
	url(r'^getBrandForDetailEntry/$',NA_Goods_Receive_View.getBrandForDetailEntry,name='getBrandForDetailEntry'),
	url(r'^getTypeApps/$',NA_Goods_Receive_View.getTypeApps,name='getTypeApps'),
	url(r'^getRefNO/$',NA_Goods_Receive_View.getRefNO,name='getRefNO'),
	url(r'^deleteDetail/$',NA_Goods_Receive_View.deleteDetail,name='deleteDetail'),
	url(r'^customFilter/$',NA_Goods_Receive_View.ShowCustomFilter,name='ShowCustomFilter_Receiving'),
]