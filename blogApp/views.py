from .models import *
from django.template import RequestContext
from django.shortcuts import render,render_to_response
from django.http import HttpResponse,HttpResponseRedirect
from django import forms
from django.utils import timezone
from django.db.models import Q
from functools import *
import random
from django.http import JsonResponse

from django.db.models import Max,Min

#表单
class UserForm(forms.Form):
    username = forms.CharField(label='用户名',max_length=100)
    password = forms.CharField(label='密码',widget=forms.PasswordInput())

class ReForm(forms.Form):
    username = forms.CharField(label='用户名',max_length=100)
    password1 = forms.CharField(label='密码',widget=forms.PasswordInput())
    password2 = forms.CharField(label='确认密码', widget=forms.PasswordInput())

class SearchForm(forms.Form):
    keywords = forms.CharField(label = "关键字", max_length = 100)

def getUserByCOOKIE(cook):
    return Cookie.objects.get( cookie = cook ).user

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
                response = HttpResponseRedirect('/info/%s' % username)
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

# 登陆成功
# def index(req):
#     userid = getUserByCOOKIE( req.COOKIES.get('userid', '') ).user_id
    
#     return render_to_response('blogApp/BlogContent.html' ,{'username':userid})

#退出
def logout(req):
    response = HttpResponse('logout !!')
    #清理cookie里保存username
    response.delete_cookie('username')
    return response


# 首页

def index(req):

    blogList = sorted(Blog.objects.all(), key = lambda x:-x.view_num)[:10]
    userList = sorted(
        User.objects.all(), key = lambda x:-(
            sum( 
                map(lambda x:x.view_num, x.blog_set.all())
                )
            )
        )[:20]

    dic = {}
    dic['userList'] = userList
    dic['blogList'] = blogList

    return render(req, "blogApp/index.html", dic)

# 搜索结果
def search(req):
    req.encoding = 'utf-8'

    queryList = Blog.objects.all()

    dic = {}

    if('keywords' in req.GET and req.GET['keywords'] == ''):
        return HttpResponse('请输入关键词')

    dic['keywords'] = []
    if ('keywords' in req.GET and not req.GET['keywords'] == ''):
        queryList = queryList.filter( 
            reduce( lambda x, y: x & y, map( 
                lambda x: (Q(title__icontains = x) | Q(title__icontains = x)) , req.GET['keywords'].split(' '))
            )
        )
        dic['keywords'].append(req.GET['keywords'])

    if ('category_id' in req.GET and not req.GET['category_id'] == ''):
        queryList = queryList.filter(category__id = req.GET['category_id'])
        dic['category_id'] = req.GET['category_id']
    
    if ('user_id' in req.GET and not req.GET['user_id'] == ''):
        queryList = queryList.filter(user__id = req.GET['user_id'])
        dic['user_id'] = req.GET['user_id']

    if ('tag_id' in req.GET and not req.GET['tag_id'] == ''):
        queryList = queryList.filter(tag_id = req.GET['tag_id'])

    dic['blogList'] = list(queryList)

    return render(req, 'blogApp/search.html', dic)

def edit(req,blogid):
    blogid = int(blogid)
    #1.标签和分类的问题
    #blogid 查出userid然后和cookie进行对比，
    #找cookie对应的id
    useridsalt = req.COOKIES.get('userid','')
    c_userid = Cookie.objects.get(cookie__exact=useridsalt).user_id
    #不加_id的话是一个对象，加的话是一贯制
    #找用户名对应的id

    #若blogid不为0则需要将博客内容读出
    #不等于0，编辑再完善
    if (blogid!=0):

        #验证正确性
        u_userid = Blog.objects.get(blog_id=blogid).user_id
        if (u_userid != c_userid):
            return HttpResponseRedirect('/login')

        #从数据库中读取原来的博客题目内容分类等
        catset1 = Category.objects.filter(user_id=c_userid)
        catset = catset1.values_list('cate_name', flat=True)
        blogset = Blog.objects.filter(blog_id=blogid)
        reblog1 = list(blogset)
        reblog = reblog1[0]
        catename = Category.objects.get(cate_id=reblog.cate_id).cate_name
        #从数据库中读取tags信息
        pblogtagset = BlogTag.objects.filter(blog_id=blogid)
        blogtagset = list(pblogtagset)
        str = ''
        for i in blogtagset:
            tagnameqs = Tag.objects.filter(tag_id=i.tag_id)
            if tagnameqs :
                tagname = Tag.objects.get(tag_id=i.tag_id).tag_name
                str = str +tagname + ','
                print(str)
        str = str.rstrip(',')
        print(str)



        #从前端获取数据
        title = req.POST.get('title', None)
        text = req.POST.get('text', None)
        mytags = req.POST.get('mytags', None)
        aclass = req.POST.get('class', None)

        if (title != None):
            # 将Blog进行更新,本来就有blogid
            # 数据转换，获取userid,classid
            #create blog
            cate_id = Category.objects.get(cate_name__exact=aclass).cate_id
            time_now = timezone.now()
            Blog.objects.filter(blog_id=blogid).update(content=text, title=title,
                                modified_time=time_now, cate_id=cate_id)
            #update tags and blogtag,mytags是新输入的tags
            #新输入的tags,列表格式
            l = mytags.split(',')
            inserttags = []
            for i in l:
                inserttags.append(i.lstrip(' ').rstrip(' '))

            #旧的删除
            for i in blogtagset:
                BlogTag.objects.filter(blog_id=blogid, tag_id=i.tag_id).delete()
            #对每一个新的i，若在tags表里有，如没有，
            for i in inserttags:
                result = Tag.objects.filter(tag_name=i)
                if result:
                    #吧它加上，便于实现
                    everyid = Tag.objects.get(tag_name=i).tag_id
                    BlogTag.objects.create(blog_id=blogid,tag_id=everyid)
                else:
                    Tag.objects.create(tag_name=i)
                    everyid = Tag.objects.get(tag_name=i).tag_id
                    BlogTag.objects.create(blog_id=blogid, tag_id=everyid)
        return render(req, 'blogApp/edit.html', {'catset': catset, 'reblog': reblog, 'blogid': blogid,'catename':catename,'str': str})

    #等于零，新的
    else:
        catset1 = Category.objects.filter(user_id=c_userid)
        catset = catset1.values_list('cate_name', flat=True)

        # 前端传后端   ，不空再传
        title = req.POST.get('title', None)
        text = req.POST.get('text', None)
        mytags = req.POST.get('mytags', None)
        aclass = req.POST.get('class', None)

        if (title != None):
            # 将Blog存进数据库,给出blogid
            # 数据转换，获取userid,classid
            cate_id = Category.objects.get(cate_name__exact=aclass).cate_id
            time_now = timezone.now()
            Blog.objects.create(content=text, title=title, view_num=0, like_num=0, create_time=time_now,
                                modified_time=time_now, cate_id=cate_id, user_id=c_userid)
            maxiddic = Blog.objects.aggregate(Max('blog_id'))
            blogid = maxiddic["blog_id__max"]

            # 将tags存进数据库,如果库中没有就插入，有就跳过,c_userid,tagnum,blogid
            # print(type(mytags))
            l = mytags.split(',')
            inserttags = []
            for i in l:
                inserttags.append(i.lstrip(' ').rstrip(' '))
            for i in l:
                result = Tag.objects.filter(tag_name=i)
                if result:
                    tagnum = Tag.objects.get(tag_name=i).tag_id
                    btresult = BlogTag.objects.get_or_create(blog_id=blogid, tag_id=tagnum)
                else:
                    Tag.objects.create(tag_name=i)
                    tagnum = Tag.objects.get(tag_name=i).tag_id
                    BlogTag.objects.create(blog_id=blogid, tag_id=tagnum)
        return render(req, 'blogApp/edit.html', {'catset': catset, 'blogid': blogid})


    #不管blog内容怎么样都要从数据库中读出标签


def manage(req,username):
    # 1.动态生成页面
    # 2.页面的按钮需要一些路由
    # 3.利用ajax将数据传到后端，存入数据库
    #添加新博客的时候时用0传入，编辑的时候用某个blogid进入
    #用username和cookie进行对比
    catetofil = req.POST.get('catetofil', None)
    useridsalt = req.COOKIES.get('userid', '')
    c_userid = Cookie.objects.get(cookie__exact=useridsalt).user_id
    u_userid = User.objects.get(name__exact=username).user_id
    if (c_userid == u_userid ):
        blogsetall = Blog.objects.filter(user_id=c_userid)
        reblogsetall = list(blogsetall)
        #后端向前端传数据
        #如果没有筛选条件传整个博客列表（默认）
        if (catetofil == None):
            blogset = Blog.objects.filter(user_id=c_userid)
            reblogset = list(blogset)
        # 如果有筛选条件，则传分类的博客对象
        if (catetofil != None):
            blogset = Blog.objects.filter(user_id=c_userid,cate_id=catetofil)
            reblogset = list(blogset)
        #传一个字典吧，分类和分类的个数传到前端,但是前端要用特别办法
        catedic = {}
        cateset = Category.objects.filter()
        recateset = list(cateset)
        for i in recateset:
            catedic[i.cate_name] = 0
        for blogone in reblogsetall:
            catename = Category.objects.get(cate_id__exact=blogone.cate_id).cate_name
            catedic[catename] = catedic[catename] + 1

        #reblogset = blogset.values_list('title','view_num','like_num')
        #print(reblogset[0][0])可以用数组访问


        test = req.POST.get('blogone', None)#ajax不能穿一个对象？直接传id了
        cate = req.POST.get('catename',None)
        catedel = req.POST.get('catetodel',None)

        if (test != None):
            Blog.objects.filter(blog_id__exact=test).delete()
        if (cate != None):
            Category.objects.create(cate_name=cate,user_id=u_userid)
        if (catedel != None):
            Category.objects.filter(cate_id__exact=catedel).delete()


        print(reblogset)

        return render(req,'blogApp/back-end.html', {'reblogset':reblogset, 'username':username,'catedic':catedic,'recateset':recateset})

        #利用reblogset自动生成表单

    else:
        return HttpResponseRedirect('/login')

#to do
def download(req,username):
    pass

#编辑个人信息
def editInfo(req, username):
    useridsalt = req.COOKIES.get('userid', '')
    result = Cookie.objects.filter(cookie__exact=useridsalt)
    userid1 = result.values_list('user', flat=True)
    userid = userid1[0]
    origin = User.objects.get(user_id__exact=userid)
    return render(req,'blogApp/personalInfoEdit.html',{'nickname':origin.nickname,'email':origin.email,'username':origin.name})


#提交个人信息
def submit(req,username):
    if req.method == 'POST':
        nickname = req.POST.get('nickname')
        email = req.POST.get('email')
        avatar = req.FILES.get('avatar')
        print(avatar)

        try:
            auser=User.objects.get(name=username)
            auser.nickname=nickname
            auser.email=email
            #auser.avatar=avatar
            data = {'state': 1}
            auser.save()
        except:
            data = {'state': 0}
        print(data)
        return JsonResponse(data)

    return render(req, 'blogApp/personalInfoEdit.html',)

#显示个人信息
def info(req,username):
    useridsalt = req.COOKIES.get('userid', '')
    result = Cookie.objects.filter(cookie__exact=useridsalt)
    userid1 = result.values_list('user', flat=True)
    userid = userid1[0]
    auser=User.objects.get(user_id__exact=userid)
    data={'nickname': auser.nickname,'email':auser.email,'username':username}
    print(data)
    return render(req,'blogApp/personalInfo.html',data)