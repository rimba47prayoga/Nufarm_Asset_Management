﻿from django.http import HttpResponse
from django.shortcuts import render
from NA_Models.models import Employee, LogEvent
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
import datetime
import json
from NA_DataLayer.common import (CriteriaSearch, ResolveCriteria,
                                 StatusForm, commonFunct, Data, decorators)
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django import forms


@decorators.ensure_authorization
def NA_Employee(request):
    return render(request, 'app/MasterData/NA_F_Employee.html')

@decorators.ensure_authorization
@decorators.ajax_required
def NA_EmployeeGetData(request):
    IcolumnName = request.GET.get('columnName')
    IvalueKey = request.GET.get('valueKey')
    IdataType = request.GET.get('dataType')
    Icriteria = request.GET.get('criteria')
    Ilimit = request.GET.get('rows', '')
    Isidx = request.GET.get('sidx', '')
    Isord = request.GET.get('sord', '')
    if(',' in Isidx):
        Isidx = Isidx.split(',')

    criteria = ResolveCriteria.getCriteriaSearch(str(Icriteria))
    dataType = ResolveCriteria.getDataType(str(IdataType))
    if(Isord is not None and str(Isord) != ''):
        emplData = Employee.objects.PopulateQuery(
            IcolumnName, IvalueKey, criteria, dataType).order_by('-' + str(Isidx))
    else:
        emplData = Employee.objects.PopulateQuery(
            IcolumnName, IvalueKey, criteria, dataType)

    totalRecord = emplData.count()
    paginator = Paginator(emplData, int(Ilimit))
    try:
        page = request.GET.get('page', '1')
    except ValueError:
        page = 1
    try:
        data = paginator.page(page)
    except (EmptyPage, InvalidPage):
        data = paginator.page(paginator.num_pages)

    rows = []
    i = 0
    for row in data.object_list:
        i += 1
        datarow = {"id": row['idapp'], "cell": [row['idapp'], i, row['nik'], row['employee_name'], row['typeapp'], row['jobtype'], row['gender'],
                                                row['status'], row['telphp'], row['territory'], row['descriptions'], row['inactive'], row['createddate'], row['createdby']]}
        rows.append(datarow)
    results = {"page": data.number, "total": paginator.num_pages,
               "records": totalRecord, "rows": rows}
    return HttpResponse(json.dumps(results, indent=4, cls=DjangoJSONEncoder), content_type='application/json')


class NA_Employee_form(forms.Form):
    nik = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'NA-Form-Control', 'placeholder': 'Enter Nik'}))
    employee_name = forms.CharField(max_length=40, required=True, widget=forms.TextInput(attrs={
        'class': 'NA-Form-Control', 'placeholder': 'Enter Employee Name'}))
    typeapp = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={
        'class': 'NA-Form-Control', 'placeholder': 'Type of Employee'}))
    jobtype = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'NA-Form-Control', 'placeholder': 'Jobtype'}))
    gender = forms.CharField(required=True, widget=forms.RadioSelect(
        choices=[('M', 'Male'), ('F', 'Female')]))
    status = forms.CharField(required=True, widget=forms.RadioSelect(
        choices=[('S', 'Single'), ('M', 'Married')]))
    telphp = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={
        'class': 'NA-Form-Control', 'placeholder': 'Phone Number'}))
    territory = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'NA-Form-Control', 'placeholder': 'Territory'}))
    descriptions = forms.CharField(max_length=250, required=True, widget=forms.Textarea(attrs={
        'class': 'NA-Form-Control', 'placeholder': 'Descriptions of Employee', 'cols': '100', 'rows': '2', 'style': 'height: 50px;clear:left;width:500px;max-width:600px'}))
    inactive = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    window_status = forms.CharField(widget=forms.HiddenInput(), required=False)
    initializeForm = forms.CharField(
        widget=forms.HiddenInput(), required=False)


def getCurrentUser(request):
    return str(request.user.username)


def getData(request, form):
    clData = form.cleaned_data
    data = {'nik': clData['nik'], 'employee_name': clData['employee_name'], 'typeapp': clData['typeapp'],
            'jobtype': clData['jobtype'], 'gender': clData['gender'], 'status': clData['status'], 'telphp': clData['telphp'],
            'territory': clData['territory'], 'descriptions': clData['descriptions'], 'inactive': clData['inactive'],
            }
    return data


@decorators.ajax_required
@decorators.detail_request_method('POST')
def Set_InActive(request):
    idapp = request.POST['idapp']
    inactive = request.POST['inactive']
    result = Employee.objects.setInActive(
        idapp, commonFunct.str2bool(inactive))
    return commonFunct.response_default(result)


@decorators.read_permission(form_name='employee')
def EntryEmployee(request):
    if request.method == 'POST':
        form = NA_Employee_form(request.POST)
        if form.is_valid():
            mode = request.POST['mode']
            data = getData(request, form)
            if mode == 'Add':
                data['createddate'] = datetime.datetime.now()
                data['createdby'] = getCurrentUser(request)
                result = Employee.objects.SaveData(**data)
                return commonFunct.response_default(result)
            elif mode == 'Edit':
                getIdapp = request.POST['idapp']
                data['idapp'] = getIdapp
                data['modifieddate'] = datetime.datetime.now()
                data['modifiedby'] = getCurrentUser(request)
                result = Employee.objects.SaveData(StatusForm.Edit, **data)
                return commonFunct.response_default(result)
            elif mode == 'Open':
                if request.POST['employee_name']:
                    return HttpResponse(
                        json.dumps({
                            'messages': 'You\'re try to Edit this Data \
                            with Open Mode\nWith technic inspect element\n Lol :D'
                        }),
                        status=403,
                        content_type='application/json'
                    )
    elif request.method == 'GET':
        idapp = request.GET['idapp']
        mode = request.GET['mode']
        if mode == 'Edit' or mode == 'Open':
            result = Employee.objects.retriveData(idapp)
            if result[0] == Data.Lost:
                return HttpResponse(json.dumps({'message': result[0]}), status=404, content_type='application/json')
            form = NA_Employee_form(initial=result[1])
            form.fields['nik'].widget.attrs['disabled'] = 'disabled'
        else:
            form = NA_Employee_form()
            del form.fields['inactive']
        return render(request, 'app/MasterData/NA_Entry_Employee.html', {'form': form})


@decorators.ajax_required
@decorators.detail_request_method('GET')
def ShowCustomFilter(request):
    cols = []
    cols.append({'name': 'nik', 'value': 'nik', 'selected': '',
                 'dataType': 'varchar', 'text': 'Nik'})
    cols.append({'name': 'employee_name', 'value': 'employee_name',
                 'selected': 'True', 'dataType': 'varchar', 'text': 'Employee Name'})
    cols.append({'name': 'typeapp', 'value': 'typeapp', 'selected': '',
                 'dataType': 'varchar', 'text': 'type of brand'})
    cols.append({'name': 'jobtype', 'value': 'jobtype',
                 'selected': '', 'dataType': 'varchar', 'text': 'Job type'})
    cols.append({'name': 'gender', 'value': 'gender',
                 'selected': '', 'dataType': 'varchar', 'text': 'Gender'})
    cols.append({'name': 'status', 'value': 'status',
                 'selected': '', 'dataType': 'varchar', 'text': 'Status'})
    cols.append({'name': 'telphp', 'value': 'telphp',
                 'selected': '', 'dataType': 'varchar', 'text': 'Telp/Hp'})
    cols.append({'name': 'territory', 'value': 'territory',
                 'selected': '', 'dataType': 'varchar', 'text': 'Territory'})
    cols.append({'name': 'descriptions', 'value': 'descriptions',
                 'selected': '', 'dataType': 'varchar', 'text': 'Descriptions'})
    cols.append({'name': 'inactive', 'value': 'inactive',
                 'selected': '', 'dataType': 'boolean', 'text': 'InActive'})
    return render(request, 'app/UserControl/customFilter.html', {'cols': cols})


@decorators.ensure_authorization
@decorators.ajax_required
@decorators.detail_request_method('POST')
@decorators.read_permission(form_name='employee', action='Delete')
def NA_Employee_delete(request):
    if request.user.is_authenticated():
        get_idapp = request.POST.get('idapp')
        result = Employee.objects.delete_employee(
            idapp=get_idapp, NA_User=request.user.username)
        return commonFunct.response_default(result)


def SearchEmployeebyform(request):
    """
    for common search employee by form
    """
    searchText = request.GET.get('employee_filter')
    Ilimit = request.GET.get('rows', '')
    Isidx = request.GET.get('sidx', '')
    Isord = request.GET.get('sord', '')
    NAData = Employee.objects.getEmloyeebyForm(searchText)

    # if data is empty.. don't use Paginator and looping, to improve performance
    if NAData == Data.Empty:
        results = {"page": "1", "total": 0, "records": 0, "rows": []}
        return HttpResponse(
            json.dumps(results, indent=4, cls=DjangoJSONEncoder),
            content_type='application/json'
        )

    try:
        multi_sort = commonFunct.multi_sort_queryset(NAData, Isidx, Isord)
    except ValueError:
        multi_sort = NAData
    else:
        NAData = multi_sort
    totalRecord = NAData.count()
    paginator = Paginator(NAData, int(Ilimit))
    try:
        page = request.GET.get('page', '1')
    except ValueError:
        page = 1
    try:
        dataRows = paginator.page(page)
    except (EmptyPage, InvalidPage):
        dataRows = paginator.page(paginator.num_pages)

    rows = []
    i = 0
    for row in dataRows.object_list:
        i += 1
        datarow = {
            "id": row['idapp'], "cell": [
                row['idapp'], i, row['nik'], row['employee_name']
            ]
        }
        rows.append(datarow)
    results = {"page": page, "total": paginator.num_pages,
               "records": totalRecord, "rows": rows}
    return HttpResponse(json.dumps(results, indent=4, cls=DjangoJSONEncoder), content_type='application/json')
