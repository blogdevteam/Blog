from .models import *
from django.template import RequestContext
from django.shortcuts import render,render_to_response
from django.http import HttpResponse,HttpResponseRedirect
from django import forms
from django.utils import timezone
import random

#表单
class UserForm(forms.Form):
    username = forms.CharField(label='用户名',max_length=100)
    password = forms.CharField(label='密码',widget=forms.PasswordInput())

class ReForm(forms.Form):
    username = forms.CharField(label='用户名',max_length=100)
    password1 = forms.CharField(label='密码',widget=forms.PasswordInput())
    password2 = forms.CharField(label='确认密码', widget=forms.PasswordInput())

#注册
def regist(req):
    if req.method == 'POST':
        uf1 = ReForm(req.POST)
        if uf1.is_valid():
            #获得表单数据
            username = uf1.cleaned_data['username']
            password1 = uf1.cleaned_data['password1']
            password2 = uf1.cleaned_data['password2']
            if(password1!=password2):
                return HttpResponse('regist failed!!')
            #添加到数据库
            time_now = timezone.now()

            # md5加密
            import hashlib
            hl = hashlib.md5()
            hl.update(password1.encode(encoding='utf-8'))
            storepassword = hl.hexdigest()

            User.objects.create(name= username,password=storepassword,regist_time=time_now,nickname=username)
            response=HttpResponseRedirect('blogApp/BlogContent.html')

            auser = User.objects.filter(name__exact=username, password__exact=storepassword)
            loginuserid1 = auser.values_list('user_id', flat=True)
            loginuserid = loginuserid1[0]

            seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+=-"
            sa = []
            for i in range(20):
                sa.append(random.choice(seed))
            salt = ''.join(sa)
            print(salt)
            response.set_cookie('userid', salt, 3600)

            # 保存到数据库（salt，userid(loginuserid))
            loginuser = User.objects.get(user_id=loginuserid)
            cookie = Cookie()
            print(loginuserid)
            cookie.user = loginuser
            cookie.cookie = salt
            cookie.save()

            return response

    else:
        uf1 = ReForm()
    return render(req, 'blogApp/register.html', {'uf1': uf1})

#登陆
def login(req):
    if req.method == 'POST':
        uf = UserForm(req.POST)
        if uf.is_valid():
            #获取表单用户密码
            username = uf.cleaned_data['username']
            password = uf.cleaned_data['password']
            import hashlib
            h2 = hashlib.md5()
            h2.update(password.encode(encoding='utf-8'))
            storepassword = h2.hexdigest()
            #获取的表单数据与数据库进行比较
            auser = User.objects.filter(name__exact = username,password__exact = storepassword)

            if auser:
                #比较成index
                response = HttpResponseRedirect('/index')
                #将username写入浏览器cookie,失效时间为3600
                loginuserid1 = auser.values_list('user_id',flat=True)
                loginuserid = loginuserid1[0]

                # 随机串
                seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+=-"
                sa = []
                for i in range(20):
                    sa.append(random.choice(seed))
                salt = ''.join(sa)
                print(salt)
                response.set_cookie('userid',salt,3600)

                #保存到数据库（salt，userid(loginuserid))
                loginuser = User.objects.get(user_id=loginuserid)
                cookie = Cookie()
                print(loginuserid)
                cookie.user = loginuser
                cookie.cookie = salt
                cookie.save()

                return response
            else:
                #比较失败，还在login
                return HttpResponseRedirect('/login')
    else:
        uf = UserForm()
    return render(req,'blogApp/Login.html',{'uf':uf})

#登陆成功
def index(req):
    useridsalt = req.COOKIES.get('userid','')
    result = Cookie.objects.filter(cookie__exact=useridsalt)
    userid1 = result.values_list('user',flat=True)
    userid =  userid1[0]
    return render_to_response('blogApp/BlogContent.html' ,{'username':userid})

#退出
def logout(req):
    response = HttpResponse('logout !!')
    #清理cookie里保存username
    response.delete_cookie('username')
    return response
