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

    cock = request.COOKIES.get('userid', None)
    currentuser = getUserByCOOKIE(cock)
    dic = {}
    dic['userList'] = userList
    dic['blogList'] = blogList
    dic['currentUser'] = currentuser

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

    cock = req.COOKIES.get('userid', None)
    if (cock != None):
        currentuser = getUserByCOOKIE(cock)
    dic['currentUser'] = currentuser
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


from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import HttpResponse

from django.shortcuts import render
from django.core.paginator import Paginator

from django import forms

from django.utils import timezone


class CommentForm(forms.Form):
    comment_content = forms.CharField()
    comment_user_id = forms.CharField()


class FollowForm(forms.Form):
    follow_user_id = forms.CharField()
    followed_user_id = forms.CharField()


class FavouriteForm(forms.Form):
    blog_id = forms.CharField()
    user_id = forms.CharField()


def remove_the_same(list):
    temp = []
    for i in list:
        if i not in temp:
            temp.append(i)
    return temp


def get_user_blog_list(user_id):
    global result
    global flag
    global count
    flag = False
    count = 0
    blog_list = []
    try:
        result = Blog.objects.filter(user_id=user_id)
        for i in result:
            time = i.create_time
            title = i.title
            content = i.content
            link = get_blogcontent_link(i.blog_id)
            cate_name = Category.objects.get(cate_id=i.cate_id).cate_name
            temp = {'title': title,
                    'content': content,
                    'time': time,
                    'blog_link': link,
                    'cate_name': cate_name}
            blog_list.append(temp)
            count +=1
        if count != 0:
            flag = True
    except Blog.DoesNotExist:
        blog_list = None
        flag = False
    return blog_list, flag


def get_user_cate(id):
    cate_list = []
    global flag
    global count
    flag = False
    count = 0
    try:
        for i in Blog.objects.filter(user_id=id):
            content = {'cate_name': (Category.objects.get(cate_id=i.cate_id)).cate_name,
                       'link': '-'}
            cate_list.append(content)
            count += 1
        cate_list = remove_the_same(cate_list)
        if count != 0:
            flag = True
    except Blog.DoesNotExist:
        cate_list = None
        flag = False
    return cate_list, flag


def get_user_tag(id):
    global tag_list
    global count
    global flag

    tag_list = []
    count = 0
    flag = False

    try:
        for i in Blog.objects.filter(user_id=id):
            for j in BlogTag.objects.filter(blog_id=i.blog_id):
                content = {'name': (Tag.objects.get(tag_id=j.tag_id)).tag_name, 'link': '-'}
                tag_list.append(content)
                count += 1
            if count > 15:
                break
        if count != 0:
            flag = True
        tag_list = remove_the_same(tag_list)
    except Blog.DoesNotExist:
        tag_list = None
        flag = False
    return tag_list, flag


def get_user_file(id):
    global file_list

    file_list = []
    try:
        for i in Blog.objects.filter(user_id=id):
            time = str(i.create_time)
            time = time[0:time.rfind(' ')]
            content = {'file': time, 'link':'-'}
            file_list.append(content)
        file_list = remove_the_same(file_list)
    except Blog.DoesNotExist:
        file_list = None

    return file_list


def get_blog_user(blog_id):
    blog = Blog.objects.get(blog_id=blog_id)
    user = User.objects.get(user_id=blog.user_id)
    return user.user_id, user.name


def personalIndex(request, username):
    user_id, flag = get_user_id(username)
    global follow_form
    global flo_flag
    global follow_user_id
    global followed_user_id

    if flag:
        if request.method == "POST":

            follow_form = FollowForm({'follow_user_id': follow_user_id,
                                      'followed_user_id': followed_user_id})
            if follow_form.is_valid():
                followed_user_id = user_id
                cock = request.COOKIES.get('userid',None)
                follow_user_id = getUserByCOOKIE(cock).user_id
                print(follow_user_id)
                print("被关注" + str(followed_user_id))
                print("关注" + str(follow_user_id))
                flo_flag = whether_follow(followed_user_id, follow_user_id)


                # follow_user_id = getUserByCOOKIE(request.COOKIES.get('userid', ''))
                if not flo_flag:
                    Follow.objects.create(fld_user_id=followed_user_id, user_id=follow_user_id)
                    flo_flag = True
                else:
                    t = Follow.objects.get(fld_user_id=followed_user_id, user_id=follow_user_id)
                    t.delete()
                    flo_flag = False
            print(flo_flag)
            context = get_personal_page_content(request, user_id)
            context['flo_flag'] = flo_flag
            context['follow_form'] = follow_form
            return render(request, 'blogApp/personalIndex.html', context)
        else:
            follow_form = FollowForm()
            followed_user_id = user_id
            cock = request.COOKIES.get('userid', None)
            follow_user_id = getUserByCOOKIE(cock).user_id
            print( follow_user_id)
            print("被关注" + str(followed_user_id))
            print("关注" + str(follow_user_id))
            flo_flag = whether_follow(followed_user_id, follow_user_id)
            print(flo_flag)

            context = get_personal_page_content(request, user_id)
            # print(flo_flag)
            context['flo_flag'] = flo_flag
            context['follow_form'] = follow_form
            return render(request, 'blogApp/personalIndex.html', context)
        # 将当前页页码，以及当前页数据传递到index.html
    else:
        return HttpResponse('未找到用户')


def get_user_id(user_name):
    try:
        user = User.objects.get(name=user_name)
    except User.DoesNotExist:
        return None, False
    return user.user_id, True


def get_personal_page_content(request, user_id):
    blog_list, blog_flag = get_user_blog_list(user_id)
    cate_list, cate_flag = get_user_cate(user_id)
    tag_list, tag_flag = get_user_tag(user_id)
    file_list = get_user_file(user_id) if blog_flag else []
    user = User.objects.get(user_id=user_id)
    # 值1：所有的数据
    # 值2：每一页的数据
    # 值3：当最后一页数据少于n条，将数据并入上一页
    paginator = Paginator(blog_list, 12, 3)

    try:
        # GET请求方式，get()获取指定Key值所对应的value值
        # 获取index的值，如果没有，则设置使用默认值1
        num = request.GET.get('index', '1')
        # 获取第几页
        number = paginator.page(num)
    except PageNotAnInteger:
        # 如果输入的页码数不是整数，那么显示第一页数据
        number = paginator.page(1)
    except EmptyPage:
        number = paginator.page(paginator.num_pages)

    follow_num = (Follow.objects.filter(fld_user_id=user_id)).count()
    return {'page': number, 'paginator': paginator,
            'blog_flag': blog_flag,
            'nickname': user.nickname,
            'regist_time': user.regist_time,
            'follow_num': follow_num,
            'cate_list': cate_list,
            'cate_flag': cate_flag,
            'tag_list': tag_list,
            'tag_flag': tag_flag,
            'file_list': file_list,
            'file_flag': blog_flag}


def get_personalpage_link(user_name):
    return 'http://127.0.0.1:8000/personalpage/' + str(user_name) + '/'


def get_blogcontent_link(blog_id):
    link = 'http://127.0.0.1:8000/blogcontent/' + str(blog_id) + '/'
    return link


def blog_content(request, blog_id):

    global comment_form
    global follow_form
    global flo_flag
    global fav_flag
    global follow_user_id
    global followed_user_id

    followed_user_id,name = get_blog_user(blog_id)
    #follow_user_id = '111119'
    flo_flag = whether_follow(followed_user_id, follow_user_id)
    fav_flag = whether_fav(blog_id, follow_user_id)

    if request.method == "POST":

        comment_form = CommentForm(request.POST)
        follow_form = FollowForm({'follow_user_id': follow_user_id,
                                  'followed_user_id': followed_user_id})
        fav_form = FavouriteForm({'blog_id': blog_id,
                                  'user_id': follow_user_id})
        if fav_form.is_valid():
            if not fav_flag:
                Favourite.objects.create(blog_id=blog_id, user_id=follow_user_id)
                fav_flag = True
            else:
                t = Favourite.objects.get(blog_id=blog_id, user_id=follow_user_id)
                t.delete()
                fav_flag = False

        if follow_form.is_valid():

            #follow_user_id = getUserByCOOKIE(request.COOKIES.get('userid', ''))
            if not flo_flag:
                Follow.objects.create(fld_user_id=followed_user_id, user_id=follow_user_id)
                flo_flag = True
            else:
                t = Follow.objects.get(fld_user_id=followed_user_id, user_id=follow_user_id)
                t.delete()
                flo_flag = False

        if comment_form.is_valid():
            comment_time = timezone.now()
            comment_content = comment_form.cleaned_data['comment_content']
            comment_blog_id = blog_id
            Comment.objects.create(content=comment_content, time=comment_time, blog_id=comment_blog_id, user_id=follow_user_id)

        context = get_content(request, blog_id)

        context['flo_flag'] = flo_flag
        context['fav_flag'] = fav_flag
        context['comment_form'] = comment_form
        context['follow_form'] = follow_form
        context['fav_form'] = fav_form

        return render(request, 'BlogContent.html', context)
    else:
        comment_form = CommentForm()
        follow_form = FollowForm()
        fav_form = FavouriteForm()

        context = get_content(request, blog_id)

        context['flo_flag'] = flo_flag
        context['fav_flag'] = fav_flag
        context['comment_form'] = comment_form
        context['follow_form'] = follow_form
        context['fav_form'] = fav_form
        return render(request, 'BlogContent.html', context)


def whether_follow(fld_user_id, user_id):
    print("函数调用")
    print("被关注"+str(fld_user_id))
    print("关注"+str(user_id))
    try:
        follow = Follow.objects.get(fld_user_id=fld_user_id, user_id=user_id)
    except Follow.DoesNotExist:
        return False
    return True


def whether_fav(blog_id, user_id):
    print("函数调用")
    print("被收藏"+str(blog_id))
    print("收藏"+str(user_id))
    try:
        fav = Favourite.objects.get(blog_id=blog_id, user_id=user_id)
    except Favourite.DoesNotExist:
        return False
    return True


def get_content(request, blog_id):
    context = {}
    # context['comment_form'] = comment_form
    id, name = get_blog_user(blog_id=blog_id)
    user = User.objects.get(user_id=id)
    blog = Blog.objects.get(blog_id=blog_id)
    blog.view_num += 1
    blog.save()
    context['title'] = blog.title
    context['content'] = blog.content
    context['time'] = blog.create_time
    context['view_num'] = blog.view_num

    context['nickname'] = user.nickname
    context['regist_time'] = user.regist_time
    context['follow_num'] = (Follow.objects.filter(fld_user_id=id)).count()
    context['user_link'] = get_personalpage_link(name)

    # get the all categories the user have used
    context['cate_list'], context['cate_flag'] = get_user_cate(id)

    # get the first 15 tags the user have used
    context['tag_list'], context['tag_flag'] = get_user_tag(id)

    # get the all time when the user wrote blog
    context['file_list'] = get_user_file(id)
    comment_list, flag = get_blog_comment(blog_id)
    global paginator
    global number
    if comment_list is not None:

        paginator = Paginator(comment_list, 6, 2)
        try:
            num = request.GET.get('index', '1')
            number = paginator.page(num)
        except PageNotAnInteger:
            number = paginator.page(1)
        except EmptyPage:
            number = paginator.page(paginator.num_pages)

        context['page'] = number
        context['paginator'] = paginator
        context['flag'] = flag
        return context


def get_blog_comment(blog_id):
    global context
    context = []
    global comment_list
    global flag
    flag = "True"
    try:
        comment_list = Comment.objects.filter(blog_id=blog_id)
        for i in comment_list:
            user_name = User.objects.get(user_id=i.user_id).nickname
            temp={'comment_user': user_name, 'content': i.content, 'time': i.time}
            context.append(temp)
        flag = "False"
    except Comment.DoesNotExist:
        context = None

    #context = remove_the_same(context)
    return context, flag


def home_page(request):
    return render(request, 'homePage.html')

#给cookie返回user对象
def getUserByCOOKIE(cook):

    return Cookie.objects.get( cookie = cook ).user