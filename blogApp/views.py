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

            username = req.POST.get('username',None)
            password1 = req.POST.get('password', None)
            password2 = req.POST.get('repeatpassword', None)

            ceshi = User.objects.filter(name = username)
            if ceshi:
                return HttpResponse('账号重复')

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
            response=HttpResponseRedirect('/index')

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

    return render(req, 'blogApp/regist.html')

#登陆
def login(req):
    if req.method == 'POST':

        username = req.POST.get('username',None)
        password = req.POST.get('password',None)


        import hashlib
        h2 = hashlib.md5()
        h2.update(password.encode(encoding='utf-8'))
        storepassword = h2.hexdigest()
        #获取的表单数据与数据库进行比较
        auser = User.objects.filter(name__exact = username,password__exact = storepassword)

        if auser:
            #比较成
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
    return render(req,'blogApp/Login.html')

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

    cock = req.COOKIES.get('userid', None)
    if (cock == None):
        currentuser = None
    if (cock!=None):
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

    
    if ('keywords' in req.GET and not req.GET['keywords'] == ''):
        queryList = queryList.filter( 
            reduce( lambda x, y: x & y, map( 
                lambda x: (Q(title__icontains = x) | Q(title__icontains = x)) , req.GET['keywords'].split(' '))
            )
        )
        dic['keywords'] = req.GET['keywords']

    if ('categoryid' in req.GET and not req.GET['categoryid'] == ''):
        queryList = queryList.filter(category_id = req.GET['categoryid'])
        dic['category'] = Category.objects.get(category_id = req.GET['category_id'])
    
    if ('userid' in req.GET and not req.GET['userid'] == ''):
        queryList = queryList.filter(user_id = req.GET['userid'])
        dic['user'] = User.objects.get(user_id = req.GET['userid'])

    if ('tagid' in req.GET and not req.GET['tagid'] == ''):
        queryList = queryList.filter(blogtag__tag__tag_id__contains = req.GET['tagid'])
        dic['tag'] = Tag.objects.get(tag_id = req.GET['tagid'])

    cock = req.COOKIES.get('userid', None)
    if (cock != None):
        currentuser = getUserByCOOKIE(cock)
    else:
        currentuser = None
    dic['currentUser'] = currentuser
    dic['blogList'] = list(queryList)
    print(dic)

    return render(req, 'blogApp/search.html', dic)

def edit(req,blogid):
    blogid = int(blogid)
    #1.标签和分类的问题
    #blogid 查出userid然后和cookie进行对比，
    #找cookie对应的id
    useridsalt = req.COOKIES.get('userid',None)
    if (useridsalt == None):
        return HttpResponseRedirect('blogApp/error.html')
    c_userid = Cookie.objects.get(cookie__exact=useridsalt).user_id
    #不加_id的话是一个对象，加的话是一贯制
    #找用户名对应的id

    #若blogid不为0则需要将博客内容读出
    #不等于0，编辑再完善
    if (blogid!=0):

        #验证正确性
        u_userid = Blog.objects.get(blog_id=blogid).user_id
        if (u_userid != c_userid):
            return HttpResponseRedirect('blogApp/error.html')

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
        user = User.objects.get(user_id=c_userid)
        return render(req, 'blogApp/edit.html', {'catset': catset, 'reblog': reblog, 'blogid': blogid,'catename':catename,'str': str,'user':user ,'currentUser':user})

    #等于零，新的
    else:
        catset1 = Category.objects.filter(user_id=c_userid)
        catset = catset1.values_list('cate_name', flat=True)

        # 前端传后端   ，不空再传
        title = req.POST.get('title', None)
        text = req.POST.get('text', None)
        mytags = req.POST.get('mytags', None)
        aclass = req.POST.get('class', None)
        print(title,text,mytags,aclass)

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
        user = User.objects.get(user_id = c_userid)
        return render(req, 'blogApp/edit.html', {'catset': catset, 'blogid': blogid,'currentUser':user})


    #不管blog内容怎么样都要从数据库中读出标签


def manage(req,username):
    # 1.动态生成页面
    # 2.页面的按钮需要一些路由
    # 3.利用ajax将数据传到后端，存入数据库
    #添加新博客的时候时用0传入，编辑的时候用某个blogid进入
    #用username和cookie进行对比
    catetofil = req.POST.get('catetofil', None)
    useridsalt = req.COOKIES.get('userid', None)
    if (useridsalt == None):
        return HttpResponseRedirect('blogApp/error.html')
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
        cateset = Category.objects.filter(user_id = u_userid)
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
        print("测试 ssss、")
        print(catedel)
        if (test != None):
            Blog.objects.filter(blog_id__exact=test).delete()
        if (cate != None):
            Category.objects.create(cate_name=cate,user_id=u_userid)
        if (catedel != None):
            Category.objects.filter(cate_id__exact=catedel).delete()


        #通过cookie获取当前用户
        dic = {}
        cock = req.COOKIES.get('userid', None)
        if (cock != None):
            currentuser = getUserByCOOKIE(cock)
        else:
            currentuser = None
        #通过传入的参数获取被访问的用户
        user = User.objects.get(name = username)
        dic['currentUser'] = currentuser
        dic['blogList'] = reblogset
        dic['user'] = user
        dic['catedic'] = catedic
        dic['recateset'] = recateset


        return render(req,'blogApp/manage.html', dic)

        #利用reblogset自动生成表单

    else:
        return HttpResponseRedirect('blogApp/error.html')

#to do
def download(req,username):
    pass

#编辑个人信息
def editInfo(req, username):
    #访问用户，增加判断，不相等时跳转到error
    user = User.objects.get(name = username)

    #从cookie中获得的当前用户
    useridsalt = req.COOKIES.get('userid', None)
    if (useridsalt != None):
        result = Cookie.objects.filter(cookie__exact=useridsalt)
        userid1 = result.values_list('user', flat=True)
        userid = userid1[0]
        currentUser = User.objects.get(user_id__exact=userid)
    else:
        currentUser = None

    follow_num = Follow.objects.filter(user_id=user.user_id).count()
    followed_num = Follow.objects.filter(fld_user_id = user.user_id).count()

    if (user.user_id == currentUser.user_id):
        return render(req, 'blogApp/editInfo.html',
                      {'user':user,'currentUser':currentUser, "follow_num": follow_num, "followed_num": followed_num})
    else:
        return HttpResponseRedirect('blogApp/error.html')





#提交个人信息
def submit(req,username):
    if req.method == 'POST':
        nickname = req.POST.get('nickname')
        email = req.POST.get('email')
        password = req.POST.get('password1')
        print(password)
        avatar = req.POST.get('avatar')
        password1 = req.POST.get('password2')
        print(password1)
        desc = req.POST.get('desc')
        auser = User.objects.get(name=username)

        import hashlib
        hl = hashlib.md5()
        hl.update(password.encode(encoding='utf-8'))
        password = hl.hexdigest()

        if(password!=auser.password):
            data={'states':2}
        else:
            try:
                auser = User.objects.get(name=username)
                auser.nickname = nickname
                auser.email = email
                auser.avatar=avatar
                auser.description=desc
                hl = hashlib.md5()
                hl.update(password1.encode(encoding='utf-8'))
                password1 = hl.hexdigest()

                auser.password=password1
                data = {'state': 1}
                auser.save()
            except:
                data = {'state': 0}
        return JsonResponse(data)
    return render(req, 'blogApp/editInfo.html',)

#显示个人信息
def info(req,username):
    useridsalt = req.COOKIES.get('userid', None)
    if (useridsalt!=None):
        result = Cookie.objects.filter(cookie__exact=useridsalt)
        userid1 = result.values_list('user', flat=True)
        userid = userid1[0]
        auser=User.objects.get(user_id__exact=userid)
    else:
        auser = None

    user = User.objects.get(name=username)
    data={'currentUser': auser,'user':user}
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

    try:
        result = Blog.objects.filter(user_id=user_id)
        flag =True
    except Blog.DoesNotExist:
        flag = False
    return result, flag


def get_user_cate(id):
    cate_list = []
    global flag
    flag = False
    try:
        for i in Blog.objects.filter(user_id=id):
            cate_list.append(Category.objects.get(cate_id=i.cate_id))
        cate_list = remove_the_same(cate_list)
        flag = True
    except Blog.DoesNotExist:
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
                tag_list.append(Tag.objects.get(tag_id=j.tag_id))
                count += 1
            if count > 15:
                break
        if count != 0:
            flag = True
    except Blog.DoesNotExist:
        tag_list = None
        flag = False
    tag_list=remove_the_same(tag_list)
    return tag_list, flag


def get_user_file(id):
    return Blog.objects.filter(user_id=id)


def get_blog_user(blog_id):
    blog = Blog.objects.get(blog_id=blog_id)
    user = User.objects.get(user_id=blog.user_id)
    return user


def personalIndex(request, username):
    judegcookie = request.COOKIES.get('userid',None)
    user = User.objects.get(name=username)
    if (judegcookie == None):
        currentUser = None

        context = get_personal_page_content(request, user.user_id)
        context["currentUser"] = currentUser
        context["user"] = user
        context["follow_num"]
        return render(request, 'blogApp/personalIndex.html', context)

    cock = request.COOKIES.get('userid', None)

    currentUser = getUserByCOOKIE(cock)
    print("++++++++++++++++++++++++++++++++++++++")
    user_id, flag = get_user_id(username)
    global follow_form
    global flo_flag
    global follow_user_id
    global followed_user_id
    follow_user_id = getUserByCOOKIE(cock).user_id

    if flag:
        if request.method == "POST":

            follow_form = FollowForm({'follow_user_id': follow_user_id,
                                      'followed_user_id': followed_user_id})
            if follow_form.is_valid():
                # followed_user_id = user_id


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
            context['alreadyFollowed'] = flo_flag
            context['follow_form'] = follow_form

            currentuser = getUserByCOOKIE(request.COOKIES.get('userid', None))
            user = User.objects.get(name=username)
            context['currentUser'] = currentuser
            context['user'] = user


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
            context['alreadyFollowed'] = flo_flag
            context['follow_form'] = follow_form

            cock = request.COOKIES.get('userid', None)
            currentuser = getUserByCOOKIE(cock)
            user = User.objects.get(name=username)
            context['currentUser'] = currentuser
            context['user'] = user
            return render(request, 'blogApp/personalIndex.html', context)
        # 将当前页页码，以及当前页数据传递到index.html
    else:
        return HttpResponseRedirect('blogApp/error.html')


def get_user_id(user_name):
    try:
        user = User.objects.get(name=user_name)
    except User.DoesNotExist:
        return None, False
    return user.user_id, True


def get_personal_page_content(request, user_id):
    blog_list, blog_flag = get_user_blog_list(user_id)
    print(blog_list)
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
            'categoryList': cate_list,
            'cate_flag': cate_flag,
            'tagList': tag_list,
            'tag_flag': tag_flag}


def get_personalpage_link(user_name):
    return 'http://127.0.0.1:8000/personalIndex/' + str(user_name) + '/'


def get_blogcontent_link(blog_id):
    link = 'http://127.0.0.1:8000/blogcontent/' + str(blog_id) + '/'
    return link


def blog_content(request, blog_id):
    global user
    global currentUser
    global comment_form
    global follow_form
    global flo_flag
    global fav_flag

    user = get_blog_user(blog_id)

    judegcookie = request.COOKIES.get('userid', None)
    if (judegcookie == None):
        currentUser = None
        context = get_content(request, blog_id)
        context["currentUser"] = currentUser
        context["user"] = user
        context["follow_num"]
        return render(request, 'blogApp/BlogContent.html', context)

    cock = request.COOKIES.get('userid', None)
    currentUser = getUserByCOOKIE(cock)

    flo_flag = whether_follow(user.user_id, currentUser.user_id)
    fav_flag = whether_fav(blog_id, currentUser.user_id)
    if request.method == "POST":

        blogtodel = request.POST.get('blogtodel',None)
        comtodel = request.POST.get('comtodel',None)

        if (blogtodel!=None):
            Blog.objects.filter(blog_id = blogtodel).delete()
            response = JsonResponse({"result": True})
            return response

        if (comtodel!=None):
            Comment.objects.filter(comment_id =comtodel).delete()
            response = JsonResponse({"result": True})
            return response


        comment_form = CommentForm(request.POST)
        follow_form = FollowForm({'follow_user_id': currentUser.user_id,
                                  'followed_user_id': user.user_id})
        fav_form = FavouriteForm({'blog_id': blog_id,
                                  'user_id': currentUser.user_id})
        if request.POST.get("favourite", None):
            if not fav_flag:
                Favourite.objects.create(blog_id=blog_id, user_id=currentUser.user_id)
                fav_flag = True
            else:
                t = Favourite.objects.get(blog_id=blog_id, user_id=currentUser.user_id)
                t.delete()
                fav_flag = False

        if request.POST.get("follow", None):

            if not flo_flag:
                Follow.objects.create(fld_user_id=user.user_id, user_id=currentUser.user_id)
                flo_flag = True
            else:
                t = Follow.objects.get(fld_user_id=user.user_id, user_id=currentUser.user_id)
                t.delete()
                flo_flag = False

        if request.POST.get('comment-text'):
            comment_time = timezone.now()
            comment_content = request.POST.get('comment-text', None)
            comment_blog_id = blog_id
            Comment.objects.create(content=comment_content, time=comment_time, blog_id=comment_blog_id,
                               user_id=currentUser.user_id)

        context = get_content(request, blog_id)

        context['alreadyFollowed'] = flo_flag
        context['alreadyFavourite'] = fav_flag
        context['comment_form'] = comment_form
        context['follow_form'] = follow_form
        context['fav_form'] = fav_form
        context["currentUser"] = currentUser
        context["user"] = user
        context["blogTagList"] = list(map(lambda x: x.tag, list(Blog.objects.get(blog_id = blog_id).blogtag_set.all()) ))

        return render(request, 'blogApp/BlogContent.html', context)
    else:
        comment_form = CommentForm()
        follow_form = FollowForm()
        fav_form = FavouriteForm()

        context = get_content(request, blog_id)
        print(context)
        context['alreadyFollowed'] = flo_flag
        context['alreadyFavourite'] = fav_flag
        context['comment_form'] = comment_form
        context['follow_form'] = follow_form
        context['fav_form'] = fav_form
        context["currentUser"] = currentUser
        context["user"] = user
        context["blogTagList"] = map(lambda x: x.tag, list(Blog.objects.get(blog_id = blog_id).blogtag_set.all()) )

        return render(request, 'blogApp/BlogContent.html', context)


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
    blog = Blog.objects.get(blog_id=blog_id)
    user = get_blog_user(blog_id)
    blog.view_num += 1
    blog.save()
    context['blog'] = blog
    context['tagList'] = Tag.objects.filter(tag_id=BlogTag(blog_id=blog_id).tag_id)
    # get the all categories the user have used
    context['categoryList'], context['cate_flag'] = get_user_cate(user.user_id)

    # get the first 15 tags the user have used
    context['tagList'], context['tag_flag'] = get_user_tag(user.user_id)
    context['follow_num'] = (Follow.objects.filter(fld_user_id=user.user_id)).count()
    # get the all time when the user wrote blog

    comment_list, flag = get_blog_comment(blog_id)
    #print(blog.toHTML())

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
    global comment_list
    global flag
    flag = False
    try:
        comment_list = Comment.objects.filter(blog_id=blog_id)
        flag = True
    except Comment.DoesNotExist:
        flag = False
    return comment_list, flag

def info(request, username):
    currentUser = getUserByCOOKIE(request.COOKIES.get("userid", None))
    user = User.objects.get(name=username)
    follow_num = Follow.objects.filter(user_id=user.user_id).count()
    followed_num = Follow.objects.filter(fld_user_id=user.user_id).count()
    return render(request, 'blogApp/info.html', {'follow_num': follow_num,
                                                 'followed_num': followed_num,
                                                 'currentUser': currentUser,
                                                 'user': user})



def home_page(request):
    return render(request, 'homePage.html')

#给cookie返回user对象
def getUserByCOOKIE(cook):

    return Cookie.objects.get( cookie = cook ).user

def notify(req,username):
    useridsalt = req.COOKIES.get('userid', None)
    if (useridsalt == None):
        return HttpResponseRedirect('blogApp/error.html')
    currentUser = Cookie.objects.get(cookie__exact=useridsalt).user
    c_userid = currentUser.user_id

    user = User.objects.get(name__exact=username)
    u_userid = user.user_id
    if (c_userid == u_userid):#cookie验证成功
        notificationsList = Notification.objects.filter(user_id = c_userid)
        dic = {}
        dic['currentUser'] = currentUser
        dic['user'] = user
        dic['notificationList'] = notificationsList

        return render(req,'blogApp/notification.html',dic)
    else:
        return HttpResponseRedirect('blogApp/error.html')

def follow(req,username):
    useridsalt = req.COOKIES.get('userid', None)
    if (useridsalt == None):#没有cookie
        return HttpResponseRedirect('blogApp/error.html')
    currentUser = Cookie.objects.get(cookie__exact=useridsalt).user
    c_userid = currentUser.user_id

    user = User.objects.get(name__exact=username)
    u_userid = user.user_id
    if (c_userid == u_userid):#cookie验证成功,cookie存的和被访问的一样

        canuser = req.POST.get('userid',None)
        if (canuser!=None):
            Follow.objects.filter(user_id = c_userid,fld_user_id = canuser).delete()


        follow = Follow.objects.filter(user_id = c_userid)
        userList = []
        for i in follow:
            userList.append(User.objects.get(user_id = i.fld_user_id))
        dic = {}
        dic['currentUser'] = currentUser
        dic['user'] = user
        dic['userList'] = userList
        dic['followList'] = follow
        return render(req, 'blogApp/follow.html', dic)
    else:
        return HttpResponseRedirect('blogApp/error.html')

def favourite(req,username):
    useridsalt = req.COOKIES.get('userid', None)
    if (useridsalt == None):#没有cookie
        return HttpResponseRedirect('blogApp/error.html')
    currentUser = Cookie.objects.get(cookie__exact=useridsalt).user
    c_userid = currentUser.user_id

    user = User.objects.get(name__exact=username)
    u_userid = user.user_id
    if (c_userid == u_userid):#cookie验证成功,cookie存id的和被访问id的一样

        canb = req.POST.get('blogid', None)
        if (canb != None):
            Favourite.objects.filter(blog_id =canb, user_id = c_userid).delete()

        favList = Favourite.objects.filter(user_id = c_userid)
        blogList = []
        for i in favList:
            blogList.append(Blog.objects.get(blog_id = i.blog_id))
        dic = {}
        dic['currentUser'] = currentUser
        dic['user'] = user
        dic['blogList'] = blogList
        print(dic)
        return render(req, 'blogApp/favourite.html', dic)
    else:
        return HttpResponseRedirect('blogApp/error.html')
