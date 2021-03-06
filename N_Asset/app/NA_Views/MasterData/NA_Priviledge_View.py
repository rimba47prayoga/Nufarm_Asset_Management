import json
from datetime import datetime
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.shortcuts import render, redirect
from django.core.serializers.json import DjangoJSONEncoder
from django import forms
from django.db import transaction
from django.contrib.auth import login, logout, authenticate

from NA_Models.models import NAPriviledge, NASysPriviledge, NAPriviledge_form
from NA_DataLayer.common import ResolveCriteria, Data, commonFunct, decorators


def NA_Priviledge(request):
    return render(request, 'app/MasterData/NA_F_Priviledge.html')


def NA_PriviledgeGetData(request):
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
        priviledgeData = NAPriviledge.objects.PopulateQuery(
            IcolumnName, IvalueKey, criteria, dataType).order_by('-' + str(Isidx))
    else:
        priviledgeData = NAPriviledge.objects.PopulateQuery(
            IcolumnName, IvalueKey, criteria, dataType)

    totalRecord = priviledgeData.count()
    paginator = Paginator(priviledgeData, int(Ilimit))
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
                i, row['idapp'], row['first_name'], row['last_name'], row['username'],
                row['email'], row['divisi'], row['role'], row['password'], row['last_login'], row['last_form'],
                row['is_active'], row['date_joined'], row['createdby']
            ]
        }
        rows.append(datarow)
    results = {"page": page, "total": paginator.num_pages,
               "records": totalRecord, "rows": rows}
    return HttpResponse(json.dumps(results, indent=4, cls=DjangoJSONEncoder), content_type='application/json')


@decorators.ajax_required
@decorators.detail_request_method('GET')
def ShowCustomFilter(request):
    cols = []
    cols.append({'name': 'first_name', 'value': 'first_name',
                 'selected': 'True', 'dataType': 'varchar', 'text': 'First Name'})
    cols.append({'name': 'last_name', 'value': 'last_name',
                 'selected': '', 'dataType': 'varchar', 'text': 'Last Name'})
    cols.append({'name': 'username', 'value': 'username',
                 'selected': '', 'dataType': 'varchar', 'text': 'User Name'})
    cols.append({'name': 'email', 'value': 'email', 'selected': '',
                 'dataType': 'varchar', 'text': 'Email'})
    cols.append({'name': 'divisi', 'value': 'divisi',
                 'selected': '', 'dataType': 'varchar', 'text': 'Divisi'})
    cols.append({'name': 'last_form', 'value': 'last_form',
                 'selected': '', 'dataType': 'varchar', 'text': 'Last Form'})
    cols.append({'name': 'inactive', 'value': 'inactive',
                 'selected': '', 'dataType': 'boolean', 'text': 'InActive'})
    return render(request, 'app/UserControl/customFilter.html', {'cols': cols})


def NA_Priviledge_sys(request):
    user_id = request.GET['user_id']
    data = NAPriviledge.objects.Get_Priviledge_Sys(user_id)
    totalRecords = len(data)
    page = request.GET.get('page', '1')
    limit_row = request.GET.get('rows', '10')
    paginator = Paginator(data, int(limit_row))
    try:
        page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        page = paginator.page(paginator.num_pages)
    data = page.object_list
    same_data = {}
    len_data = len(data)
    for index, j in enumerate(data):
        if (index + 1) < len_data:
            if j['form_name'] == data[index + 1]['form_name']:
                if j['form_name'] in same_data:
                    same_data[j['form_name']] += 1
                else:
                    same_data[j['form_name']] = 2
    for index, i in enumerate(data):
        if i['form_name'] in same_data:
            i['attr'] = {}
            i['attr']['form_name'] = {}
            if index > 0:
                if 'attr' in data[index - 1]:
                    if i['form_name'] != data[index - 1]['form_name']:
                        if data[index + 1]['form_name'] == i['form_name']:
                            i['attr']['form_name']['rowspan'] = same_data[i['form_name']]
                    else:
                        i['attr']['form_name']['display'] = "none"
                else:
                    i['attr']['form_name']['rowspan'] = same_data[i['form_name']]
            else:
                i['attr']['form_name']['rowspan'] = same_data[i['form_name']]

    return HttpResponse(
        json.dumps(
            {"page": page.number, "total": paginator.num_pages,
                "records": totalRecords, "rows": data},
            cls=DjangoJSONEncoder
        ),
        content_type='application/json'
    )


def Entry_Priviledge(request):
    if request.method == 'POST':
        form = NA_Priviledge_Form(request.POST)
        if form.is_valid():
            result = form.save(request)
            return commonFunct.response_default(result)
        else:
            raise forms.ValidationError(form.errors)
    elif request.method == 'GET':
        statusForm = request.GET['statusForm']
        if statusForm == 'Edit' or statusForm == 'Open':
            idapp = request.GET['idapp']
            data = NAPriviledge.objects.retrieveData(idapp)
            form = NA_Priviledge_Form(initial=data)
            if int(data['role']) == NAPriviledge.GUEST:
                form.fields['divisi'].widget.attrs['disabled'] = ''
        else:
            form = NA_Priviledge_Form()
            form.fields['password'].widget.attrs['required'] = ''
            form.fields['confirm_password'].widget.attrs['required'] = ''
            form.fields['divisi'].widget.attrs['disabled'] = ''
        return render(request, 'app/MasterData/NA_Entry_Priviledge.html', {'form': form})


def Delete_user(request):
    idapp = request.POST['idapp']
    result = NAPriviledge.objects.Delete(idapp)
    return commonFunct.response_default(result)


@decorators.ajax_required
@decorators.detail_request_method('POST')
def ChangeRole(request, email):
    user = NAPriviledge.objects.get(email=email)
    role = request.POST['role']
    divisi = request.POST['divisi']
    user.role = role
    user.divisi = divisi
    user.save()
    return commonFunct.response_default((Data.Success,))


class NA_Priviledge_Form(forms.Form):
    idapp = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'First Name', 'style': 'height:unset'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Last Name', 'style': 'height:unset'}))
    username = forms.CharField(max_length=30, required=True, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'User Name', 'style': 'height:unset'}))
    email = forms.CharField(max_length=30, required=True, widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Email'}))
    divisi = forms.ChoiceField(
        required=False,
        choices=(
            ('', '-----------'),
            ('IT', 'IT'),
            ('GA', 'GA')
        ),
        widget=forms.Select(
            attrs={'class': 'form-control'}
        )
        
    )
    role = forms.ChoiceField(widget=forms.Select(
        attrs={'class': 'form-control'}), choices=(NAPriviledge.ROLE_CHOICES))
    statusForm = forms.CharField(widget=forms.TextInput(
        attrs={'style': 'display:none'}), required=True)
    password = forms.CharField(max_length=30, required=False, widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Password', 'style': 'height:unset'}))
    confirm_password = forms.CharField(max_length=30, required=False, widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Confirm Password', 'style': 'height:unset'}))
    initializeForm = forms.CharField(
        widget=forms.HiddenInput(), required=False)

    def clean_password(self):
        if self.cleaned_data['statusForm'] == 'Add':
            password = self.cleaned_data.get('password')
            if password is None or password == '':
                raise forms.ValidationError(
                    'Please fill out password'
                )

    def clean_confirm_password(self):
        if self.cleaned_data['statusForm'] == 'Add':
            confirm_password = self.cleaned_data.get('confirm_password')
            if confirm_password is None or confirm_password == '':
                raise forms.ValidationError(
                    'Please fill out confirm password'
                )

    def clean(self):
        statusForm = self.cleaned_data['statusForm']
        role = self.cleaned_data['role']
        if isinstance(role, str):
            role = int(role)
        if role != NAPriviledge.GUEST:
            divisi = self.cleaned_data['divisi']
            if divisi is None or divisi == '':
                raise forms.ValidationError('Please fill out divisi')
        if statusForm == 'Edit':
            idapp = self.cleaned_data.get('idapp')
            if idapp is None or idapp == '':
                raise forms.ValidationError('Please fill out idapp')
        confirm_password = self.cleaned_data.get('confirm_password')
        password = self.cleaned_data.get('password')
        if password != confirm_password:
            raise forms.ValidationError(
                'Password didn\'t match with confirm password'
            )
        return super(NA_Priviledge_Form, self).clean()

    def getFormData(self):
        return {
            'first_name': self.cleaned_data.get('first_name'),
            'last_name': self.cleaned_data.get('last_name'),
            'username': self.cleaned_data.get('username'),
            'email': self.cleaned_data.get('email'),
            'divisi': self.cleaned_data.get('divisi'),
            'role': self.cleaned_data.get('role')
        }

    def save(self, request):
        statusForm = self.cleaned_data.get('statusForm')
        if statusForm is None or statusForm == '':
            raise forms.ValidationError(
                'Status Form cannot be null'
            )
        else:
            if statusForm == 'Add':
                with transaction.atomic():
                    user = NAPriviledge()
                    user.first_name = self.cleaned_data['first_name']
                    user.last_name = self.cleaned_data['last_name']
                    user.username = self.cleaned_data['username']
                    user.email = self.cleaned_data['email']
                    user.role = self.cleaned_data['role']
                    if user.role != NAPriviledge.GUEST:
                        user.divisi = self.cleaned_data['divisi']
                    user.set_password(self.cleaned_data['password'])
                    user.date_joined = datetime.now()
                    user.createdby = request.user.username
                    user.save()
                    NASysPriviledge.set_permission(user)

            elif statusForm == 'Edit':
                idapp = self.cleaned_data.get('idapp')
                try:
                    user = NAPriviledge.objects.get(idapp=idapp)
                except NAPriviledge.DoesNotExist:
                    return (Data.Lost,)
                else:
                    data_init = {
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'username': user.username,
                        'email': user.email,
                        'divisi': user.divisi,
                        'role': user.role
                    }
                    data_form = self.getFormData()
                    sames = [k for k in data_form if data_form[k]
                             == data_init[k]]
                    for same in sames:
                        data_form.pop(same)

                    with transaction.atomic():
                        NAPriviledge.objects.filter(idapp=idapp).update(**data_form)
                        if 'role' in data_form:
                            if (int(data_form['role']) != NAPriviledge.GUEST
                                    and int(user.role) == NAPriviledge.GUEST):
                                user.refresh_from_db()
                                NASysPriviledge.set_permission(user)
        return (Data.Success,)


@decorators.admin_required_action('change')
@decorators.ajax_required
@decorators.detail_request_method('POST')
def NA_Sys_Priviledge_setInactive(request, idapp):
    inactive = request.POST['inactive']
    result = NASysPriviledge.objects.setInActive(idapp, inactive)
    return commonFunct.response_default(result)


@decorators.admin_required_action('delete')
@decorators.ajax_required
@decorators.detail_request_method('POST')
def NA_Sys_Priviledge_delete(request, idapp):
    result = NASysPriviledge.objects.Delete(idapp)
    return commonFunct.response_default(result)


@decorators.admin_required_action('add')
@decorators.ajax_required
def NA_Sys_Priviledge_add(request, email):
    if request.method == 'POST':
        form = NA_Permission_Form(request.POST)
        if form.is_valid():
            result = form.save(request)
            if isinstance(result, HttpResponse):
                return result
            return commonFunct.response_default(result)
        else:
            raise forms.ValidationError(form.errors)
    elif request.method == 'GET':
        form = NA_Permission_Form()
        return render(request, 'app/MasterData/NA_Entry_Permission.html', {'form': form})


def NA_Sys_Priviledge_check_permission(request, user_id):
    fk_form = request.GET['fk_form']
    data = NASysPriviledge.objects.CheckPermission(fk_form, user_id)
    if data == Data.Empty:
        return HttpResponse(
            json.dumps(commonFunct.EmptyGrid()),
            content_type='application/json'
        )
    dataRow = []
    no = 0
    for row in data:
        no += 1
        dataRow.append({
            'idapp': row['idapp'],
            'no': no,
            'form_name': row['form_name'],
            'permission': row['permission'],
            'set': '1',
            # 'inactive': row['inactive'],
        })
    return HttpResponse(
        json.dumps(dataRow),
        content_type='application/json'
    )


def NA_Sys_Priviledge_get_permission(request, email):
    form_name_ori = request.GET['form_name']
    user = NAPriviledge.objects.get(email=email)
    return commonFunct.response_default(
        (Data.Success, user.get_permission(form_name_ori))
    )


def NA_Sys_Priviledge_SetDefaultPermission(request, email):
    user = NAPriviledge.objects.get(email=email)
    if int(user.role) != NAPriviledge.GUEST:
        NASysPriviledge.set_permission(user)
        return commonFunct.response_default((Data.Success,))


class NA_Permission_Form(forms.Form):
    fk_form = forms.ModelChoiceField(
        queryset=NAPriviledge_form.objects.all(),
        widget=forms.Select(
            attrs={'class': 'form-control', 'style': 'display:inline-block'})
    )
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    allow_view = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'style': 'display:none'}), required=False)
    allow_add = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'style': 'display:none'}), required=False)
    allow_edit = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'style': 'display:none'}), required=False)
    allow_delete = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'style': 'display:none'}), required=False)
    initialize_permissionForm = forms.CharField(
        widget=forms.HiddenInput(), required=False)

    def save(self, request):
        user_id = self.cleaned_data['user_id']
        # instance of NA_Priviledge_form
        fk_form = self.cleaned_data['fk_form']
        allow_view = self.cleaned_data['allow_view']
        allow_add = self.cleaned_data['allow_add']
        allow_edit = self.cleaned_data['allow_edit']
        allow_delete = self.cleaned_data['allow_delete']
        permissions = {
            'Allow View': allow_view,
            'Allow Add': allow_add,
            'Allow Edit': allow_edit,
            'Allow Delete': allow_delete
        }
        user = NAPriviledge.objects.get(idapp=user_id)
        if user.role == NAPriviledge.GUEST:
            if allow_add or allow_edit or allow_delete:
                message = '__cannot_add_other_permission_guest'
                return HttpResponse(
                    json.dumps({'message': message}),
                    status=403,
                    content_type='application/json'
                )

            permissions.pop('Allow Add')
            permissions.pop('Allow Edit')
            permissions.pop('Allow Delete')

        data_permissions = []
        for k, v in permissions.items():
            if v:
                data_permissions.append(k)

        if user.is_have_permission(fk_form.form_name_ori):
            users_permission = user.get_permission(fk_form.form_name_ori)
            for i in users_permission:
                if i['permission'] in data_permissions:
                    data_permissions.pop(
                        data_permissions.index(i['permission']))

        NASysPriviledge.set_custom_permission(
            user_id=user_id,
            fk_form=fk_form.idapp,
            permissions=data_permissions,
            createdby=request.user.username
        )
        return (Data.Success,)


def NA_Priviledge_login(request):
    if request.user.is_authenticated():
        return redirect(request.GET.get('next', '/'))
    else:
        title = "Login"
        if request.method == 'POST':
            form = NA_Priviledge_Login_Form(request.POST or None)
            if form.is_valid():
                email = form.cleaned_data.get("email")
                password = form.cleaned_data.get("password")
                # authenticates Email & Password
                user = authenticate(email=email, password=password)
                login(request, user)
                next_action = request.GET.get('next')
                if next_action is not None:
                    return redirect(next_action)
                else:
                    return redirect('home')
            else:
                raise forms.ValidationError(form.errors)
        form = NA_Permission_Form()
        return render(
            request,
            "app/layout.html",
            {"form": form, "title": title}
        )


class NA_Priviledge_Login_Form(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    next = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise forms.ValidationError("User Does Not Exist.")
            if not user.check_password(password):
                raise forms.ValidationError("Password Does not Match.")
            if not user.is_active:
                raise forms.ValidationError("User is not Active.")

        return super(NA_Priviledge_Login_Form, self).clean(*args, **kwargs)


def NA_Priviledge_register(request):
    if request.method == 'POST':
        form = NA_Priviledge_Register_Form(request.POST, request.FILES or None)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='NA_DataLayer.NA_Auth.NA_AuthBackend')
            return redirect('home')
    else:
        form = NA_Priviledge_Register_Form()
        return render(
            request,
            'app/MasterData/NA_Priviledge_Register.html',
            {'form': form}
        )


def NA_Priviledge_logout(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        logout(request)
        return redirect('home')


class NA_Priviledge_Register_Form(forms.Form):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter First Name'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter Last Name'}))
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter Username'}))
    email = forms.CharField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Email Address'}))
    picture = forms.ImageField(required=False)
    password1 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm Password'}))
    initializeForm_user = forms.CharField(
        required=False, widget=forms.HiddenInput())

    def save(self):
        with transaction.atomic():
            user = NAPriviledge()
            user.username = self.cleaned_data['username']
            user.email = self.cleaned_data['email']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            pict = self.cleaned_data.get('picture')
            if pict:
                user.picture = pict
            user.set_password(self.cleaned_data['password1'])
            user.save()
            NASysPriviledge.set_permission(user)
        return user


def NA_Priviledge_change_picture(request, email):
    if request.user.email != email:
        return commonFunct.permision_denied('<h1>403 Forbidden</h1>')
    user = NAPriviledge.objects.get(idapp=request.user.idapp)
    picture = request.FILES['picture']
    user.picture = picture
    user.save()
    return commonFunct.response_default((Data.Success, user.get_picture_name()))
